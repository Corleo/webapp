# coding: utf-8

# Bokeh app to stream data from a palmar grip electronic dynamometer.

# TODO:
#   * corrigir erro no modo vline do HoverTool para linhas horizontais
#   * callback JS pra desconectar do mosquitto
#       - quando a janela/aba do navegador for fechada
#       - quando o servidor for desligado
#       - quando a conexão estiver ociosa por mais de 10min

# Bokeh
from bokeh.layouts import widgetbox, row, column
from bokeh.plotting import figure, curdoc
from bokeh.palettes import brewer
from bokeh.models.widgets import Button, Select, Toggle, Slider
from bokeh.models import ColumnDataSource, CustomJS, Grid, Label

# Custom models
from timeAxis.timeAxis import TimeAxis
from varModel.varModel import VarModel
from customHover.customHover import CustomHover

# Mosquitto
import json
import paho.mqtt.client as mqtt

# Others
import g
import re
import util
import time
import requests


##############################################################################
# Init

# ''' FOR TESTING/DEBUG
if g.BOKEH_DEV:
    import os

    FILE_PATH = os.path.abspath('../webesp/data_dump.txt')
# '''

# open a session to keep the local document in sync with server
doc = curdoc()

t_raw_old = 0
t_old     = 0
new_data  = dict()

try:
    args      = doc.session_context.request.arguments
    g.TOKEN   = args.get('token')[0]
    g.CTRL_ID = re.sub("[\W]", "", g.TOKEN)[7:23]

    url = "{}get_calibrations/{}/".format(g.BOKEH_HOST, g.TOKEN)
    req = requests.get(url)

    if g.BOKEH_DEV:
        print "req.content:", req.content[:20], "\n"

    CALIBRATIONS = req.json()
except:
    exit()

g.device_id = CALIBRATIONS['d_code'][0]
g.d_idx     = CALIBRATIONS['d_code'].index(g.device_id)
g.c_ang     = float(CALIBRATIONS['c_data'][g.d_idx]['angular'])
g.c_lin     = float(CALIBRATIONS['c_data'][g.d_idx]['linear'])

##############################################################################
# Sources

source1   = ColumnDataSource(data=dict(f=[], t=[]))
source2   = ColumnDataSource(data=dict(f=[], t=[]))
data_freq = ColumnDataSource(data=dict(value=[]))

##############################################################################
# Mosquitto

conn_status = VarModel()
conn_status.value = False


def on_connect(client, userdata, flags, rc):
    if g.BOKEH_DEV:
        print("Connected with result code " + str(rc))
    if rc == 0:
        util.add_subscription(client, 'measure')


def on_disconnect(client, userdata, rc):
    if rc != 0:
        client.loop_stop()

        if g.BOKEH_DEV:
            print("Unexpected disconnection.")

    util.doc_next_tick(doc, util.conn_status_update, conn_status, False)


def on_subscribe(client, userdata, mid, granted_qos):
    if g.BOKEH_DEV:
        print("Subscribed with mid %s\n" % mid)


def on_unsubscribe(client, userdata, mid):
    if g.BOKEH_DEV:
        print("Unsubscribed with mid %s\n" % mid)


def on_message(client, userdata, msg):
    if msg.topic == g.t_device_ctrl_cb:
        on_message_device_cb(client, msg)

    elif msg.topic == g.t_measure:
        on_message_measure(client, msg)


def on_message_device_cb(client, msg):
    """Callback function that handles messages from 't_device_ctrl_cb' topic
    which is used as a callback topic to return the results of the control
    commands sent to the device.

    msg.payload = string with the result
    """
    device_cb_msg = str(msg.payload)
    if g.BOKEH_DEV:
        print(device_cb_msg)

    new_conn_status = None

    if device_cb_msg == 'successfully_connected':
        new_conn_status = True
        device_frequency(data_freq_sld.value)

        # ''' FOR TESTING/DEBUG
        if g.BOKEH_DEV:
            if os.path.isfile(FILE_PATH): os.remove(FILE_PATH)
        # '''

    elif device_cb_msg == 'already_connected':
        new_conn_status = True

    elif device_cb_msg == 'ok_to_unsubscribe':
        new_conn_status = False
        client.unsubscribe([g.t_measure, g.t_device_ctrl_cb])
        util.doc_next_tick(doc, util.add_subscription, client, 'measure')

    elif device_cb_msg in ['successfully_disconnected', 'no_control_allowed',
    'esp_init', 'esp_interrupted']:
        new_conn_status = False

        if not stream_data_btn.active:
            util.doc_next_tick(doc, disable_stream)

    if new_conn_status is not None:
        util.doc_next_tick(doc, util.conn_status_update, conn_status, new_conn_status)


