# coding: utf-8

# Bokeh app to plot measures from the palmar grip electronic dynamometer
# that are save in the database.

# Bokeh
from bokeh.layouts import column
from bokeh.plotting import figure, curdoc
from bokeh.palettes import brewer
from bokeh.models import ColumnDataSource, CustomJS, Grid
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter

# Custom models
from timeAxis.timeAxis import TimeAxis
from customHover.customHover import CustomHover

# Others
import g
import re
import util
import requests


##############################################################################
# Init

# open a session to keep the local document in sync with server
doc = curdoc()

try:
    args      = doc.session_context.request.arguments
    g.TOKEN   = args.get('token')[0]
    g.CTRL_ID = re.sub("[\W]", "", g.TOKEN)[7:23]

    url = "{}get_measurement/{}/".format(g.BOKEH_HOST, g.TOKEN)
    req = requests.get(url)

    if g.BOKEH_DEV:
        print "req:", req, "\n"

    MEASURES = req.json()
    MEASURES['m_data'] = [{k:[float(v) for v in _list] for k,_list in _dict.items()} for _dict in MEASURES['m_data']]
except:
    exit()


##############################################################################
# Sources

source = ColumnDataSource(data=dict(
    f = MEASURES['m_data'][0]['force'],
    t = MEASURES['m_data'][0]['time']
))

source_table = ColumnDataSource(data=dict(
    m_datetime = MEASURES['m_date'],
    d_code     = MEASURES['d_code'],
    c_ang      = [_d['angular'] for _d in MEASURES['c_data']],
    c_lin      = [_d['linear'] for _d in MEASURES['c_data']],
    index      = range(len(MEASURES['id']))
))
source_table.selected['1d']['indices'] = [0]


##############################################################################
# Plot

plot = figure(
    x_axis_type=None,
    plot_height=350,
    plot_width=800,
    tools=g.TOOLS1,
    toolbar_location="above",
    toolbar_sticky=True,
    active_drag='xpan',
    active_tap=None,
    active_scroll='xwheel_zoom',
)
xaxis = TimeAxis()
plot.add_layout(xaxis, 'below')
plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
plot.x_range.min_interval = 2 * xaxis.ticker.tickers[0].min_interval

color = brewer['Paired'][4][-1]
line = plot.line(x='t', y='f', source=source, color=color)
circle = plot.circle(x='t', y='f', source=source, color=color)

plot.add_tools(CustomHover(
    tooltips = [
        ("force", "$~y{0.000}"),
        ("time", "$xaxis_f"),
    ],
    mode = 'vline',
    line_policy = "interp",
    renderers = [line],
))

plot.xaxis.axis_label = "time"
plot.yaxis.axis_label = "force (N)"

data_table = DataTable(
    source = source_table, width=800, height=327, editable=False,
    columns = [
        TableColumn(
            field = "d_code",
            title = "Device code",
        ),
        TableColumn(
            field = "m_datetime",
            title = "Measurement date",
        ),
        TableColumn(
            field = "c_ang",
            title = "Calibration's angular coef.",
            formatter = NumberFormatter(format="0.000")
        ),
        TableColumn(
            field = "c_lin",
            title = "Calibration's linear coef.",
            formatter = NumberFormatter(format="0.000")
        ),
    ]
)

def upd_plot_source(attr, old, new):
    old_ind = old['1d']['indices']
    new_ind = new['1d']['indices']

    if new_ind and new_ind != old_ind:
        source.data.update(
            f = MEASURES['m_data'][new_ind[0]]['force'],
            t = MEASURES['m_data'][new_ind[0]]['time']
        )

source_table.on_change('selected', upd_plot_source)
source_table.js_on_change('selected', CustomJS(
    args = dict(p=plot),
    code = """
        p.toolbar.tools[""" + util.reset_tool_index(g.TOOLS1) + """].trigger('do');
    """
))


##############################################################################
# Bokeh doc

doc.add_root(column(plot, data_table))
