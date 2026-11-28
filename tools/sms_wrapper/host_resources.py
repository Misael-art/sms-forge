"""Read-only host observations for the SMSForge bootstrap CLI."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import time


def cpu_ticks(proc):
    with (proc / 'stat').open() as stream:
        fields = list(map(int, stream.readline().split()[1:9]))
    return sum(fields), fields[3] + fields[4]


def swap_pages(proc):
    with (proc / 'vmstat').open() as stream:
        return {key: int(value) for key, value in map(str.split, stream)
                if key in ('pswpin', 'pswpout')}


def linux_sample(processes, proc=Path('/proc'), devices=Path('/sys/class')):
    total, idle = cpu_ticks(proc)
    swap = swap_pages(proc)
    start = time.monotonic()
    time.sleep(1)
    total_end, idle_end = cpu_ticks(proc)
    swap_end = swap_pages(proc)
    seconds = time.monotonic() - start
    mem = {}
    for line in (proc / 'meminfo').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in ('MemTotal', 'MemAvailable'):
            mem[key] = int(value.split()[0]) * 1024
    psi = {}
    for name in ('cpu', 'memory', 'io'):
        try:
            rows = (proc / 'pressure' / name).read_text().splitlines()
            psi[name] = {row.split()[0]: float(dict(field.split('=') for field in
                         row.split()[1:])['avg10']) for row in rows}
        except OSError:
            psi[name] = None
    zones = []
    for zone in sorted((devices / 'thermal').glob('thermal_zone*')):
        try:
            trips = [int(p.with_name(p.name.replace('_type', '_temp')).read_text()) / 1000
                     for p in zone.glob('trip_point_*_type') if p.read_text().strip() == 'passive']
            zones.append(dict(name=zone.joinpath('type').read_text().strip(),
                              current_c=int(zone.joinpath('temp').read_text()) / 1000,
                              passive_trip_c=min(trips, default=None)))
        except (OSError, ValueError):
            continue
    for sensor in sorted((devices / 'hwmon').glob('hwmon*/temp*_input')):
        try:
            prefix = sensor.name.removesuffix('_input')
            label = sensor.with_name(prefix + '_label')
            critical = sensor.with_name(prefix + '_crit')
            chip = sensor.with_name('name').read_text().strip()
            zones.append(dict(name=chip + '/' + (label.read_text().strip() if label.is_file() else prefix),
                              current_c=int(sensor.read_text()) / 1000, passive_trip_c=None,
                              critical_c=int(critical.read_text()) / 1000 if critical.is_file() else None))
        except (OSError, ValueError):
            continue
    sample = dict(cpu_percent=(100 * (1 - (idle_end - idle) / (total_end - total))
                               if total_end > total else None),
                  loadavg=os.getloadavg(), psi_avg10_percent=psi,
                  total_bytes=mem.get('MemTotal'), available_bytes=mem.get('MemAvailable'),
                  swap_pages_per_sec={k: (swap_end[k] - v) / seconds for k, v in swap.items()},
                  thermal_zones=zones)
    if processes:
        rows = []
        for pid in proc.glob('[0-9]*'):
            try:
                rss = int((pid / 'statm').read_text().split()[1]) * os.sysconf('SC_PAGE_SIZE')
                command = (pid / 'cmdline').read_bytes().rstrip(b'\0').replace(b'\0', b' ')
                rows.append(dict(pid=int(pid.name), rss_bytes=rss, command=os.fsdecode(command)))
            except (OSError, IndexError, ValueError):
                continue
        sample['processes'] = sorted(rows, key=lambda row: -row['rss_bytes'])
    return sample


def windows_sample(processes):
    shell = shutil.which('pwsh.exe') or (
        Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
    command = [str(shell), '-NoProfile', '-NonInteractive', '-File',
               str(Path(__file__).with_name('windows_resources.ps1'))]
    if processes:
        command.append('-Processes')
    result = subprocess.run(command, capture_output=True, encoding='utf-8',
                            errors='replace', timeout=60)
    if result.returncode:
        raise OSError(result.stderr.strip() or 'CIM collection failed')
    return json.loads(result.stdout)


def observe(root, temp, processes=False):
    system = platform.system()
    if system == 'Windows':
        sample = windows_sample(processes)
    elif system == 'Linux':
        sample = linux_sample(processes)
    else:
        raise OSError(f'host telemetry unavailable for {system}')
    volumes = {}
    for role, path in [('destination', root), ('temp', temp)]:
        path = Path(path).resolve(strict=True)
        volumes[role] = dict(path=str(path), device=path.stat().st_dev,
                             free_bytes=shutil.disk_usage(path).free)
        if system == 'Linux' and shutil.which('findmnt'):
            fs = subprocess.run(['findmnt', '-n', '-o', 'FSTYPE', '-T', str(path)],
                                capture_output=True, text=True, timeout=5)
            volumes[role]['filesystem'] = fs.stdout.strip() or None
        elif system == 'Windows':
            volumes[role]['filesystem'] = windows_filesystem(path)
    return dict(schema='smsforge.host_resources/v1', platform=system,
                captured_at=datetime.now(timezone.utc).isoformat(), volumes=volumes,
                claim_ceiling='host_observation_only', **sample)


def windows_filesystem(path):
    import ctypes
    root = ctypes.create_unicode_buffer(32768)
    kind = ctypes.create_unicode_buffer(256)
    kernel = ctypes.windll.kernel32
    if kernel.GetVolumePathNameW(str(path), root, len(root)) and kernel.GetVolumeInformationW(
            root, None, 0, None, None, None, kind, len(kind)):
        return kind.value
    return None


def check_budget(sample, peak_mib, output_mib, staging_mib):
    """Arithmetic for declared estimates. Pressure and thermal review are separate."""
    mib = 1024**2
    needs = {'destination': output_mib*mib, 'temp': staging_mib*mib}
    by_device = {}
    ram_needed = peak_mib*mib
    free_disk_after = {}
    known = True
    for role, vol in sample['volumes'].items():
        device = vol['device']
        kind = vol.get('filesystem')
        known = known and bool(kind)
        if kind in ('tmpfs', 'ramfs'):
            ram_needed += needs[role]
        by_device[device] = by_device.get(device, 0) + needs[role]
    disk_ok = True
    for role, vol in sample['volumes'].items():
        free_disk_after[role] = vol['free_bytes'] - by_device[vol['device']]
        reserve = 0 if vol.get('filesystem') in ('tmpfs', 'ramfs') else 10*1024**3
        disk_ok = disk_ok and free_disk_after[role] >= reserve
    free = sample.get('available_bytes')
    total = sample.get('total_bytes')
    after = free - ram_needed if free is not None else None
    reserve = max(4*1024**3, (total+3)//4) if total else None
    return dict(peak_mib=peak_mib, output_mib=output_mib, staging_mib=staging_mib,
                ram_after_bytes=after, ram_reserve_bytes=reserve, free_disk_after_bytes=free_disk_after,
                within_reserves=(disk_ok and after >= reserve
                                 if known and after is not None and reserve is not None else None))


def monitor(root, args):
    temp = args.temp or tempfile.gettempdir()
    for index in range(args.samples):
        start = time.monotonic()
        sample = observe(root, temp, args.processes)
        sample['collection_seconds'] = round(time.monotonic() - start, 3)
        if args.peak_mib is not None:
            sample['budget'] = check_budget(sample, args.peak_mib, args.output_mib, args.staging_mib)
        print(json.dumps(sample), flush=True)
        if index + 1 < args.samples:
            time.sleep(max(0, args.interval - (time.monotonic() - start)))
    return 0
