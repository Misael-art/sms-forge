#!/usr/bin/env bash
# Diagnostic playback of source sheet; it is not a framebuffer or calibrated sprite.
set -eu
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
source_png="$project_dir/data/source_art/sprite_studies/alis/strong_thrust_round1/sequence_01.png"
out_dir="$project_dir/out/diagnostics/alis_strong_thrust_round1"
mkdir -p "$out_dir"
if [ "${1:-}" = "--grounded-converted" ]; then
  preview="$out_dir/converted_grounded_preview"
  rtk proxy ffmpeg -v error -nostdin -n -filter_complex_threads 1 -threads 1 \
    -loop 1 -framerate 60 -i "$preview/right_idle_limit.png" \
    -loop 1 -framerate 60 -i "$preview/right_prepare_limit.png" \
    -loop 1 -framerate 60 -i "$preview/right_thrust_limit.png" \
    -loop 1 -framerate 60 -i "$preview/right_recover_limit.png" \
    -filter_complex '[0:v]split=2[a][e];[a]trim=end_frame=8,setpts=PTS-STARTPTS[a0];[1:v]trim=end_frame=7,setpts=PTS-STARTPTS[b0];[2:v]trim=end_frame=3,setpts=PTS-STARTPTS[c0];[3:v]trim=end_frame=6,setpts=PTS-STARTPTS[d0];[e]trim=end_frame=12,setpts=PTS-STARTPTS[e0];[a0][b0][c0][d0][e0]concat=n=5:v=1:a=0,loop=loop=3:size=36:start=0,format=yuv420p[out]' \
    -map '[out]' -frames:v 144 -c:v libx264 -threads 1 -preset ultrafast -crf 16 \
    -movflags +faststart "$preview/right_limit_normal.mp4"
  rtk proxy ffmpeg -v error -nostdin -n -threads 1 -i "$preview/right_limit_normal.mp4" \
    -vf 'setpts=4*PTS' -r 60 -c:v libx264 -threads 1 -preset ultrafast -crf 16 \
    "$preview/right_limit_slow.mp4"
  exit 0
fi
if [ "$#" -ne 0 ]; then
  printf '%s\n' 'uso: alis_pivot_sketch.sh [--grounded-converted]' >&2
  exit 2
fi
rtk proxy ffmpeg -v error -nostdin -n -filter_complex_threads 1 -threads 1 \
  -loop 1 -framerate 60 -i "$source_png" \
  -filter_complex '[0:v]split=5[a][b][c][d][e];[a]crop=367:724:0:0,pad=632:724:24:0,scale=158:180:flags=neighbor,trim=end_frame=8,setpts=PTS-STARTPTS[a0];[b]crop=391:724:367:0,pad=632:724:18:0,scale=158:180:flags=neighbor,trim=end_frame=7,setpts=PTS-STARTPTS[b0];[c]crop=602:724:758:0,pad=632:724:22:0,scale=158:180:flags=neighbor,trim=end_frame=3,setpts=PTS-STARTPTS[c0];[d]crop=401:724:1360:0,pad=632:724:56:0,scale=158:180:flags=neighbor,trim=end_frame=6,setpts=PTS-STARTPTS[d0];[e]crop=367:724:0:0,pad=632:724:24:0,scale=158:180:flags=neighbor,trim=end_frame=12,setpts=PTS-STARTPTS[e0];[a0][b0][c0][d0][e0]concat=n=5:v=1:a=0,loop=loop=3:size=36:start=0,format=yuv420p[out]' \
  -map '[out]' -frames:v 144 -c:v libx264 -threads 1 -preset ultrafast -crf 18 \
  -movflags +faststart "$out_dir/sequence_01_pivot_sketch_normal.mp4"
rtk proxy ffmpeg -v error -nostdin -n -threads 1 \
  -i "$out_dir/sequence_01_pivot_sketch_normal.mp4" \
  -vf 'setpts=4*PTS' -r 60 -c:v libx264 -threads 1 -preset ultrafast -crf 18 \
  "$out_dir/sequence_01_pivot_sketch_slow.mp4"
