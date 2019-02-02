#!/usr/bin/env python3

# Use setup() to 
#   * Load a dictionary formatted as below
#   * Provide an input handler object with a method:
#     handler.on_input(controller, event, value)
#
# call start() to begin handling input
# call stop() to temporarily release devices
# call start() again to open them again with the same configuration
# call shutdown() to kill the background thread
#
# Analog controls get a value between -1.0 and 1.0
# Buttons get 1 for "pressed" and 0 for "released"
#
# Analog axes can be bound to ax0, ax1, ax2, etc.
# Buttons can be bound to b0, b1, ...
# Buttons can be bound to ax0-, ax0+, ax1-, ...
#
# controller is one of "controller1", "controller2", "console"


import os
import struct
import array
import json
import sys
import select
import evdev
import threading
import time
from fcntl import ioctl

# This maps to a plugged-in Dual-shock 4 for player 1
# and the keyboard for player 2.
DEFAULT_MAP = json.loads("""
{
   "controller1": {
      "device": "/dev/input/js0",

      "axis-X1": "ax0",
      "axis-Y1": "ax1",
      "axis-X2": "ax3",
      "axis-Y2": "ax4",

      "button-Y": "b2",
      "button-X": "b3",
      "button-B": "b1",
      "button-A": "b0",

      "dpad-up": "ax7-",
      "dpad-down": "ax7+",
      "dpad-left": "ax6-",
      "dpad-right": "ax6+",

      "bumper-L": "b4",
      "bumper-R": "b5",
      "trigger-L": "b6",
      "trigger-R": "b7",

      "L3": "b11",
      "R3": "b12"
   },

   "controller2": {
      "device": "keyboard",

      "button-Y": "i",
      "button-X": "j",
      "button-B": "l",
      "button-A": "k",

      "dpad-up": "w",
      "dpad-down": "s",
      "dpad-left": "a",
      "dpad-right": "d",

      "bumper-L": "q",
      "bumper-R": "e",
      "trigger-L": "1",
      "trigger-R": "3",

      "L3": "z",
      "R3": "x"
   },

	"console": {
    "device": "keyboard",
		"quit": "esc"
	}
}
""")


