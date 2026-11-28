#!/usr/bin/env bash
# Keep the WSLg sockets untouched while running the official private bridge.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
cd "$root"
if [[ $# -lt 1 ]]; then
    printf 'usage: %s OUT_DIR [compare_duel_pilots.py options]\n' "$0" >&2
    exit 2
fi
out="$(realpath -m -- "$1")"
shift
stage="$(mktemp -d /var/tmp/smsforge-pilot-XXXXXXXX)"
mkdir "$stage/pulse-runtime" "$stage/pulse-state"
mkdir -m 0700 "$stage/sessions"
export PULSE_RUNTIME_PATH="$stage/pulse-runtime" PULSE_STATE_PATH="$stage/pulse-state"
export PULSE_SERVER="unix:$stage/native"

env -u PULSE_SERVER pulseaudio --daemonize=no --exit-idle-time=180 --use-pid-file=no -n \
    --load="module-native-protocol-unix socket=$stage/native" \
    --load="module-null-sink sink_name=smsforge_base" --log-target=stderr >"$stage/pulse.log" 2>&1 &
pulse_pid=$!
finish() {
    kill "$pulse_pid" 2>/dev/null || true
    wait "$pulse_pid" 2>/dev/null || true
    if [[ -d "$out" ]]; then
        cp -- "$stage/pulse.log" "$out/pulse.log"
    fi
    rm -rf -- "$stage"
}
trap finish EXIT
for attempt in {1..30}; do
    pactl info >/dev/null 2>&1 && break
    kill -0 "$pulse_pid" 2>/dev/null || break
    sleep 0.2
done
pactl info >/dev/null || { cat "$stage/pulse.log" >&2; exit 1; }

bwrap --die-with-parent --unshare-net --bind / / --dev /dev --perms 1777 --tmpfs /tmp \
    --perms 1777 --dir /tmp/.X11-unix \
    --bind "$stage/sessions" "/tmp/smsforge-$(id -u)" --chdir "$root" -- \
    bash -c '
        out="$1"
        shift
        result=0
        if [[ ${SMSFORGE_TRACE_PILOT_BOOT:-0} == 1 ]]; then
            (
                sleep 14
                for proc in /proc/[0-9]*; do
                    [[ -r "$proc/cmdline" ]] || continue
                    cmd="$(tr "\0" " " <"$proc/cmdline" 2>/dev/null)" || continue
                    if [[ "$cmd" == java\ * && "$cmd" =~ -Dsmsforge.root=/tmp/smsforge-[0-9]+/([0-9a-f]{32})\  ]]; then
                        session="${BASH_REMATCH[1]}"
                        [[ -f "/tmp/smsforge-$(id -u)/$session/session.json" ]] || continue
                        kill -QUIT "${proc##*/}" 2>/dev/null || true
                    fi
                done
            ) &
        fi
        bash tools/sms_wrapper/run_host.sh python3 -u \
            SMS_projects/master_of_fighters/tools/compare_duel_pilots.py --out "$out" "$@" || result=$?
        for d in "/tmp/smsforge-$(id -u)"/*/; do
            for log in supervisor.log xvfb.log emulator.log; do
                if [[ -f "$d$log" && -d "$out" ]]; then
                    cp -- "$d$log" "$out/$(basename "$d")-$log"
                fi
            done
        done
        exit "$result"
    ' compare "$out" "$@"
