package smsforge;

import components.input.AbstractButtonInputProvider;
import components.input.SMSButtons;
import components.input.SMSJoypad;
import platform.Emulicious;
import platform.DisplayWindow;
import system.MasterSystem;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.nio.ByteBuffer;
import javax.swing.SwingUtilities;
import java.util.Properties;
import platform.SoundOutput;
import javax.sound.sampled.SourceDataLine;

/** Process-local controllers. The original emulator JAR is never rewritten.
 * This adapter is version pinned by the Python coordinator. No JInput poll,
 * keyboard event, wall-clock timer or RAM write supplies gameplay input.
 */
public final class ForgeSMS {
    static volatile int p1, p2, console;
    static volatile long frames;
    static long sequence;
    static MasterSystem system;
    static String session, token;
    static Path root;
    static Method stop, start;
    static DisplayWindow display;
    static volatile boolean closed;
    static volatile boolean audioEnabled;
    static boolean realtimeRecording, steppedRecording;
    static long recordingStartNanos, recordingStartFrame;
    static Path steppedRecordingDir;
    static long steppedRecordedFrames;
    static volatile byte[] replayInputs;
    static ByteBuffer replayCommits;
    static Path replayCommitsPath;
    static int replayProbeAddress, replayProbeSize;

    static final class ReplayFrameOutput extends BufferedOutputStream {
        ReplayFrameOutput(OutputStream destination) { super(destination, 1024 * 1024); }

        @Override public void write(int value) throws IOException {
            // DisplayWindow writes RGB24 bytes on the sole emulator runner.
            // The controller stops that runner before it closes the stream.
            byte[] buffer = buf;
            if (buffer == null || count == buffer.length) super.write(value);
            else buffer[count++] = (byte)value;
        }
    }

    static void prepareSilentAudio() throws Exception {
        // -muted prevents every ROM sample from reaching the host during boot.
        // Prime the already-open line with zeros so host routing can see it.
        Field f = SoundOutput.class.getDeclaredField("line"); f.setAccessible(true);
        SourceDataLine line = (SourceDataLine)f.get(null);
        if (line == null) return; // No audio backend: keep muted, never fallback.
        line.flush(); line.start();
        // ALSA stop/start recreates the PipeWire stream on this host. Keep its
        // identity across emulator pauses; gate PCM at write, not host volume.
        SourceDataLine stable = (SourceDataLine)java.lang.reflect.Proxy.newProxyInstance(
            ForgeSMS.class.getClassLoader(), new Class<?>[]{SourceDataLine.class}, (proxy, m, args) -> {
                if (m.getName().equals("stop") || m.getName().equals("start") || m.getName().equals("flush")) return null;
                if (m.getName().equals("write") && !audioEnabled) {
                    int count = (Integer)args[2];
                    return line.write(new byte[count], 0, count);
                }
                try { return m.invoke(line, args); }
                catch (InvocationTargetException e) { throw e.getCause(); }
            });
        f.set(null, stable);
        int bytes = Math.min(line.available(), 8820);
        if (bytes > 0) line.write(new byte[bytes], 0, bytes);
        // An idle ALSA PCM can also be recreated after an underrun. Supply
        // zeros while the ROM is paused/muted so the routed stream stays alive.
        Thread keepalive = new Thread(() -> {
            byte[] zeros = new byte[8820];
            try {
                while (!closed) {
                    if (!audioEnabled || !Emulicious.isRunning()) {
                        int count = Math.min(line.available(), zeros.length);
                        if (count > 0) line.write(zeros, 0, count);
                    }
                    Thread.sleep(10);
                }
            } catch (Exception e) { e.printStackTrace(); }
        }, "smsforge-silent-audio-keepalive");
        keepalive.setDaemon(true); keepalive.start();
    }
    static void enableAudio() throws Exception {
        pause();
        SoundOutput sound = (SoundOutput)field("sound");
        // Boot samples remain in the emulator buffer even while muted.
        Field length = SoundOutput.class.getDeclaredField("length"); length.setAccessible(true);
        length.setInt(sound, 0);
        sound.stop();
        sound.setSoundEnabled(true);
        Field muted = Emulicious.class.getDeclaredField("soundMuted"); muted.setAccessible(true);
        muted.setBoolean(null, false);
        ((Properties)field("properties")).setProperty("SoundMuted", "false");
        audioEnabled = true;
    }
    static final class Provider extends AbstractButtonInputProvider {
        public boolean isButtonDown(int id) {
            if (id >= SMSButtons.SMSKEY_A_UP && id <= SMSButtons.SMSKEY_A_2)
                return (p1 & (1 << (id - SMSButtons.SMSKEY_A_UP))) != 0;
            if (id >= SMSButtons.SMSKEY_B_UP && id <= SMSButtons.SMSKEY_B_2)
                return (p2 & (1 << (id - SMSButtons.SMSKEY_B_UP))) != 0;
            return (id == SMSButtons.SMSKEY_PAUSE && (console & 1) != 0)
                || (id == SMSButtons.SMSKEY_RESET && (console & 2) != 0);
        }
    }
    static final class Pad extends SMSJoypad {
        final int port;
        Pad(int port, Provider provider) { super(port, provider); this.port = port; }
        public void frameFinished() {
            super.frameFinished();
            if (port == 0) {
                long relativeFrame = ++frames - recordingStartFrame;
                byte[] inputs = replayInputs;
                if (inputs != null) {
                    int next = (int)relativeFrame * 2;
                    if (next <= inputs.length) {
                        replayCommits.putLong(System.nanoTime());
                        for (int i=0; i<replayProbeSize; i++)
                            replayCommits.put((byte)system.peekByte(replayProbeAddress+i));
                    }
                    p1 = next < inputs.length ? inputs[next] : 0;
                    p2 = next < inputs.length ? inputs[next+1] : 0;
                }
            }
        }
    }

