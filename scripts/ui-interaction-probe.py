import ctypes as c
import os
import re
import signal
import subprocess
import sys
import time
from PIL import Image
from itertools import groupby

window = int(sys.argv[1], 16)
root_path = sys.argv[2]
with Image.open(os.environ['FADRIO_UI_REFERENCE_CAPTURE']).convert('RGB') as capture:
    # Find the first real vertical fader by its green value track.
    candidates = []
    for px in range(30, capture.width - 30):
        pixels = [py for py in range(180, capture.height - 60)
                  if (lambda rgb: rgb[1] > rgb[0] + 45 and rgb[2] > rgb[0] + 35)(capture.getpixel((px, py)))]
        runs = [[value for _, value in group] for _, group in groupby(enumerate(pixels), lambda pair: pair[1] - pair[0])]
        longest = max(runs, key=len, default=[])
        if len(longest) > 100:
            candidates.append((px, longest))
    assert candidates, 'No rendered vertical fader found'
    first = [candidate for candidate in candidates if candidate[0] < candidates[0][0] + 8]
    slider_x, track_pixels = first[len(first) // 2]
    slider_top = min(track_pixels) - 8
    slider_bottom = max(track_pixels) - 8
    slider_target = round(slider_top + .63 * (slider_bottom - slider_top))
mute_y = max(track_pixels) + 44
x = c.CDLL('libX11.so.6')
t = c.CDLL('libXtst.so.6')
x.XOpenDisplay.restype = c.c_void_p
x.XDefaultRootWindow.argtypes = [c.c_void_p]
x.XDefaultRootWindow.restype = c.c_ulong
x.XGetInputFocus.argtypes = [c.c_void_p, c.POINTER(c.c_ulong), c.POINTER(c.c_int)]
x.XSetInputFocus.argtypes = [c.c_void_p, c.c_ulong, c.c_int, c.c_ulong]
x.XRaiseWindow.argtypes = [c.c_void_p, c.c_ulong]
x.XFlush.argtypes = [c.c_void_p]
x.XCloseDisplay.argtypes = [c.c_void_p]
x.XTranslateCoordinates.argtypes = [c.c_void_p, c.c_ulong, c.c_ulong, c.c_int, c.c_int, c.POINTER(c.c_int), c.POINTER(c.c_int), c.POINTER(c.c_ulong)]
x.XStringToKeysym.argtypes = [c.c_char_p]
x.XStringToKeysym.restype = c.c_ulong
x.XKeysymToKeycode.argtypes = [c.c_void_p, c.c_ulong]
x.XKeysymToKeycode.restype = c.c_uint
x.XQueryPointer.argtypes = [c.c_void_p, c.c_ulong, c.POINTER(c.c_ulong), c.POINTER(c.c_ulong), c.POINTER(c.c_int), c.POINTER(c.c_int), c.POINTER(c.c_int), c.POINTER(c.c_int), c.POINTER(c.c_uint)]
x.XInternAtom.argtypes = [c.c_void_p, c.c_char_p, c.c_int]
x.XInternAtom.restype = c.c_ulong

class ClientMessage(c.Structure):
    _fields_ = [('type', c.c_int), ('serial', c.c_ulong), ('send_event', c.c_int),
               ('display', c.c_void_p), ('window', c.c_ulong),
               ('message_type', c.c_ulong), ('format', c.c_int), ('data', c.c_long * 5)]

class Event(c.Union):
    _fields_ = [('message', ClientMessage), ('padding', c.c_long * 24)]

x.XSendEvent.argtypes = [c.c_void_p, c.c_ulong, c.c_int, c.c_long, c.POINTER(Event)]
x.XResizeWindow.argtypes = [c.c_void_p, c.c_ulong, c.c_uint, c.c_uint]
t.XTestFakeMotionEvent.argtypes = [c.c_void_p, c.c_int, c.c_int, c.c_int, c.c_ulong]
t.XTestFakeButtonEvent.argtypes = [c.c_void_p, c.c_uint, c.c_int, c.c_ulong]
t.XTestFakeKeyEvent.argtypes = [c.c_void_p, c.c_uint, c.c_int, c.c_ulong]
d = x.XOpenDisplay(None)
assert d, 'No X11 display'
root = x.XDefaultRootWindow(d)
old_focus, revert = c.c_ulong(), c.c_int()
x.XGetInputFocus(d, c.byref(old_focus), c.byref(revert))
root_ret, child = c.c_ulong(), c.c_ulong()
old_x, old_y, win_x, win_y, mask = c.c_int(), c.c_int(), c.c_int(), c.c_int(), c.c_uint()
x.XQueryPointer(d, root, c.byref(root_ret), c.byref(child), c.byref(old_x), c.byref(old_y), c.byref(win_x), c.byref(win_y), c.byref(mask))
origin_x, origin_y = c.c_int(), c.c_int()
x.XTranslateCoordinates(d, window, root, 0, 0, c.byref(origin_x), c.byref(origin_y), c.byref(child))

def move(px, py):
    t.XTestFakeMotionEvent(d, -1, origin_x.value + px, origin_y.value + py, 0)
    x.XFlush(d)
    time.sleep(.08)

def button(down):
    t.XTestFakeButtonEvent(d, 1, down, 0)
    x.XFlush(d)
    time.sleep(.08)

def key(name):
    code = x.XKeysymToKeycode(d, x.XStringToKeysym(name.encode()))
    t.XTestFakeKeyEvent(d, code, 1, 0)
    t.XTestFakeKeyEvent(d, code, 0, 0)
    x.XFlush(d)
    time.sleep(.08)

def activate():
    # Ask the window manager to activate the owned window. Merely assigning
    # X input focus can leave GNOME's active-window state on the prior app.
    event = Event()
    event.message.type = 33  # ClientMessage
    event.message.display = d
    event.message.window = window
    event.message.message_type = x.XInternAtom(d, b'_NET_ACTIVE_WINDOW', 0)
    event.message.format = 32
    event.message.data[0] = 2  # pager/test activation request
    x.XSendEvent(d, root, 0, (1 << 20) | (1 << 19), c.byref(event))
    x.XFlush(d)
    time.sleep(.3)
    focus = c.c_ulong()
    focus_revert = c.c_int()
    x.XGetInputFocus(d, c.byref(focus), c.byref(focus_revert))
    assert focus.value == window, f'Owned window did not receive keyboard focus: {focus.value:#x}'

def state():
    output = subprocess.check_output(['dotnet', root_path + '/src/Fadrio.Cli/bin/Debug/net10.0/fadrioctl.dll', 'apps'], text=True)
    assert 'Application: Fadrio Fixture' in output, output
    return int(re.search(r'Volume: (\d+)%', output)[1]), 'Muted: true' in output

def wait_state(predicate):
    # UI commands run on a worker and PipeWire reports them asynchronously.
    deadline = time.monotonic() + 10
    observed = state()
    while not predicate(observed) and time.monotonic() < deadline:
        time.sleep(.1)
        observed = state()
    assert predicate(observed), observed
    return observed

try:
    activate()
    time.sleep(.5)
    x.XTranslateCoordinates(d, window, root, 0, 0, c.byref(origin_x), c.byref(origin_y), c.byref(child))
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        def capture_preview(name):
            geometry = subprocess.check_output(['xwininfo', '-id', hex(window)], text=True)
            width = re.search(r'Width: (\d+)', geometry)[1]
            height = re.search(r'Height: (\d+)', geometry)[1]
            move(400, 110)
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'x11grab',
                            '-window_id', hex(window), '-video_size', width + 'x' + height,
                            '-i', os.environ['DISPLAY'], '-frames:v', '1',
                            os.environ['FADRIO_UI_CAPTURE_DIR'] + '/' + name + '.png'], check=True)

        for name, count in [('console-dark', 2), ('console-light', 1)]:
            activate()
            move(870, 42)
            button(1)
            button(0)
            key('Home')
            for _ in range(count): key('Down')
            key('Return')
            time.sleep(.7)
            capture_preview(name)
        x.XResizeWindow(d, window, 420, 680)
        x.XFlush(d)
        time.sleep(.7)
        x.XTranslateCoordinates(d, window, root, 0, 0, c.byref(origin_x), c.byref(origin_y), c.byref(child))
        capture_preview('console-narrow')
        print('Captured real multi-application console, dark/light themes and narrow viewport', flush=True)
        sys.exit(0)
    if len(sys.argv) > 3:
        # The shell passes only its own isolated daemon PID.
        move(slider_x, slider_target)
        button(1)
        move(slider_x, slider_target + 20)
        os.kill(int(sys.argv[3]), signal.SIGTERM)
        time.sleep(1)
        move(slider_x, slider_target)
        button(0)
        print('Disconnected the isolated daemon during an active drag', flush=True)
        sys.exit(0)
    wait_state(lambda observed: observed[0] == 100)
    move(slider_x, slider_top)
    button(1)
    for step in range(1, 9): move(slider_x, round(slider_top + (slider_target - slider_top) * step / 8))
    button(0)
    volume, muted = wait_state(lambda observed: 35 <= observed[0] <= 45)
    print('Rendered slider drag reached', volume, 'percent', flush=True)
    # Reassert focus after the separate CLI probe; the desktop may redirect it.
    activate()
    # A recreated row has a new control; focus that slider explicitly before
    # testing its keys, rather than relying on desktop activation history.
    move(slider_x, slider_target)
    button(1)
    button(0)
    key('Home')
    for _ in range(10): key('Up')
    volume, muted = wait_state(lambda observed: observed[0] == 10)
    print('Keyboard Home + ten Up keys reached 10 percent', flush=True)
    move(slider_x, mute_y)
    button(1)
    button(0)
    wait_state(lambda observed: observed[1])
    print('Rendered mute button muted the isolated stream', flush=True)
except Exception:
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'x11grab',
                    '-window_id', hex(window), '-video_size', str(capture.width) + 'x' + str(capture.height),
                    '-i', os.environ['DISPLAY'], '-frames:v', '1',
                    os.path.dirname(os.environ['FADRIO_UI_REFERENCE_CAPTURE']) + '/probe-failure.png'])
    raise
finally:
    t.XTestFakeButtonEvent(d, 1, 0, 0)
    t.XTestFakeMotionEvent(d, -1, old_x.value, old_y.value, 0)
    if old_focus.value > 1: x.XSetInputFocus(d, old_focus.value, revert.value, 0)
    x.XFlush(d)
    x.XCloseDisplay(d)
