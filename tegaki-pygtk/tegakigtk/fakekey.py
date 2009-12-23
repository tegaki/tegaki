# -*- coding: utf-8 -*-

# Copyright (C) 2009 The Tegaki project contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Contributors to this file:
# - Mathieu Blondel

"""
Send fake key events in order to display text
where the cursor is currently located.
"""

import time
import os
import platform

if os.name == 'nt':
    from ctypes import *

    PUL = POINTER(c_ulong)
    class KeyBdInput(Structure):
        _fields_ = [("wVk", c_ushort),
                    ("wScan", c_ushort),
                    ("dwFlags", c_ulong),
                    ("time", c_ulong),
                    ("dwExtraInfo", PUL)]

    class HardwareInput(Structure):
        _fields_ = [("uMsg", c_ulong),
                    ("wParamL", c_short),
                    ("wParamH", c_ushort)]

    class MouseInput(Structure):
        _fields_ = [("dx", c_long),
                    ("dy", c_long),
                    ("mouseData", c_ulong),
                    ("dwFlags", c_ulong),
                    ("time",c_ulong),
                    ("dwExtraInfo", PUL)]

    class Input_I(Union):
        _fields_ = [("ki", KeyBdInput),
                    ("mi", MouseInput),
                    ("hi", HardwareInput)]

    class Input(Structure):
        _fields_ = [("type", c_ulong),
                    ("ii", Input_I)]

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x2
    KEYEVENTF_UNICODE = 0x4

    def _send_unicode_win(unistr):
        for ch in unistr:
            inp = Input()
            inp.type = INPUT_KEYBOARD

            inp.ii.ki.wVk = 0
            inp.ii.ki.wScan = ord(ch)
            inp.ii.ki.dwFlags = KEYEVENTF_UNICODE

            windll.user32.SendInput(1, byref(inp), sizeof(inp))
            
            inp.ii.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            windll.user32.SendInput(1, byref(inp), sizeof(inp))

    _send_unicode = _send_unicode_win

elif platform.system() == "Darwin":
    def _send_unicode_osx(unistr):
        # TODO: use CGPostKeyboardEvent?
        raise NotImplementedError

    _send_unicode = _send_unicode_osx

else:

    try:
        import pyatspi
        from gtk import gdk   

        def _send_unicode_atspi(unistr):
            for ch in unistr:
                keyval = gdk.unicode_to_keyval(ord(ch))
                pyatspi.Registry.generateKeyboardEvent(keyval, None,
                                                        pyatspi.KEY_SYM)

        _send_unicode = _send_unicode_atspi

    except ImportError:

        from ctypes import *

        try:
            Xlib = CDLL("libX11.so.6")
            Xtst = CDLL("libXtst.so.6")
            KeySym = c_uint
            Xlib.XGetKeyboardMapping.restype = POINTER(KeySym)
        except OSError:
            Xlib = None

        def _send_unicode_x11(unistr):
            if Xlib is None: raise NameError

            dpy = Xlib.XOpenDisplay(None)

            if not dpy: raise OSError # no display

            min_, max_, numcodes = c_int(0), c_int(0), c_int(0)
            Xlib.XDisplayKeycodes(dpy, byref(min_), byref(max_))

            for ch in unistr:
                sym = Xlib.XStringToKeysym("U" + hex(ord(ch)).replace("0x", ""))

                keysym = Xlib.XGetKeyboardMapping(dpy, min_,
                                                max_.value-min_.value+1,
                                                byref(numcodes))

                keysym[(max_.value-min_.value-1)*numcodes.value] = sym

                Xlib.XChangeKeyboardMapping(dpy,min_,numcodes,keysym,
                                            (max_.value-min_.value))

                Xlib.XFree(keysym)
                Xlib.XFlush(dpy)

                code = Xlib.XKeysymToKeycode(dpy, sym)

                Xtst.XTestFakeKeyEvent(dpy, code, True, 1)
                Xtst.XTestFakeKeyEvent(dpy, code, False, 1)

            Xlib.XFlush(dpy)
            Xlib.XCloseDisplay(dpy)

        _send_unicode = _send_unicode_x11

def send_unicode(unistr):
    assert(isinstance(unistr, unicode))
    try:
        _send_unicode(unistr)
        return True
    except (OSError, NotImplementedError, NameError), e:
        return False
    except e, msg:
        print "send_unicode", e, msg
        return False

if __name__ == "__main__":
    send_unicode(u"漢字")