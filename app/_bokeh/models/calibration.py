# coding: utf-8

# Bokeh app to get calibration data for the palmar grip electronic dynamometer.

from bokeh.layouts import widgetbox, layout, column
from bokeh.plotting import figure, curdoc
from bokeh.palettes import brewer
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter,\
NumberEditor, IntEditor, CheckboxGroup, Div, Button, Select, Toggle
from bokeh.models import ColumnDataSource, CustomJS, Legend, Label, \
HoverTool

# Custom models
from varModel.varModel import VarModel

# Mosquitto
import json
import paho.mqtt.client as mqtt

# Others
import g
import re
import util
import time
import numpy
import requests
from scipy.optimize import leastsq


##############################################################################
# Init

# open a session to keep the local document in sync with server
doc = curdoc()

new_data = dict()

try:
    args      = doc.session_context.request.arguments
    g.TOKEN   = args.get('token')[0]
    g.CTRL_ID = re.sub("[\W]", "", g.TOKEN)[7:23]

    url = "{}get_devices/{}/".format(g.BOKEH_HOST, g.TOKEN)
    req = requests.get(url)

    if g.BOKEH_DEV:
        print "req.content:", req.content[:20], "\n"

    DEVICES = req.json()
except:
    exit()

g.device_id = DEVICES['code'][0]
g.d_idx     = DEVICES['code'].index(g.device_id)

##############################################################################
# Sources

source      = ColumnDataSource(data=dict(f=[], v=[], index=[]))
source_fit  = ColumnDataSource(data=dict(x=[], y=[]))
source_regr = ColumnDataSource(data=dict(x=[], y=[]))


##############################################################################
# Mosquitto

conn_status = VarModel()
conn_status.value = False


def on_connect(client, userdata, flags, rc):
    if g.BOKEH_DEV:
        if g.BOKEH_DEV:
            print("\nMqtt: Connected with result code %s." % str(rc))

    if rc == 0:
        util.add_subscription(client, 'calibration')


def on_disconnect(client, userdata, rc):
    if rc != 0:
        client.loop_stop()

        if g.BOKEH_DEV:
            print("\nMqtt: Unexpected disconnection.\n")

    util.doc_next_tick(doc, util.conn_status_update, conn_status, False)


def on_subscribe(client, userdata, mid, granted_qos):
    if g.BOKEH_DEV:
        print("\nMqtt: Subscribed with mid %s.\n" % mid)


def on_unsubscribe(client, userdata, mid):
    if g.BOKEH_DEV:
        print("\nMqtt: Unsubscribed with mid %s." % mid)


def on_message(client, userdata, msg):
    if msg.topic == g.t_device_ctrl_cb:
        on_message_device_cb(client, msg)

    elif msg.topic == g.t_calibration:
        on_message_calibration(client, msg)


def on_message_device_cb(client, msg):
    device_cb_msg = str(msg.payload)

    if g.BOKEH_DEV:
        print(device_cb_msg)

    new_conn_status = None

    if device_cb_msg in ['successfully_connected', 'already_connected']:
        new_conn_status = True

    elif device_cb_msg == 'ok_to_unsubscribe':
        new_conn_status = False
        client.unsubscribe([g.t_calibration, g.t_device_ctrl_cb])
        util.doc_next_tick(doc, util.add_subscription, client, 'calibration')

    elif device_cb_msg in ['successfully_disconnected', 'no_control_allowed',
        'esp_init', 'esp_interrupted']:
        new_conn_status = False

    if new_conn_status is not None:
        util.doc_next_tick(doc, util.conn_status_update, conn_status, new_conn_status)


def on_message_calibration(client, msg):
    try:
        data = json.loads(msg.payload)
    except:
        if g.BOKEH_DEV:
            print(msg.payload)
        return

    if 'voltage' in data:
        global new_data

        _data_index = source.data['index']
        _new_index = [_data_index[-1] + 1] if _data_index else [0]

        try:
            _new_v = [int(data['voltage'])]
        except:
            if g.BOKEH_DEV:
                print(data)
            return

        new_data = dict(
            f  = [0.0],
            v  = _new_v,
            index = _new_index,
        )

        if g.BOKEH_DEV and new_data['v']:
            print('index: %3d | f: %7.3f | v: %4d' % (
                    new_data['index'][-1],
                    new_data['f'][-1],
                    new_data['v'][-1],
                )
            )


client = mqtt.Client(
    client_id=g.CTRL_ID,
    clean_session=True
)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_message = on_message

client.connect_async(host=g.MQTT_HOST, port=g.MQTT_PORT, keepalive=60)
client.loop_start()


##############################################################################
# Plot