class Joydev:
  def __init__(self, device):
    self.device = device
    self.fd = None

    if (not os.path.exists(self.device)):
      raise RuntimeError("Unable to find joystick device {}".format(self.device))

    # Maps from event number to axis/button name
    self.axis_map = {}
    self.button_map = {}

    # Last known state
    self.axis_state = {}
    self.axis_discrete = {}
    self.button_state = {}

  def _configure(self):

    # Get the device name.
    buf = bytearray(64)
    ioctl(self.fd, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
    js_name = buf.decode("ascii")
    sys.stderr.write('{} is {}\n'.format(self.device, js_name))

    # Get number of axes and buttons.
    buf = bytearray(1)
    ioctl(self.fd, 0x80016a11, buf) # JSIOCGAXES
    num_axes = buf[0]

    buf = bytearray(1)
    ioctl(self.fd, 0x80016a12, buf) # JSIOCGBUTTONS
    num_buttons = buf[0]

    # Get the axis map.
    buf = array.array('B', [0] * 0x40)
    ioctl(self.fd, 0x80406a32, buf) # JSIOCGAXMAP

    index = 0
    for axis in buf[:num_axes]:
        axis_name = "ax{}".format(index)
        self.axis_map[index] = axis_name
        self.axis_state[axis_name] = 0.0
        self.axis_discrete[axis_name] = 0
        index += 1

    # Get the button map.
    buf = array.array('H', [0] * 200)
    ioctl(self.fd, 0x80406a34, buf) # JSIOCGBTNMAP

    index = 0
    for btn in buf[:num_buttons]:
        btn_name = "b{}".format(index)
        self.button_map[index] = btn_name
        self.button_state[btn_name] = 0
        index += 1

    #sys.stderr.write('%d axes found: %s\n' % (num_axes, ', '.join(self.axis_map.values())))
    #sys.stderr.write('%d buttons found: %s\n' % (num_buttons, ', '.join(self.button_map.values())))

  def start(self):
    if (self.fd is not None): return
    self.fd = open(self.device, "rb")
    self._configure()

  def stop(self):
    if (self.fd is None): return
    self.fd.close()
    self.fd = None

  def fileno(self):
    return self.fd.fileno()

  # Waits for a bit, returns True if there's an event.
  def wait(self):
    ready,_,_ = select.select([self], [], [], 0.5)
    if len(ready) > 0: return True
    return False

  # Do a select() on the joydev or use joydev.wait()
  # then call this to read and parse one event
  # returns None if the event was for initial state
  # Returns a list of tuples of 
  # returns "b0",1 for button presses
  # returns "ax2",-0.4 for axis changes
  def get_event(self):
    evbuf = self.fd.read(8)
    if evbuf:
      time, value, type, number = struct.unpack('IhBB', evbuf)

      ret = []

      if type & 0x01:
        # Button event
        btn_name = self.button_map[number]
        if btn_name:
          self.button_state[btn_name] = value
          if value:
            ret += [(btn_name,1)]
          else:
            ret += [(btn_name,0)]

      if type & 0x02:
        # Axis event
        ax_name = self.axis_map[number]
        if ax_name:

          # Analog axis event
          fvalue = value / 32767.0
          ret += [(ax_name, fvalue)]
          self.axis_state[ax_name] = fvalue


          # Discrete (ax+ and ax-) events
          discrete = self.axis_discrete[ax_name]
          if (fvalue > 0.75): discrete = 1
          elif (fvalue < -0.75): discrete = -1
          elif (fvalue < 0.1 and fvalue > -0.1): discrete = 0

          # If the axis moved enough, make it either a button press or release
          if (discrete != self.axis_discrete[ax_name]):

            if (discrete == 1):
              ret += [ (ax_name+"+", 1) ]   # Pressed
            elif (discrete == -1):
              ret += [ (ax_name+"-", 1) ]   # Pressed
            else:
              if (self.axis_discrete[ax_name] == 1):
                ret += [ (ax_name+"+", 0) ]   # Released

              if (self.axis_discrete[ax_name] == -1):
                ret += [ (ax_name+"-", 0) ]   # Released

            self.axis_discrete[ax_name] = discrete

      if type & 0x80:
         ret = None

      return ret


class Keyboard:

  def __init__(self):
    self.device = None
    self.evdev = None

    # Go through available devices and pick the first that seems
    # to be a keyboard
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    self.device = None
    for device in devices:
      caps = device.capabilities(verbose=True)
      K1 = ('EV_KEY', 1)
      if K1 not in caps: continue

      keymap = caps[K1]
      for keycode, number in keymap:
        if (keycode == "KEY_Q"):
          self.device = device.path
          break

      if self.device is not None:
        break

    if self.device is None:
      raise RuntimeError("Unable to locate a keyboard. Permissions to /dev/input/event* ?")

    self.button_map = {}
    # Lazy extraction of all the evdev keycodes
    # If a key is named KEY_VIDEO_PREV, we will map it to "video_prev"
    # This is less sensitive to portability issues, since the keyboard isn't really
    # important other than for local testing.
    # The basic keys (letters, space, bakspace, etc.) will have neatly predictable names.
    # Some other useful ones are esc,enter,leftshift,leftctrl,left,up,pageup,f1
    for code,name in evdev.ecodes.KEY.items():
      if isinstance(name, str):
        short_name = name.replace("KEY_", "").lower()
        self.button_map[code] = short_name


  def start(self):
    if (self.evdev is not None): return

    self.evdev = evdev.InputDevice(self.device)

  def stop(self):
    if (self.evdev is None): return
    self.evdev.close()
    self.evdev = None

  def fileno(self):
    return self.evdev.fd

  def wait(self):
    ready,_,_ = select.select([self], [], [], 0.5)
    if len(ready) > 0: return True
    return False

  def get_event(self):
    events = self.evdev.read()
    ret = []
    for ev in events:
      if ev.type == evdev.ecodes.EV_KEY:
        # ev.val == 1 for press, 0 for release
        if ev.value == 0 or ev.value == 1:
          if ev.code in self.button_map:
            ret += [ (self.button_map[ev.code],ev.value) ]
          else:
            sys.stderr.write("WARNING: Unhandled keyboard input code {}".format(ev.code))
    return ret


# A persistent thread that checks all input devices and
# routes the proper events to the input handler
class InputThread(threading.Thread):

  def __init__(self, input_handler, game_conf):
    threading.Thread.__init__(self)

    # Thread management
    self.do_shutdown = False
    self.is_enabled = threading.Event()
    self.is_enabled.clear()

    self.input_handler = input_handler


    # For each loaded input device, there's an object in DEVICES
    # For each device, there is a map of 
    # button/axis/key/whatever to a tuple of
    # (controller, event)
    #
    self.DEVICES = {}
    self.CONTROLLER_MAP = {}

    self.DEVICES["keyboard"] = Keyboard()
    self.CONTROLLER_MAP[self.DEVICES["keyboard"]] = {}

    for controller in [ "controller1", "controller2", "console" ]:

      if controller not in game_conf:
        raise RuntimeError("Controller {} missing.".format(controller))

      cmap = game_conf[controller]

      if "device" not in cmap:
        raise RuntimeError("Controller {} does not have a device specified.".format(controller))

      device = cmap["device"]
      if device not in self.DEVICES:
        # Previously unused joystick device
        self.DEVICES[device] = Joydev(device)
        self.CONTROLLER_MAP[self.DEVICES[device]] = {}

      for event,button in cmap.items():
        if event == "device": continue
        #sys.stderr.write("Mapping {} to ({}, {})\n".format(button, controller, event))
        self.CONTROLLER_MAP[self.DEVICES[device]][button] = (controller, event)

    sys.stderr.write("Spawning input thread\n")
    self.start()


  def resume(self):
    for dev,handler in self.DEVICES.items():
      handler.start()
    self.is_enabled.set()

  def pause(self):
    self.is_enabled.clear()
    for dev,handler in self.DEVICES.items():
      handler.stop()

  def shutdown(self):
    self.do_shutdown = True
    self.is_enabled.set()


  def run(self):
    while not self.do_shutdown:

      # Allow the input to be paused
      self.is_enabled.wait()
      if self.do_shutdown: break

      ready,_,_ = select.select([ handler for _,handler in self.DEVICES.items()] , [], [], 0.1)
      if len(ready) > 0:
        # Get control events like "ax1 moved to 0.32"
        for handler in ready:
          cmap = self.CONTROLLER_MAP[handler]
          inputs = handler.get_event()

          if inputs is None: continue

          # Mape those controls to events like "axis-X1"
          for control,value in inputs:
            if control in cmap:
              controller,event = cmap[control]
              self.input_handler.on_input(controller, event, value)




INPUT_THREAD = None


def setup(input_handler, game_conf):
  global INPUT_THREAD
  if INPUT_THREAD is not None: return
  if game_conf is None: game_conf = DEFAULT_MAP
  INPUT_THREAD = InputThread(input_handler, game_conf)

def start():
  global INPUT_THREAD
  if INPUT_THREAD is None: return
  INPUT_THREAD.resume()

def stop():
  global INPUT_THREAD
  if INPUT_THREAD is None: return
  INPUT_THREAD.pause()

def shutdown():
  global INPUT_THREAD
  if INPUT_THREAD is None: return
  INPUT_THREAD.shutdown()









def main():
  print("Running input mapper")

  class Dummy:
    def on_input(self, controller, event, value):
      print("{} {} -> {}".format(controller, event, value))
      if (event == "quit"):
        shutdown()


  if (True):
    dummy_handler = Dummy()
    setup(dummy_handler, DEFAULT_MAP)
    start()

  elif (False):
    if (False):
      # Open the joystick device.
      fn = '/dev/input/js0'
      print('Opening %s...' % fn)
      dev = Joydev(fn)
    else:
      dev = Keyboard()


    dev.start()

    while True:
      if (dev.wait()):
        events = dev.get_event()
        if (events is not None):
          for ev in events:
            print(ev)

  return 0

if __name__ == "__main__":
  sys.exit(main())
