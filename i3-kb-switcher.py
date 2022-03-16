#!/usr/bin/env python3

'''
The script remembers current layout for an focused window,
and activates it automatically when the same window gets focus again.

Autostart from the i3 config:
  exec_always --no-startup-id ~/scripts/i3-kb-switcher.py

Dependencies:
  xkb-switch (https://github.com/grwlf/xkb-switch)
'''

import i3ipc
import logging
import os
from subprocess import check_output, STDOUT
import threading

POLL_RATE = 2 # seconds
PID_FILE = '/tmp/i3-kb-switcher.pid'
os.environ['DISPLAY'] = ':0'
layouts_map = {}

#logging.basicConfig(filename='/tmp/i3-kb-switcher.log', level=logging.DEBUG)
log = logging.getLogger('kbsw')

def exec(args):
    try:
        return check_output(args, stderr=STDOUT).decode().strip()
    except Exception as e:
        out = e.output.strip()
        log.error(out)
        return out

def on_window_focus(i3, event):
    id = event.container.id
    log.debug('%s got focus', id)
    l = layouts_map.get(id)
    if l != None:
        exec(['xkb-switch', '-s', l])
        log.debug('Set layout: %s', l)

def on_window_close(i3, event):
    id = event.container.id
    del layouts_map[id]
    log.debug('%s is closed', id)

def get_focused_window(windows):
    for w in windows:
        if w.focused:
            return w.id

def remember_layout():
    threading.Timer(POLL_RATE, remember_layout).start()
    windows = i3.get_tree().find_focused().workspace().descendants()
    focused = get_focused_window(windows)
    if focused != None:
        layout = exec('xkb-switch')
        layouts_map[focused] = layout
        log.debug('%s => %s', focused, layout)

def kill_old_copy():
    exec(['bash', '-c', 'kill -9 $(cat {})'.format(PID_FILE)])
    open(PID_FILE, 'w').write(str(os.getpid()))

def init_i3_conn():
    i3_sp = exec(['i3', '--get-socketpath'])
    log.debug('i3 socket path = %s', i3_sp)
    i3 = i3ipc.Connection(auto_reconnect=True, socket_path=i3_sp)
    i3.on('window::focus', on_window_focus)
    i3.on('window::close', on_window_close)
    return i3

###########################################################

i3 = init_i3_conn()
kill_old_copy()
remember_layout()
log.debug('<<< Started >>>')
i3.main()