plot = figure(
    plot_height      = 350,
    plot_width       = 732,
    x_axis_type      = 'linear',
    y_axis_type      = 'linear',
    tools            = g.TOOLS3,
    toolbar_location = "above",
    toolbar_sticky   = True,
    active_drag      = 'box_zoom',
    active_tap       = None,
    active_scroll    = 'wheel_zoom'
)
plot.x_range.update(start = 0)

if not g.WITH_LINEAR_COEF:
    plot.y_range.update(start = 0)

plot.xaxis.axis_label = "voltage (V/1023)"
plot.yaxis.axis_label = "force (N)"

circle = plot.circle(x='v', y='f', source=source)

color = brewer['Paired'][10][3]
line_regr = plot.line(x='x', y='y', source=source_regr, color=color)

color = brewer['Paired'][10][5]
circle_fit = plot.circle(x='x', y='y', source=source_fit, color=color)

plot.add_layout(Label(
    name                  = "save_confirmation",
    x                     = 80,
    y                     = plot.plot_height - 50,
    x_units               = 'screen',
    y_units               = 'screen',
    render_mode           = 'canvas',
    text                  = "",
    text_color            = 'red',
    text_font_size        = '1em',
    text_font_style       = 'bold',
    text_align            = 'left',
    text_baseline         = 'middle',
    border_line_alpha     = 0.0,
    background_fill_color = 'white',
    background_fill_alpha = 1.0,
))

plot.add_layout(Label(
    name                  = "linear_regression",
    x                     = 80,
    y                     = plot.plot_height - 70,
    x_units               = 'screen',
    y_units               = 'screen',
    render_mode           = 'canvas',
    text                  = "",
    text_font_size        = '0.8em',
    text_font_style       = 'normal',
    text_baseline         = 'middle',
    border_line_width     = 1.1,
    border_line_color     = 'black',
    border_line_alpha     = 0.0,
    background_fill_color = 'white',
    background_fill_alpha = 0.0,
))

legend = Legend(items = [
    ("force VS voltage"  , [circle]),
    ("Calibration curve" , [line_regr]),
    ("Calibrated points" , [circle_fit]),
], location = (5, -30))
plot.add_layout(legend, 'right')

hover = HoverTool(
    tooltips = [
        ("force", "$~y{0.0}"),
        ("voltage", "$~x{0.0}"),
    ],
    mode = 'vline',
    line_policy = "interp",
    renderers = [line_regr],
)
plot.add_tools(hover)


data_table = DataTable(
    source = source, width=400, height=327, editable=True,
    columns = [
        TableColumn(
            field = "f",
            title = "force (N)",
            editor = NumberEditor(step=0.001),
            formatter = NumberFormatter(format="0.000")
        ),
        TableColumn(
            field = "v",
            title = "voltage (V/1023)",
            editor = IntEditor(step=1)
        ),
    ]
)


##############################################################################
# Widgets

_div                 = Div(text=""" """, height=4)
checkbox             = CheckboxGroup(labels=['','',''], active=[0])
device_slc           = Select(title="Device ID:", value=g.device_id, options=DEVICES['code'])
device_conn_btn      = Toggle(label="Connect to device", button_type="success", active=True)
read_point_btn       = Button(label="Read point", button_type="primary")
clear_points_btn     = Button(label="Clear selected points", button_type="warning")
clear_everything_btn = Button(label="Clear everything", button_type="danger")
calibrate_btn        = Button(label="Get calibration curve", button_type="success")
save_btn             = Button(label="Save calibration", button_type="primary")
export_btn           = Button(label="Export points", button_type="success")


# Select: esp device selection by Id
def device_slc_callback(attr, old, new):
    g.device_id = new
    g.d_idx     = DEVICES['code'].index(g.device_id)

    if conn_status.value:
        util.doc_next_tick(doc, util.device_control, client, "unsub")
    else:
        client.unsubscribe([g.t_calibration, g.t_device_ctrl_cb])
        util.doc_next_tick(doc, util.add_subscription, client, 'calibration')

# Toggle button: esp device's connection control
def device_conn_btn_callback(new):
    if conn_status.value:
        command = "disc"
        plot.select_one('save_confirmation').update(text="")
    else:
        command = "conn"

    util.device_control(client, command)

def read_point_btn_callback():
    if conn_status.value:
        util.device_control(client, "calibrate")

def clear_calibration_data():
    """ Helper function for clear_points_btn_callback() and
    clear_everything_btn_callback() functions.
    """
    if source_fit.data['x'] or source_regr.data['x']:
        source_fit.data.update(x=[], y=[])
        source_regr.data.update(x=[], y=[])

        g.coef = []

        checkbox.active    = [0]
        circle.visible     = True
        line_regr.visible  = False
        circle_fit.visible = False

        plot.select_one('linear_regression').update(
            text = "",
            border_line_alpha = 0.0,
            background_fill_alpha = 0.0,
        )

