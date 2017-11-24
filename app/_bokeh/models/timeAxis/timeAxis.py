from bokeh.core.properties import Override, List, String
from bokeh.models import CompositeTicker, AdaptiveTicker, TickFormatter, LinearAxis

# Globals
ONE_NANO   = 1e-9
ONE_MILLI  = 1e-3
ONE_SECOND = 1.0
ONE_MINUTE = 60.0 * ONE_SECOND
ONE_HOUR   = 60 * ONE_MINUTE


def _TIME_TICK_FORMATTER_HELP(field):
    return """
    Formats for displaying time values in the %s range.
    See the :class:`~bokeh.models.formatters.TimeTickFormatter` help for a list of all supported formats.
    """ % field


class TimeTicker(CompositeTicker):
    """ Generate nice ticks across different time scales.
    """
    __implementation__ = 'time_ticker.coffee'

    num_minor_ticks = Override(default=4)
    tickers = Override(default=lambda: [
        AdaptiveTicker(
            mantissas=[1, 2, 5],
            base=10,
            min_interval=ONE_NANO,
            max_interval=500 * ONE_MILLI,
            num_minor_ticks=5
        ),
        AdaptiveTicker(
            mantissas=[1, 2, 5, 10, 15, 20, 30],
            base=60,
            min_interval=ONE_SECOND,
            max_interval=30 * ONE_MINUTE,
            num_minor_ticks=4
        ),
        AdaptiveTicker(
            mantissas=[1, 2, 4, 6, 8, 12],
            base=24,
            min_interval=ONE_HOUR,
            max_interval=None,
            num_minor_ticks=4
        )
    ])


class TimeTickFormatter(TickFormatter):
    """ A ``TickFormatter`` for displaying time values nicely across a
    range of scales.
    ``TimeTickFormatter`` has the following properties for setting formats
    at different time scales:
    * ``nanoseconds``
    * ``micronanosec``
    * ``microseconds``
    * ``millimicrosec``
    * ``milliseconds``
    * ``secmillisec``
    * ``seconds``
    * ``minsec``
    * ``minutes``
    * ``hourmin``
    * ``hours``

    Each scale property can be set to format or list of formats to use for
    formatting time tick values that fall in in that "time scale".
    By default, only the first format string passed for each time scale
    will be used. By default, all leading zeros are stripped away from
    the formatted labels.
    """
    __implementation__ = 'time_tick_formatter.coffee'

    nanoseconds    = List(
                        String,
                        default=['ns'],
                        help=_TIME_TICK_FORMATTER_HELP("``nanoseconds``")
                    ).accepts(String, lambda fmt: [fmt])

    micronanosec   = List(
                        String,
                        default=['us'],
                        help=_TIME_TICK_FORMATTER_HELP("``micronanosec`` (for combined microseconds and nanoseconds)")
                    ).accepts(String, lambda fmt: [fmt])

    microseconds    = List(
                        String,
                        default=['us'],
                        help=_TIME_TICK_FORMATTER_HELP("``microseconds``")
                    ).accepts(String, lambda fmt: [fmt])

    millimicrosec   = List(
                        String,
                        default=['ms'],
                        help=_TIME_TICK_FORMATTER_HELP("``millimicrosec`` (for combined milliseconds and microseconds)")
                    ).accepts(String, lambda fmt: [fmt])

    milliseconds    = List(
                        String,
                        default=['ms'],
                        help=_TIME_TICK_FORMATTER_HELP("``milliseconds``")
                    ).accepts(String, lambda fmt: [fmt])

    secmillisec     = List(
                        String,
                        default=['s'],
                        help=_TIME_TICK_FORMATTER_HELP("``secmillisec`` (for combined seconds and milliseconds)")
                    ).accepts(String, lambda fmt: [fmt])

    seconds         = List(
                        String,
                        default=['s'],
                        help=_TIME_TICK_FORMATTER_HELP("``seconds``")
                    ).accepts(String, lambda fmt: [fmt])

    minsec          = List(
                        String,
                        default=['%Mm%Ss', ':%M:%S'],
                        help=_TIME_TICK_FORMATTER_HELP("``minsec`` (for combined minutes and seconds)")
                    ).accepts(String, lambda fmt: [fmt])

    minutes         = List(
                        String,
                        default=['%Mm', ':%M'],
                        help=_TIME_TICK_FORMATTER_HELP("``minutes``")
                    ).accepts(String, lambda fmt: [fmt])

    hourmin         = List(
                        String,
                        default=['%Hh%Mm', '%H:%M'],
                        help=_TIME_TICK_FORMATTER_HELP("``hourmin`` (for combined hours and minutes)")
                    ).accepts(String, lambda fmt: [fmt])

    hours           = List(
                        String,
                        default=['%Hh'],
                        help=_TIME_TICK_FORMATTER_HELP("``hours``")
                    ).accepts(String, lambda fmt: [fmt])


class TimeAxis(LinearAxis):
    """ An LinearAxis that picks nice numbers for tick locations on a
    time scale. Configured with a ``TimeTickFormatter`` by default.
    """
    __implementation__ = 'time_axis.coffee'

    ticker      = Override(default=lambda: TimeTicker())
    formatter   = Override(default=lambda: TimeTickFormatter())