    static void loadReplay(String name, int address, int length) throws IOException {
        if (address < 0xC000 || address >= 0xE000 || length < 1 || length > 256 || address+length > 0xE000)
            throw new IOException("replay probe range");
        Path path = root.resolve("evidence").resolve(name + ".inputs");
        long size = Files.size(path);
        if (size < 120 || size > 3600 || size % 2 != 0) throw new IOException("replay input length");
        byte[] inputs = Files.readAllBytes(path);
        if (inputs.length != size) throw new IOException("replay changed while reading");
        for (byte value : inputs) if (value < 0 || value > 63) throw new IOException("replay input mask");
        replayCommits = ByteBuffer.allocate(inputs.length / 2 * (Long.BYTES + length));
        replayProbeAddress = address;
        replayProbeSize = length;
        replayCommitsPath = root.resolve("evidence").resolve(name + ".commits");
        p1 = inputs[0]; p2 = inputs[1]; console = 0;
        replayInputs = inputs;
    }

    static void stopReplay() throws IOException {
        if (replayInputs == null) return;
        replayInputs = null;
        p1 = p2 = console = 0;
        try (OutputStream stream = Files.newOutputStream(replayCommitsPath, StandardOpenOption.CREATE_NEW)) {
            stream.write(replayCommits.array(), 0, replayCommits.position());
        } finally {
            replayCommits = null;
            replayCommitsPath = null;
        }
    }
    static Object field(String name) throws Exception {
        Field f = Emulicious.class.getDeclaredField(name); f.setAccessible(true); return f.get(null);
    }
    static Method method(String name) throws Exception {
        Method m = Emulicious.class.getDeclaredMethod(name); m.setAccessible(true); return m;
    }
    static void pause() throws Exception {
        stop.invoke(null);
        if (Emulicious.isRunning() || field("runnerThread") != null)
            throw new IOException("emulator runner did not stop");
    }
    static void step(int count) throws Exception {
        if (count < 0 || count > 36000) throw new IOException("invalid frame count");
        pause();
        long target = frames + count;
        // Small slices end within one Z80 instruction of the actual VDP edge.
        // A stuck debugger cannot masquerade as advancement: the budget fails.
        long budget = (long)system.getCyclesPerFrame() * (count + 2);
        while (frames < target) {
            if ((budget -= 64) < 0) throw new IOException("VDP frame counter stalled");
            execute(64);
        }
        display.repaint();
    }
    static void execute(int cycles) throws IOException {
        long before = frames;
        system.execute(cycles);
        if (!steppedRecording || frames == before) return;
        if (frames != before + 1) throw new IOException("step passed more than one VDP frame");
        File image = steppedRecordingDir.resolve(String.format("%06d.png", steppedRecordedFrames)).toFile();
        display.writeScreenToFile(image, true);
        if (!image.isFile() || image.length() == 0) throw new IOException("missing framebuffer at VDP edge");
        ++steppedRecordedFrames;
    }
    static String status() {
        return "\"pid\":" + ProcessHandle.current().pid() + ",\"frame\":" + frames
            + ",\"p1\":" + p1 + ",\"p2\":" + p2 + ",\"console\":" + console
            + ",\"emulator_input\":" + system.getInputState()
            + ",\"nominal_hz\":" + ((double)system.getCyclesPerSecond()/system.getCyclesPerFrame())
            + ",\"audio_enabled\":" + audioEnabled
            + ",\"recording_realtime\":" + realtimeRecording
            + ",\"running\":" + Emulicious.isRunning();
    }
    static int mask(String s, int max) throws IOException {
        int value = Integer.parseInt(s);
        if (value < 0 || value > max) throw new IOException("invalid control mask");
        return value;
    }
    static String command(String line) throws Exception {
        String[] a = line.trim().split(" ");
        if (a.length < 4 || !session.equals(a[0]) || !token.equals(a[1]))
            throw new IOException("session authentication rejected");
        long seq = Long.parseLong(a[2]);
        if (closed || seq <= sequence) throw new IOException("stale or closed command");
        sequence = seq;
        String extra = "";
        if (realtimeRecording && !a[3].equals("status") &&
                !a[3].equals("record-stop") && !a[3].equals("close"))
            throw new IOException("realtime capture active; stop before pausing or stepping");
        if (steppedRecording && (a[3].equals("run") || a[3].equals("record-start")))
            throw new IOException("stepped capture active; stop before free run");
        switch (a[3]) {
        case "status": if (a.length != 4) throw new IOException("arity"); break;
        case "pause": pause(); break;
        case "run": start.invoke(null); break;
        case "audio-enable": if (a.length != 4) throw new IOException("arity"); enableAudio(); break;
        case "audio-disable": if (a.length != 4) throw new IOException("arity"); pause(); audioEnabled=false; break;
        case "input":
            if (a.length != 7) throw new IOException("arity");
            pause();
            int n1 = mask(a[4],63), n2 = mask(a[5],63), nc = mask(a[6],3);
            p1=n1; p2=n2; console=nc;
            extra=",\"received\":true,\"applied\":true"; break;
        case "step": if(a.length != 5) throw new IOException("arity"); step(Integer.parseInt(a[4])); break;
        case "sample-commit":
            if(a.length != 6 && a.length != 7) throw new IOException("arity");
            int sampleAddress = Integer.parseInt(a[4]);
            int sampleStamp = mask(a[5], 255);
            int maxVdpFrames = a.length == 7 ? mask(a[6], 8) : 3;
            if(sampleAddress < 0xC000 || sampleAddress >= 0xE000 || sampleStamp % 2 != 0)
                throw new IOException("sample address or commit stamp");
            if(maxVdpFrames == 0) throw new IOException("zero sampling budget");
            pause();
            long sampleFrame = frames;
            int sampleCycles = 0;
            long sampleBudget = (long)system.getCyclesPerFrame() * maxVdpFrames;
            while((system.peekByte(sampleAddress) & 255) != sampleStamp) {
                if(sampleCycles >= sampleBudget || frames - sampleFrame > maxVdpFrames)
                    throw new IOException("MFD1 commit missing, expected " + sampleStamp
                        + " observed " + (system.peekByte(sampleAddress) & 255)
                        + " after " + (frames - sampleFrame) + " VDP frames");
                execute(4);
                sampleCycles += 4;
            }
            extra=",\"cycles_advanced\":" + sampleCycles + ",\"start_frame\":" + sampleFrame;
            break;
        case "sequence":
            if(a.length != 5) throw new IOException("arity");
            String[] steps=a[4].split(",");
            if(steps.length>256) throw new IOException("sequence too long");
            int[][] plan=new int[steps.length][4]; int total=0;
            for(int i=0;i<steps.length;i++) {
                String[] parts=steps[i].split(":");
                if(parts.length!=4) throw new IOException("sequence format");
                plan[i][0]=mask(parts[0],63);plan[i][1]=mask(parts[1],63);
                plan[i][2]=mask(parts[2],3);plan[i][3]=mask(parts[3],36000);
                total+=plan[i][3];
            }
            if(total>36000) throw new IOException("sequence frame budget");
            pause();StringBuilder trace=new StringBuilder(",\"trace\":[");
            try {
                for(int i=0;i<plan.length;i++) {
                    if(i>0)trace.append(',');long begin=frames;
                    p1=plan[i][0];p2=plan[i][1];console=plan[i][2];step(plan[i][3]);
                    trace.append("{\"begin\":").append(begin).append(",\"end\":").append(frames)
                         .append(",\"p1\":").append(p1).append(",\"p2\":").append(p2).append('}');
                }
            } finally {p1=p2=console=0;}
            extra=trace.append(']').toString();break;
        case "read":
            if(a.length != 6) throw new IOException("arity");
            pause(); int addr=Integer.parseInt(a[4]), len=Integer.parseInt(a[5]);
            if(addr<0xC000 || len<1 || len>256 || addr+len>0xE000) throw new IOException("RAM range");
            StringBuilder b=new StringBuilder(",\"ram\":[");
            for(int i=0;i<len;i++) { if(i>0)b.append(','); b.append(system.peekByte(addr+i)); }
            extra=b.append(']').toString(); break;
        case "read-vram":
            if(a.length != 6) throw new IOException("arity");
            pause();
            int vramAddress = Integer.parseInt(a[4]), vramLength = Integer.parseInt(a[5]);
            if(vramAddress < 0 || vramAddress >= 0x4000 || vramLength < 1 || vramLength > 0x2000
                    || vramAddress + vramLength > 0x4000) throw new IOException("VRAM range");
            int[] vram = system.getVRAM();
            StringBuilder vdp = new StringBuilder(",\"sat_address\":").append(system.getSpriteAttributeTableAddress())
                    .append(",\"vram\":[");
            for(int i=0;i<vramLength;i++) {
                if(i>0) vdp.append(',');
                vdp.append(vram[vramAddress+i]&255);
            }
            extra=vdp.append(']').toString(); break;
        case "sram":
            pause();int[] ram=system.getSRAM();
            if(ram==null || ram.length<2)throw new IOException("SRAM absent");
            extra=",\"sram\":["+ram[0]+","+ram[1]+"]";break;
        case "capture":
            if(a.length != 5 || !a[4].matches("[A-Za-z0-9_-]+\\.png")) throw new IOException("capture name");
            pause(); File file=root.resolve("evidence").resolve(a[4]).toFile();
            SwingUtilities.invokeAndWait(() -> display.writeScreenToFile(file,true));
            if(!file.isFile()) throw new IOException("capture absent");
            try(OutputStream out=Files.newOutputStream(root.resolve("effective-config.ini"))) {
                ((Properties)field("properties")).store(out,"SMSForge effective settings at capture");
            }
            break;
        case "video":
            if(a.length!=6 || !a[4].matches("[A-Za-z0-9_-]+"))throw new IOException("video format");
            int count=mask(a[5],1800);if(count<2)throw new IOException("video too short");
            Path dir=root.resolve("evidence").resolve(a[4]);Files.createDirectory(dir);
            pause();long first=frames;
            try {
                for(int i=0;i<count;i++) {
                    step(1);File frame=dir.resolve(String.format("%06d.png",i)).toFile();
                    display.writeScreenToFile(frame,true);
                }
            } finally {p1=p2=console=0;}
            extra=",\"first_frame\":"+first+",\"recorded_frames\":"+count;break;
        case "record-steps-start":
            if(a.length!=5 || !a[4].matches("[A-Za-z0-9_-]{1,64}") || steppedRecording)
                throw new IOException("stepped recording name or state");
            pause();
            steppedRecordingDir=Files.createDirectory(root.resolve("evidence").resolve(a[4]));
            steppedRecordedFrames=0;
            recordingStartFrame=frames;
            recordingStartNanos=System.nanoTime();
            steppedRecording=true;
            extra=",\"first_frame\":"+recordingStartFrame;break;
        case "record-steps-stop":
            if(a.length!=4 || !steppedRecording) throw new IOException("no stepped recording active");
            pause();
            steppedRecording=false;
            extra=",\"first_frame\":"+recordingStartFrame+
                  ",\"recorded_frames\":"+steppedRecordedFrames+
                  ",\"capture_elapsed_ns\":"+(System.nanoTime()-recordingStartNanos);break;
        case "record-start":
            if((a.length!=5 && a.length!=8) || !a[4].matches("[A-Za-z0-9_-]{1,64}") || steppedRecording
                || (a.length==8 && !a[5].equals("vdp-replay")))
                throw new IOException("recording name or state");
            pause();
            // Native DisplayWindow callback writes cropped RGB24 before any
            // compositor/scale. Buffered output avoids one syscall per byte.
            OutputStream destination = Files.newOutputStream(root.resolve("evidence").resolve(a[4]+".rgb"),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            OutputStream stream = a.length==8 ? new ReplayFrameOutput(destination) :
                new BufferedOutputStream(destination, 1024*1024);
            display.setScreenRecorderStream(stream,true);
            recordingStartFrame=frames;
            recordingStartNanos=System.nanoTime();
            realtimeRecording=true;
            try {
                if(a.length==8) loadReplay(a[4], Integer.parseInt(a[6]), Integer.parseInt(a[7]));
                start.invoke(null);
            }
            catch(Exception failure) {
                display.setScreenRecorderStream(null,true);
                realtimeRecording=false;
                stopReplay();
                throw failure;
            }
            extra=",\"first_frame\":"+recordingStartFrame;break;
        case "record-stop":
            if(a.length!=4 || !realtimeRecording)
                throw new IOException("no matching recording active");
            pause();
            long elapsedNanos=System.nanoTime()-recordingStartNanos;
            display.setScreenRecorderStream(null,true);
            realtimeRecording=false;
            stopReplay();
            extra=",\"first_frame\":"+recordingStartFrame+
                  ",\"recorded_frames\":"+display.getRecordedScreens()+
                  ",\"capture_elapsed_ns\":"+elapsedNanos;break;
        case "close":
            pause();
            if(realtimeRecording) {
                display.setScreenRecorderStream(null,true);
                realtimeRecording=false;
                stopReplay();
            }
            steppedRecording=false;
            p1=p2=console=0; closed=true; break;
        default: throw new IOException("unknown command");
        }
        return "{\"ok\":true,\"session_id\":\""+session+"\",\"seq\":"+seq+","+status()+extra+"}";
    }
    public static void main(String[] args) throws Exception {
        root=Paths.get(System.getProperty("smsforge.root"));
        session=System.getProperty("smsforge.session");
        token=Files.readString(root.resolve("token")).trim();
        // Disable native discovery and hotplug; the two SMSJoypads below are
        // the only gameplay providers, regardless of focus or keyboard state.
        System.setProperty("jinput.useDefaultPlugin","false");
        System.setProperty("net.java.games.input.useDefaultPlugin","false");
        System.setProperty("jinput.plugins","");
        String[] mutedArgs = new String[args.length + 1];
        mutedArgs[0] = "-muted"; System.arraycopy(args, 0, mutedArgs, 1, args.length);
        Emulicious.main(mutedArgs);
        long deadline=System.nanoTime()+30_000_000_000L;
        while(!Emulicious.isReady() || field("system")==null) {
            if(System.nanoTime()>deadline) throw new IOException("emulator boot timeout");
            Thread.sleep(20);
        }
        SwingUtilities.invokeAndWait(() -> {});
        stop=method("stop"); start=method("start"); pause();
        if(!(field("system") instanceof MasterSystem)) throw new IOException("SMS ROM required");
        system=(MasterSystem)field("system");
        display=(DisplayWindow)field("displayWindow");
        Provider provider=new Provider();
        system.plugInInputDevice(0,new Pad(0,provider));
        system.plugInInputDevice(1,new Pad(1,provider));
        system.setButtons(new SMSButtons(provider));
        step(120); // Finish boot before exposing the endpoint; never a desktop fallback.
        prepareSilentAudio();
        Path socketPath=root.resolve("control.sock");
        try(ServerSocketChannel server=ServerSocketChannel.open(StandardProtocolFamily.UNIX)) {
            server.bind(UnixDomainSocketAddress.of(socketPath));
            Files.writeString(root.resolve("ready.tmp"),"{\"ok\":true,"+status()+"}");
            Files.move(root.resolve("ready.tmp"),root.resolve("ready.json"),StandardCopyOption.ATOMIC_MOVE);
            while(!closed) {
                try(SocketChannel client=server.accept()) {
                    client.configureBlocking(false);
                    ByteBuffer buffer=ByteBuffer.allocate(8192);long expiry=System.nanoTime()+2_000_000_000L;
                    boolean complete=false;
                    while(buffer.hasRemaining() && System.nanoTime()<expiry) {
                        int got=client.read(buffer);
                        if(got<0)break;
                        if(got>0 && buffer.get(buffer.position()-1)=='\n'){complete=true;break;}
                        Thread.sleep(1);
                    }
                    if(!complete)continue;
                    String line=new String(buffer.array(),0,buffer.position(),java.nio.charset.StandardCharsets.UTF_8);
                    String response;
                    try { response=command(line); }
                    catch(Exception e) {
                        if(line.startsWith(session+" "+token+" ")){
                            pause();p1=p2=console=0;
                            String[] fields = line.split(" ", 5);
                            String operation = fields.length > 3 ? fields[3].trim() : "";
                            if(operation.equals("sample-commit") || operation.equals("capture"))
                                System.err.println(operation + ": " + e);
                        }
                        response="{\"ok\":false,\"error\":\"command rejected\"}";
                    }
                    client.configureBlocking(true);
                    Writer out=Channels.newWriter(client,"UTF-8"); out.write(response+"\n"); out.flush();
                }
            }
        } catch(Exception e) {
            p1=p2=console=0;e.printStackTrace();System.exit(1);
        } finally { p1=p2=console=0; Files.deleteIfExists(socketPath); }
        System.exit(0);
    }
}
