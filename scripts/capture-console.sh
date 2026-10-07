#!/usr/bin/env bash
set -euo pipefail
repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"
for command in xwininfo xprop ffmpeg pipewire pw-cat pw-dump dotnet rg python3; do
    command -v "$command" >/dev/null || { echo "Missing $command" >&2; exit 77; }
done
python3 -c 'from PIL import Image' >/dev/null
[[ -n "${DISPLAY:-}" ]] || exit 77
if xwininfo -root -tree | rg '"Fadrio"' >/dev/null; then
    echo 'Close the existing Fadrio window before capturing.' >&2
    exit 1
fi
fadrio_capture_dir=$(mktemp -d -t fadrio-console-XXXXXX)
fadrio_capture_pids=()
cleanup() {
    for fadrio_capture_pid in "${fadrio_capture_pids[@]}"; do kill "$fadrio_capture_pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
    printf 'capture_dir=%s\n' "$fadrio_capture_dir"
}
trap cleanup EXIT INT TERM
export XDG_RUNTIME_DIR="$fadrio_capture_dir"
export PIPEWIRE_RUNTIME_DIR="$fadrio_capture_dir"
export PIPEWIRE_REMOTE=pipewire-0
export XDG_DATA_HOME="$fadrio_capture_dir/share"
export XDG_CACHE_HOME="$fadrio_capture_dir/cache"
export LD_LIBRARY_PATH="$PWD/build/native"
export FADRIO_UI_CAPTURE_DIR="$fadrio_capture_dir"
mkdir -p "$XDG_DATA_HOME/applications" "$XDG_DATA_HOME/icons"
cp assets/branding/raster/fadrio-app-icon-monochrome.png "$XDG_DATA_HOME/icons/fadrio-fixture.png"
for fadrio_capture_name in Browser Chat Game Music; do
    cat >"$XDG_DATA_HOME/applications/dev.fglabs.Fadrio.Capture$fadrio_capture_name.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$fadrio_capture_name (fixture)
Exec=fadrio-capture-$fadrio_capture_name
EOF
done
pipewire -c "$PWD/tests/fixtures/pipewire/fadrio-test.conf" >"$fadrio_capture_dir/pipewire.log" 2>&1 &
fadrio_capture_pids+=("$!")
for _ in {1..100}; do [[ -S "$fadrio_capture_dir/pipewire-0" ]] && break; sleep .05; done
[[ -S "$fadrio_capture_dir/pipewire-0" ]]
start_stream() {
    pw-cat --playback --target 0 --rate 48000 --channels 2 --format s16 --volume "$2" \
        -P "{ application.name = \"$1 (fixture)\" application.id = \"dev.fglabs.Fadrio.Capture$1\" application.icon-name = \"$3\" }" \
        - </dev/zero >>"$fadrio_capture_dir/streams.log" 2>&1 &
    fadrio_capture_pids+=("$!")
}
start_stream Browser .2 fadrio-fixture
start_stream Browser .8 fadrio-fixture
start_stream Chat .6 missing-fixture-icon
start_stream Game .78 missing-fixture-icon
start_stream Music .35 missing-fixture-icon
env -u WAYLAND_DISPLAY dotnet "$PWD/src/Fadrio.UI/bin/Debug/net10.0/fadrio.dll" >"$fadrio_capture_dir/ui.log" 2>&1 &
fadrio_capture_ui_pid=$!
fadrio_capture_pids+=("$fadrio_capture_ui_pid")
fadrio_capture_window=""
for _ in {1..300}; do
    fadrio_capture_window=$(xwininfo -root -tree | awk '/"Fadrio"/ && !/mutter/ {if (!found) print $1; found=1}')
    [[ -n "$fadrio_capture_window" ]] && break
    sleep .1
done
[[ -n "$fadrio_capture_window" ]]
xprop -id "$fadrio_capture_window" _NET_WM_PID | rg -F "= $fadrio_capture_ui_pid" >/dev/null
sleep 2
# Seed actual observed levels through the same native bridge as the app.
# Raw node IDs remain inside this private diagnostic capture fixture.
python3 - "$PWD/build/native/libfadrio_native.so" <<'PYSEED'
import ctypes as c
import json
import subprocess
import sys
import threading
import time

class EventPrefix(c.Structure):
    _fields_ = [('size', c.c_uint32), ('type', c.c_int), ('generation', c.c_uint64)]
ready = threading.Event()
@c.CFUNCTYPE(None, c.c_void_p, c.c_void_p)
def callback(pointer, _):
    event_type = c.cast(pointer, c.POINTER(EventPrefix)).contents.type
    if event_type == 1: ready.set()
lib = c.CDLL(sys.argv[1])
lib.vm_context_create.argtypes = [type(callback), c.c_void_p]
lib.vm_context_create.restype = c.c_void_p
lib.vm_start.argtypes = [c.c_void_p]
lib.vm_set_stream_volume.argtypes = [c.c_void_p, c.c_uint32, c.c_float]
lib.vm_context_destroy.argtypes = [c.c_void_p]
context = lib.vm_context_create(callback, None)
assert context
try:
    assert lib.vm_start(context) == 0
    assert ready.wait(5), 'Native fixture did not connect'
    nodes = json.loads(subprocess.check_output(['pw-dump'], text=True))
    levels = {'Browser': [.2, .8], 'Chat': [.6], 'Game': [.78], 'Music': [.35]}
    for name, volumes in levels.items():
        matches = [node for node in nodes if node.get('type') == 'PipeWire:Interface:Node'
                   and node.get('info', {}).get('props', {}).get('application.id') == 'dev.fglabs.Fadrio.Capture' + name]
        assert len(matches) == len(volumes), (name, len(matches))
        for node, volume in zip(matches, volumes):
            deadline = time.monotonic() + 5
            while lib.vm_set_stream_volume(context, node['id'], volume) != 0:
                assert time.monotonic() < deadline, 'Native fixture volume failed'
                time.sleep(.1)
finally:
    lib.vm_context_destroy(context)
PYSEED
sleep 1
dotnet src/Fadrio.Cli/bin/Debug/net10.0/fadrioctl.dll mute xdg:dev.fglabs.Fadrio.CaptureMusic >"$fadrio_capture_dir/mute.txt"
dotnet src/Fadrio.Cli/bin/Debug/net10.0/fadrioctl.dll apps >"$fadrio_capture_dir/apps.txt"
[[ $(rg -c '^Application:' "$fadrio_capture_dir/apps.txt") == 4 ]]
sleep 1
ffmpeg -hide_banner -loglevel error -f x11grab -window_id "$fadrio_capture_window" \
    -video_size 940x680 -i "$DISPLAY" -frames:v 1 "$fadrio_capture_dir/before.png"
export FADRIO_UI_REFERENCE_CAPTURE="$fadrio_capture_dir/before.png"
python3 scripts/ui-interaction-probe.py "$fadrio_capture_window" "$PWD" --preview
kill -0 "$fadrio_capture_ui_pid"