def on_message_measure(client, msg):
    if stream_data_btn.active: return

    try:
        data = re.search("(\[[0-9.,\s]+\])\)$", msg.payload).group(1)
        data = json.loads(data)
    except Exception as e:
        if g.BOKEH_DEV:
            print("Exception with MQTT payload {}".format(e))
            print("MQTT payload: {}".format(msg.payload))
        return

    if data and isinstance(data, list) and len(data) % 2 == 0:
        global t_raw_old, t_old, new_data

        for _index, _value in enumerate(data):
            # data = [<time>,<force>,<time>,<force>,...]
            if _index % 2 == 1: continue

            try:
                _new_f = float(data[_index+1]) * g.c_ang
                _new_f = _new_f if not g.c_lin else _new_f + g.c_lin

                t_raw_new = data[_index]

                if t_raw_old == 0:
                    _new_t = 0
                else:
                    _new_t = t_old + t_raw_new - t_raw_old
                    # _new_t = t_old + util.esp_time_diff(t_raw_new, t_raw_old)

                t_raw_old = t_raw_new
                t_old = _new_t

                if not new_data: new_data = dict(f=[], t=[])
                new_data['f'].append(_new_f)
                new_data['t'].append(float(_new_t) * 1e-6)

                if g.BOKEH_DEV:
                    print('f: %7.3f | t: %7.3f | f_raw: %5d | t_raw: %11d' % (
                            new_data['f'][-1],
                            new_data['t'][-1],
                            data[_index+1],
                            data[_index],
                        )
                    )
            except Exception as e:
                if g.BOKEH_DEV:
                    print("Exception in processing measures: {}".format(e))
                    print("Data in Exception: {}".format(data))
                return

        # ''' FOR TESTING/DEBUG
        if g.BOKEH_DEV:
            with open(FILE_PATH, 'a') as dump_file:
                dump_file.write("{}\n".format(msg.payload))
        # '''


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

FOLLOW_INTERVAL  = 4.0  # sec (float)
TOOLBAR_LOCATION = "above"
TOOLBAR_STICKY   = True

#1
plot1 = figure(
    title            = "Streaming data at %.1f Hz" % (1e3 / g.DATA_FREQ_VAL),
    x_axis_type      = None,
    plot_height      = 120,
    plot_width       = 800,
    tools            = g.TOOLS1,
    toolbar_location = TOOLBAR_LOCATION,
    toolbar_sticky   = TOOLBAR_STICKY,
    active_drag      = 'xbox_select',
    active_tap       = None,
    active_scroll    = 'xwheel_zoom'
)
xaxis1 = TimeAxis()
plot1.add_layout(xaxis1, 'below')
plot1.add_layout(Grid(dimension=0, ticker=xaxis1.ticker))
plot1.x_range.update(
    follow           = 'end',
    follow_interval  = FOLLOW_INTERVAL,
    range_padding    = 0.0,
    min_interval     = 2 * xaxis1.ticker.tickers[0].min_interval
)

color   = brewer['Paired'][4][1]
line1   = plot1.line(x='t', y='f', source=source1, color=color)
circle1 = plot1.circle(x='t', y='f', source=source1, color=color)

plot1.add_tools(CustomHover(
    tooltips = [
        ("force", "$~y{0.000}"),
        ("time", "$xaxis_f"),
    ],
    mode        = 'vline',
    line_policy = "interp",
    renderers   = [line1],
))

#2
plot2 = figure(
    title            = "Selected data to save",
    x_axis_type      = None,
    plot_height      = 350,
    plot_width       = 800,
    tools            = g.TOOLS2,
    toolbar_location = TOOLBAR_LOCATION,
    toolbar_sticky   = TOOLBAR_STICKY,
    active_drag      = 'pan',
    active_tap       = None,
    active_scroll    = 'xwheel_zoom',
    logo             = None
)
xaxis2 = TimeAxis()
plot2.add_layout(xaxis2, 'below')
plot2.add_layout(Grid(dimension=0, ticker=xaxis2.ticker))
plot2.x_range.min_interval = 2 * xaxis2.ticker.tickers[0].min_interval

color   = brewer['Paired'][4][-1]
line2   = plot2.line(x='t', y='f', source=source2, color=color)
circle2 = plot2.circle(x='t', y='f', source=source2, color=color)

plot2.add_tools(CustomHover(
    tooltips = [
        ("force", "$~y{0.000}"),
        ("time", "$xaxis_f"),
    ],
    mode        = 'vline',
    line_policy = "interp",
    renderers   = [line2],
))