def clear_points_btn_callback():
    ds_indices = source.selected['1d']['indices']
    if not ds_indices:
        if g.BOKEH_DEV:
            print("Nothing to clear: no data selected.\n")
        return False

    ds_indices.sort(reverse=True)

    for i in ds_indices:
        source.data['f'].pop(i)
        source.data['v'].pop(i)

    source.data['index'] = range(0, len(source.data['f']))

    clear_calibration_data()

    if g.BOKEH_DEV:
        print " "
        print "ds_indices:", ds_indices
        print "len(source.data['f']):", len(source.data['f'])
        print "source.data['f']: ", source.data['f']
        print "\n", "source:"

        for i in source.data['index']:
            _f  = source.data['f'][i]
            _v  = source.data['v'][i]
            print('index: %3d | f: %7.3f | v: %4d' % (i, _f, _v))

        print " "
        print "len(data_table.source.data['f']):", len(data_table.source.data['f'])
        print "data_table.source.data['f']:", data_table.source.data['f']
        print "\n", "data_table:"

        for i in data_table.source.data['index']:
            _f  = data_table.source.data['f'][i]
            _v  = data_table.source.data['v'][i]
            print('index: %3d | f: %7.3f | v: %4d' % (i, _f, _v))
        print " "

def clear_everything_btn_callback():
    source.data.update(f=[], v=[], index=[])
    clear_calibration_data()

def calibrate_btn_callback():
    if not source.data['f']:
        if g.BOKEH_DEV:
            print "Calibration Fail: no data to calibrate.", "\n"
        return

    g.coef = []
    if g.WITH_LINEAR_COEF:
        fit = lambda p, x: p[0] + p[1]*(x)
    else:
        fit = lambda p, x: p[0]*(x)
    err = lambda p, x, y: fit(p,x) - y

    # initial guess
    p0 = [0.0, 0.8] if g.WITH_LINEAR_COEF else [0.8]

    _x_ds = list(source.data['v'])
    _y_ds = list(source.data['f'])

    # calls scipy.optimize.leastsq() to find optimal parameters and converts
    # lists into numpy.array on the fly. Some info about convergence is
    # in success and the optimized parameters in coef.
    g.coef, success = leastsq(
        err, p0,
        args=(numpy.array(_x_ds), numpy.array(_y_ds)),
        ftol=5e-9, xtol=5e-9
    )

    # Calibration curve
    _x_regr = util.calibre_x_list(_x_ds)
    if g.WITH_LINEAR_COEF:
        source_regr.data.update(
            y = [g.coef[1]*_i + g.coef[0] for _i in _x_regr],
            x = _x_regr,
        )

        # Calibrated points
        source_fit.data.update(
            y = [g.coef[1]*_i + g.coef[0] for _i in _x_ds],
            x = _x_ds,
        )
    else:
        source_regr.data.update(
            y = [g.coef[0]*_i for _i in _x_regr],
            x = _x_regr,
        )

        # Calibrated points
        source_fit.data.update(
            y = [g.coef[0]*_i for _i in _x_ds],
            x = _x_ds,
        )

    checkbox.active    = [0, 1, 2]
    circle.visible     = True
    line_regr.visible  = True
    circle_fit.visible = True

    if g.WITH_LINEAR_COEF:
        sign = '+' if g.coef[0] >= 0.0 else '-'
        plot.select_one('linear_regression').update(
            text = " linear regression: f(x) = %.8f * x %s %.8f " %
                                               (abs(g.coef[1]), sign, abs(g.coef[0])),
            border_line_alpha = 1.0,
            background_fill_alpha = 1.0,
        )
    else:
        plot.select_one('linear_regression').update(
            text = " linear regression: f(x) = %.8f * x " % abs(g.coef[0]),
            border_line_alpha = 1.0,
            background_fill_alpha = 1.0,
        )

    if g.BOKEH_DEV:
        print " "
        print "coef:", g.coef
        print "y_regr:", source_regr.data['y']
        print "x_regr:", source_regr.data['x']
        print "y_fit:", source_fit.data['y']
        print "x_fit:", source_fit.data['x']

def save_btn_callback():
    if not g.coef:
        if g.BOKEH_DEV:
            print "Nothing to save: no calibration data.", "\n"
        return False

    data_save = dict(
        d_id = DEVICES['id'][g.d_idx],
        lin  = g.coef[0] if g.WITH_LINEAR_COEF else 0,
        ang  = g.coef[1] if g.WITH_LINEAR_COEF else g.coef[0],
    )

    url = "http://localhost:5000/bokeh/save_calibration/%s/" % g.TOKEN
    req = requests.post(url, json=data_save)

    if req.content == "successfully_saved":
        _text = "Calibration successfully saved!"
    else:
        _text = "Saving error: refresh the browser and try again."
    plot.select_one('save_confirmation').update(text=_text)

    if g.BOKEH_DEV:
        print "data_save:", data_save, "\n"
        print "req.content:", req.content[:20], "\n"


