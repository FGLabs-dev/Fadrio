import ctypes as c
import os
import re
import signal
import subprocess
import sys
import time
from PIL import Image

window = int(sys.argv[1], 16)
root_path = sys.argv[2]
with Image.open(os.environ['FADRIO_UI_REFERENCE_CAPTURE']).convert('RGB') as capture:
    # Locate the long blue slider track in the actual rendering. Font metrics
    # can move the row; fixed Y coordinates gave false results with host fonts.
    candidates = []
    for py in range(capture.height):
        count = sum(1 for px in range(30, capture.width - 30)
                    if (lambda rgb: rgb[2] > rgb[0] + 60 and rgb[1] > rgb[0] + 30)(capture.getpixel((px, py))))
        if count > 150:
            candidates.append(py)
    assert candidates, 'No rendered slider track found'
    slider_y = candidates[len(candidates) // 2]
mute_y = slider_y + 48
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
    if len(sys.argv) > 3:
        # The shell passes only its own isolated daemon PID.
        move(73, slider_y)
        button(1)
        move(100, slider_y)
        os.kill(int(sys.argv[3]), signal.SIGTERM)
        time.sleep(1)
        move(146, slider_y)
        button(0)
        print('Disconnected the isolated daemon during an active drag', flush=True)
        sys.exit(0)
    wait_state(lambda observed: observed[0] == 100)
    move(314, slider_y)
    button(1)
    for px in [290, 265, 240, 215, 190, 165, 146]: move(px, slider_y)
    button(0)
    volume, muted = wait_state(lambda observed: 35 <= observed[0] <= 45)
    print('Rendered slider drag reached', volume, 'percent', flush=True)
    # Reassert focus after the separate CLI probe; the desktop may redirect it.
    activate()
    # A recreated row has a new control; focus that slider explicitly before
    # testing its keys, rather than relying on desktop activation history.
    move(146, slider_y)
    button(1)
    button(0)
    key('Home')
    for _ in range(10): key('Right')
    volume, muted = wait_state(lambda observed: observed[0] == 10)
    print('Keyboard Home + ten Right keys reached 10 percent', flush=True)
    move(62, mute_y)
    button(1)
    button(0)
    wait_state(lambda observed: observed[1])
    print('Rendered mute button muted the isolated stream', flush=True)
finally:
    t.XTestFakeButtonEvent(d, 1, 0, 0)
    t.XTestFakeMotionEvent(d, -1, old_x.value, old_y.value, 0)
    if old_focus.value > 1: x.XSetInputFocus(d, old_focus.value, revert.value, 0)
    x.XFlush(d)
    x.XCloseDisplay(d)