plot2.xaxis.axis_label = "time"
plot2.yaxis.axis_label = "force (N)"

plot2.add_layout(Label(
    name                  = "save_confirmation",
    x                     = 80,
    y                     = plot2.plot_height - 50,
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

# Linking plot2 with plot1 selection
source1.callback = CustomJS(
    args = dict(
        s2 = source2,
        p2 = plot2
    ),
    code = """
        var inds = cb_obj.selected['1d'].indices;
        var d1 = cb_obj.data;
        var d2 = s2.data;
        var d1_x0;

        d2['f'] = [];
        d2['t'] = [];

        inds.sort(function(a, b){return a-b});
        d1_x0 = d1['t'][inds[0]];
        for (i = 0; i < inds.length; i++) {
            d2['f'].push(d1['f'][inds[i]]);
            d2['t'].push(d1['t'][inds[i]] - d1_x0);
        };

        p2.toolbar.tools[""" + util.reset_tool_index(g.TOOLS2) + """].trigger('do');
        s2.trigger('change');
    """
)

##############################################################################
# Widgets

device_slc           = Select(title="Device ID:", value=g.device_id, options=CALIBRATIONS['d_code'])
device_conn_btn      = Toggle(label="Connect to device", button_type="success", active=True)
stream_data_btn      = Toggle(label="Start streaming", button_type="primary", active=True)
reset_stream_btn     = Button(label="Reset stream", button_type="danger")
save_selection_btn   = Button(label="Save selection", button_type="success")
export_selection_btn = Button(label="Export selection", button_type="primary")
data_freq_sld        = Slider(title="Period (ms)", value=g.DATA_FREQ_VAL, start=5, end=50, step=1, callback_policy="mouseup")


def device_frequency(period):
    client.publish(
        topic=g.t_period,
        payload=json.dumps(dict(ctrl_id=g.CTRL_ID, period=period)),
        qos=0,
        retain=False
    )

# Select: esp device selection by Id
def device_slc_callback(attr, old, new):
    g.device_id = new
    g.d_idx     = CALIBRATIONS['d_code'].index(g.device_id)
    g.c_ang     = float(CALIBRATIONS['c_data'][g.d_idx]['angular'])
    g.c_lin     = float(CALIBRATIONS['c_data'][g.d_idx]['linear'])

    if conn_status.value:
        disable_stream()
        util.doc_next_tick(doc, util.device_control, client, "unsub")
    else:
        client.unsubscribe([g.t_measure, g.t_device_ctrl_cb])
        util.doc_next_tick(doc, util.add_subscription, client, 'measure')

# Toggle button: esp device's connection control
def device_conn_btn_callback(toggle_val):
    if conn_status.value:
        command="disc"
        plot2.select_one('save_confirmation').update(text="")
    else:
        command="conn"

    util.device_control(client, command)

# Toggle button: stream data control
def stream_data_btn_callback(toggle_val):
    if conn_status.value:
        util.device_control(client, "toggle")

# Push button: reset stream
def reset_stream_btn_callback():
    global t_raw_old, new_data
    time.sleep(1e-3 * g.DEBOUNCE_VAL)
    t_raw_old = 0
    new_data = dict()
    source1.data = dict(f=[], t=[])

# Push button: save selected stream data
def save_selection_btn_callback():
    ds_ind = source1.selected['1d']['indices']
    if not ds_ind:
        if g.BOKEH_DEV:
            print "No data selected!", "\n"
        return False

    data_save = dict(
        d_id = CALIBRATIONS['d_id'][g.d_idx],
        c_id = CALIBRATIONS['c_id'][g.d_idx],
        f    = [],
        t    = [],
    )

    ds_t_0 = source1.data['t'][ds_ind[0]]
    for i in ds_ind:
        data_save['f'].append("%.6f" %  source1.data['f'][i])
        data_save['t'].append("%.6f" % (source1.data['t'][i] - ds_t_0))

    url = "http://localhost:5000/bokeh/save_measurement/%s/" % g.TOKEN
    req = requests.post(url, json=data_save)

    if req.content == "successfully_saved":
        _text = "Measurement successfully saved!"
    else:
        _text = "Saving error: refresh the browser and try again."
    plot2.select_one('save_confirmation').update(text=_text)

    if g.BOKEH_DEV:
        print "ds_ind:", ds_ind, "\n"
        print "data_save:", data_save, "\n"
        print "req.content:", req.content[:20], "\n"


# Slider: frequency of measurement acquisition
def data_freq_sld_callback(attr, old, new):
    new = data_freq.data['value'][0]

    disable_stream()
    if conn_status.value: device_frequency(new)


def data_freq_on_title(attr, old, new):
    plot1.title.text = "Streaming data at %.1f Hz" % (1e3 / new)


def clear_message(attr, old, new):
    plot2.select_one('save_confirmation').update(text="")


def disable_stream():
    stream_data_btn.update(
        active = True,
        label = "Start streaming",
        button_type = "primary",
    )


source1.on_change('selected', clear_message)

device_slc.on_change('value', device_slc_callback)
device_slc.js_on_change('value', CustomJS(
    args = dict(btn=reset_stream_btn),
    code = """
        document.getElementById('modelid_' + btn.id).click();
    """
))

device_conn_btn.on_click(device_conn_btn_callback)
device_conn_btn.callback = CustomJS(
    args = dict(btn=stream_data_btn),
    code = """
        if (!btn.active) {
            document.getElementById('modelid_' + btn.id).click();
        }
    """
)

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

stream_data_btn.on_click(stream_data_btn_callback)
stream_data_btn.callback = CustomJS(
    args = dict(
        s1 = source1,
        p1 = plot1,
        conn_status = conn_status
    ),
    code = """
        if(!conn_status.value && cb_obj.active) {
            console.log('This application must be connected to ESP device to start streaming data from it.');
            cb_obj.active = false;
            return;
        }

        if(cb_obj.active) {
            cb_obj.label = "Stop streaming";
            cb_obj.button_type = "warning";

            p1.toolbar.tools[""" + util.reset_tool_index(g.TOOLS1) + """].trigger('do');
        } else {
            cb_obj.label = "Start streaming";
            cb_obj.button_type = "primary";

            setTimeout(function(){
                s1.data['t'].push('nan');
                s1.data['f'].push('nan');
            },""" + str(g.DEBOUNCE_VAL) + """);
        }

        s1.trigger('change');
    """
)

reset_stream_btn.on_click(reset_stream_btn_callback)
reset_stream_btn.callback = CustomJS(
    args = dict(
        s1 = source1,
        p1 = plot1,
        p2 = plot2
    ),
    code = """
        s1.data['t'] = [];
        s1.data['f'] = [];
        s1.trigger('change');

        p1.toolbar.tools[""" + util.reset_tool_index(g.TOOLS1) + """].trigger('do');
        p2.toolbar.tools[""" + util.reset_tool_index(g.TOOLS2) + """].trigger('do');
    """
)

save_selection_btn.on_click(save_selection_btn_callback)
save_selection_btn.callback = CustomJS(
    args = dict(s2=source2),
    code = """
        var dataLength = s2.data['f'].length;

        if(dataLength == 0) {
            alert('No data selected!');
        }
    """
)

export_selection_btn.callback = CustomJS(
    args = dict(s2=source2),
    code = """
        var data = s2.data;
        var dataLength = data['f'].length;

        if(dataLength > 0) {
            var filetext = 'force,time\\n';
            for (i=0; i < dataLength; i++) {
                var currRow = [
                    data['f'][i].toFixed(6).toString(),
                    data['t'][i].toFixed(6).toString().concat('\\n')
                ];
                var joined = currRow.join();
                filetext = filetext.concat(joined);
            }

            var now      = new Date().toISOString().slice(0,-5).replace(/[:-]/g,'_');
            var filename = 'measurement_data__' + now + '.csv';
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
            alert('No data selected!');
        }
    """
)

data_freq.on_change('data', data_freq_sld_callback)
data_freq_sld.on_change('value', data_freq_on_title)
data_freq_sld.callback = CustomJS(
    args = dict(
        data_freq   = data_freq,
        conn_status = conn_status,
    ),
    code = """
        if(!conn_status.value) {
            console.log("This application must be connected to ESP device to change it's acquisition frequency.");
        }

        data_freq.data = { value: [cb_obj.value] }
    """
)


##############################################################################
# Periodic streaming update call

def periodic_stream():
    global new_data

    if new_data:
        util.doc_next_tick(doc, util.stream_update, source=source1, new_data=new_data)
        new_data = dict()


##############################################################################
# Bokeh doc loop

doc.add_root(row(
    widgetbox(
        device_slc,
        device_conn_btn,
        stream_data_btn,
        reset_stream_btn,
        save_selection_btn,
        export_selection_btn,
        data_freq_sld,
        width=180
    ),
    column(plot1, plot2)
))
doc.add_periodic_callback(periodic_stream, g.SERVER_PERIOD)
