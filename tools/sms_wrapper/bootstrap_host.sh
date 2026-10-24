#!/usr/bin/env bash
# Entry point deliberately needs only bash before installing OS prerequisites.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
apply=0
system=0
profile=full
for ((i=1;i<=$#;i++)); do
    arg="${!i}"
    case "$arg" in
        --apply) apply=1 ;;
        --system-packages) system=1 ;;
        --profile) j=$((i+1)); profile="${!j:-}" ;;
    esac
done
case "$profile" in build|qa|full) ;; *) echo 'profile must be build, qa or full' >&2; exit 2 ;; esac
if ((system && !apply)); then
    echo '--system-packages requires --apply' >&2; exit 2
fi
if ((apply && system)); then
    elevate=()
    if ((EUID != 0)); then
        command -v sudo >/dev/null || { echo 'sudo/root required for OS packages; no portable sandbox fallback' >&2; exit 2; }
        elevate=(sudo)
    fi
    # Use the distro's repositories; never execute a downloaded shell script.
    source /etc/os-release
    if [[ "${ID:-} ${ID_LIKE:-}" =~ (ubuntu|debian) ]]; then
        base=(ca-certificates git curl python3 python3-venv python3-pip build-essential zstd libgc1)
        qa=(default-jdk fontconfig fonts-dejavu-core xvfb xauth x11-utils bubblewrap ffmpeg pulseaudio-utils pulseaudio libsdl2-2.0-0 libgl1 libxrender1 libxtst6 libxi6 libasound2t64)
        # Debian 12 calls the ALSA library libasound2, Ubuntu 24.04 libasound2t64.
        if [[ "${ID:-}" == debian && "${VERSION_ID:-}" == 12 ]]; then qa[${#qa[@]}-1]=libasound2; fi
        "${elevate[@]}" apt-get update
        packages=("${base[@]}")
        if [[ "$profile" != build ]]; then packages+=("${qa[@]}"); fi
        "${elevate[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${packages[@]}"
    elif [[ "${ID:-} ${ID_LIKE:-}" =~ (arch|manjaro) ]]; then
        packages=(ca-certificates git curl python python-pip gcc make zstd gc)
        if [[ "$profile" != build ]]; then packages+=(jdk17-openjdk fontconfig ttf-dejavu xorg-server-xvfb xorg-xauth xorg-xdpyinfo bubblewrap ffmpeg libpulse pulseaudio sdl2 libglvnd alsa-lib libxtst libxi libxrender); fi
        # Arch partial upgrades are unsupported. Require an already refreshed host.
        "${elevate[@]}" pacman -S --needed --noconfirm "${packages[@]}"
    else
        echo "Unsupported distro for package automation: ${ID:-unknown}; see doc/continuity/20261024-new-host.md" >&2
        exit 2
    fi
fi
command -v python3 >/dev/null || { echo 'Install Python 3.11+ or rerun with --apply --system-packages' >&2; exit 2; }
exec python3 "$here/host_bootstrap.py" "$@"