def clear_message(attr, old, new):
    plot.select_one('save_confirmation').update(text="")


source.on_change('data', clear_message)

hover.callback = CustomJS(
    args = dict(cb=checkbox),
    code = """
        if(!cb.active.includes(%d)) {
            document.getElementsByClassName('bk-tooltip')[%d].style.display = 'none';
        }
    """ % (1, 0)
)

checkbox.callback = CustomJS(
    args = dict(
        p0 = circle,
        p1 = line_regr,
        p2 = circle_fit,
    ),
    code = """
        //Toggle glyph visibility based on checkbox status
        p0.visible = cb_obj.active.includes(0);
        p1.visible = cb_obj.active.includes(1);
        p2.visible = cb_obj.active.includes(2);
    """
)

click_reset_tool = CustomJS(
    args = dict(p=plot),
    code = """
        p.toolbar.tools[""" + util.reset_tool_index(g.TOOLS3) + """].trigger('do');
    """
)

device_slc.on_change('value', device_slc_callback)
device_slc.js_on_change('value', CustomJS(
    args = dict(btn=clear_everything_btn),
    code = """
        document.getElementById('modelid_' + btn.id).click();
    """
))

device_conn_btn.on_click(device_conn_btn_callback)

conn_status.js_on_change('value', CustomJS(
    args = dict(btn=device_conn_btn),
    code = """
        console.log('This application is connected to ESP device: ' + cb_obj.value);

        if(cb_obj.value) {
            btn.label = "Disconnect from device";
            btn.button_type = "warning";
        } else {
            btn.label = "Connect to device";
            btn.button_type = "success";
        }
    """
))

read_point_btn.on_click(read_point_btn_callback)
read_point_btn.callback = CustomJS(
    args = dict(
        p  = plot,
        dt = data_table,
        conn_status = conn_status,
    ),
    code = """
        if(!conn_status.value) {
            console.log('This application must be connected to ESP device to read data from it.');
            return;
        }

        p.toolbar.tools[""" + util.reset_tool_index(g.TOOLS3) + """].trigger('do');

        setTimeout(function(){
            dt.trigger('change');
        },""" + str(g.DEBOUNCE_VAL) + """);
    """
)

clear_points_btn.on_click(clear_points_btn_callback)
clear_points_btn.callback = click_reset_tool

clear_everything_btn.on_click(clear_everything_btn_callback)
clear_everything_btn.callback = click_reset_tool

calibrate_btn.on_click(calibrate_btn_callback)
calibrate_btn.callback = click_reset_tool

save_btn.on_click(save_btn_callback)
save_btn.callback = CustomJS(
    args = dict(s=source_fit),
    code = """
        if(s.data['x'].length == 0) {
            alert('Nothing to save. Please, perform the calibration before attempting to save.');
        }
    """
)

export_btn.callback = CustomJS(
    args = dict(s=source),
    code = """
        var data = s.data;
        var dataLength = data['f'].length;

        if(dataLength > 0) {
            var filetext = 'force,voltage\\n';
            for (i=0; i < dataLength; i++) {
                var currRow = [
                    data['f'][i].toFixed(6).toString(),
                    data['v'][i].toString().concat('\\n')
                ];
                var joined = currRow.join();
                filetext = filetext.concat(joined);
            }

            var now      = new Date().toISOString().slice(0,-5).replace(/[:-]/g,'_');
            var filename = 'calibration_data__' + now + '.csv';
            var blob     = new Blob([filetext], { type: 'text/csv;charset = utf-8;' });

            //addresses IE
            if(navigator.msSaveBlob) {
                navigator.msSaveBlob(blob, filename);
            } else {
                var link              = document.createElement("a");
                link.href             = URL.createObjectURL(blob);
                link.download         = filename;
                link.target           = "_blank";
                link.style.visibility = 'hidden';
                link.dispatchEvent(new MouseEvent('click'));
            }
        } else {
            alert('No data points to export!');
        }
    """
)


##############################################################################
# Periodic streaming update call

def periodic_stream():
    global new_data

    if new_data:
        util.doc_next_tick(doc, util.stream_update, source=source, new_data=new_data, rollover=200)
        new_data = dict()


##############################################################################
# Bokeh doc loop

controls = widgetbox(
    device_slc,
    device_conn_btn,
    read_point_btn,
    calibrate_btn,
    save_btn,
    export_btn,
    clear_points_btn,
    clear_everything_btn,
    width = 180
)

doc.add_root(layout(
    children = [
        [plot, column(_div, checkbox)],
        [controls, data_table],
    ],
    sizing_mode = 'fixed',
))

doc.add_periodic_callback(periodic_stream, g.SERVER_PERIOD)
