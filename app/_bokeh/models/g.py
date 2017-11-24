# global variable names for Bokeh apps
import os

# Bokeh
BOKEH_HOST    = "http://localhost:5000/bokeh/"
BOKEH_DEV     = True if os.environ.get('BOKEH_PY_LOG_LEVEL') == 'debug' else False
DEBOUNCE_VAL  = 200  # ms (int)
SERVER_PERIOD = 5    # ms (int)
DATA_FREQ_VAL = 5    # ms (int)

TOOLS1 = "xpan, xbox_select, resize, xwheel_zoom, xwheel_pan, reset, crosshair, save"
TOOLS2 = "pan, box_zoom, resize, xwheel_zoom, ywheel_zoom, xwheel_pan, ywheel_pan, reset, crosshair, save"
TOOLS3 = "pan, box_select, box_zoom, resize, wheel_zoom, reset, save, crosshair, save"

# Device index for calibration and measurement
d_idx = None

# Calibration
WITH_LINEAR_COEF = False
coef             = []
c_ang            = None
c_lin            = None

# Mosquitto
MQTT_HOST = "localhost"
MQTT_PORT = 1883

TOKEN     = None
CTRL_ID   = None
device_id = None

t_period         = ""
t_device_ctrl    = ""
t_measure        = ""
t_device_ctrl_cb = ""
t_calibration    = ""

# Micropython timers
# https://github.com/micropython/micropython/blob/master/tests/extmod/ticks_diff.py
# MAXTIME =  0x3fffffffffffffff # 62 bits for micropython unix
# MAXTIME = 0x3fffffff          # 30 bits for micropython ESP
# MAXTIME = 0x7fffffff          # 31 bits for nodemcu

T_INTERVAL =  0x4000000000000000 # 62 bits for micropython unix
# T_INTERVAL = 0x40000000          # 30 bits for micropython ESP
# T_INTERVAL = 0x80000000          # 31 bits for nodemcu
T_PERIOD = T_INTERVAL // 2
