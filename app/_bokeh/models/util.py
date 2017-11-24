import g
import json
import math
import functools


def doc_next_tick(doc, func, *args, **kwargs):
    """Schedule a function execution using Bokeh Tornado threads for the
    next Tornado loop.

    Args:
        + doc     : Bokeh application's curdoc().
        + func    : function's name.
        + *args   : function's arguments.
        + **kargs : function's key arguments.
    """

    doc.add_next_tick_callback(functools.partial(func, *args, **kwargs))


def stream_update(source, new_data, rollover=6000):
    """Source stream update function to stream new data to source object.

    Args:
        + source   : Bokeh's data source object.
        + new_data : new source data to be streamed to client's browser.
        + rollover : amount of data to be maintained in client's browser.
    """

    source.stream(new_data=new_data, rollover=rollover)


def calibre_x_list(_list, _num=4):
    """Create xaxis calibration list.

    Args:
        + _list : xaxis data source list.
        + _num  : quantity of elements to be created into the _list.

    Return:
        a list with points equally spaced by steps that are based on _num
        and a number power of 2 that is closer to the largest element in
        the _list.
    """

    _max = int(math.pow(2, math.ceil(math.log(max(_list), 2)))) + 1
    return range(0, _max, _max/_num)


def reset_tool_index(tools):
    """Find reset button index in 'tools' string list.

    Args:
        + tools: Bokeh' string list containing plot tools names.

    Return:
        an index of the reset button in this string list.
    """

    return str([zz.strip() for zz in tools.split(',')].index('reset'))


def conn_status_update(conn_status, value):
    """Update mosquitto's connection status with the device.

    Args:
        + conn_status: object containing the connection status.
        + value: connection status value.
    """

    conn_status.value = value


def device_control(client, command):
    """Publish a mosquitto topic with a command to control the device.

    Args:
        + client  : mosquitto client object.
        + command : command to control the device.
    """

    client.publish(
        topic=g.t_device_ctrl,
        payload=json.dumps(dict(ctrl_id=g.CTRL_ID, command=command)),
        qos=1,
        retain=False
    )


def config_new_topics(topic_type):
    """Define topics' name based on device ID.

    Args:
        + topic_type : type of topic subscription (measure or calibration).
    """

    _topics = []

    # # sub topics
    # t_period  = b"device/%s/period" % dev_id
    # t_control = b"device/%s/control" % dev_id

    # # pub topics
    # t_control_cb  = b"device/%s/control_cb" % dev_id
    # t_measurement = b"device/%s/measurement" % dev_id
    # t_calibration = b"device/%s/calibration" % dev_id

    # pub topics
    g.t_period = str("period/%s" % g.device_id)
    g.t_device_ctrl = str("devicectrl/%s" % g.device_id)
    _topics.append(g.t_period)
    _topics.append(g.t_device_ctrl)

    # sub topics
    g.t_device_ctrl_cb = str("devicectrlcb/%s" % g.device_id)
    _topics.append(g.t_device_ctrl_cb)

    if topic_type == 'measure':
        g.t_measure = str("measure/%s" % g.device_id)
        _topics.append(g.t_measure)

    elif topic_type == 'calibration':
        g.t_calibration = str(b"calibration/%s" % g.device_id)
        _topics.append(g.t_calibration)

    if g.BOKEH_DEV:
        print("\nSetting topics:")
        for topic in _topics:
            print(" * %s" % topic)


def add_subscription(client, topic_type):
    """Add subscription to new mosquitto topics.

    Args:
        + client     : mosquitto client object.
        + topic_type : type of topic subscription (measure or calibration).
    """

    if topic_type == 'measure':
        config_new_topics('measure')
        client.subscribe([(g.t_measure, 1), (g.t_device_ctrl_cb, 1)])

    elif topic_type == 'calibration':
        config_new_topics('calibration')
        client.subscribe([(g.t_calibration, 1), (g.t_device_ctrl_cb, 1)])


def esp_time_diff(end, start):
    """Circular time difference calculator for [-T_INTERVAL/2, T_INTERVAL/2 - 1]
    where T_INTERVAL is the maximum time interval:
        * 62 bits for micropython unix
        * 30 bits for micropython ESP
    """
    diff = end - start

    if diff < -(g.T_PERIOD):
        diff += g.T_INTERVAL
    elif diff >= (g.T_PERIOD):
        diff -= g.T_INTERVAL

    return diff
