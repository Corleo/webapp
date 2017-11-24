import {TickFormatter} from "models/formatters/tick_formatter"
import * as p from "core/properties"

_pad = (num, size=2) ->
    [i, j] = String(num).split "."
    i = "0" + i while i.length < size
    return if j then i + '.' + j else i

_formatter = (tick, resol, _formats) ->
    [seconds, sub_seconds] = (tick.toFixed 9).split('.')
    [milli, micro, nano] = sub_seconds.match /.{3}/g

    seconds = parseInt (Math.abs seconds)

    signal  = if tick < 0 then "-" else ""

    hour    = String(Math.floor seconds / 3600)
    min     = String(Math.floor (seconds % 3600) / 60)
    sec     = String(Math.floor seconds % 60)

    milli   = String(parseInt milli)
    micro   = String(parseInt micro)
    nano    = String(parseInt nano)

    # get minor non zero resolution
    if tick != 0
        resol = switch
            when resol in ["hours", "hourmin"] then (
                resol
            )
            when resol == "minutes" then (
                if min != "0"
                    resol
                else
                    "hours"
            )
            when resol == "minsec" then (
                if min != "0" or sec != "0"
                    resol
                else
                    "hours"
            )
            when resol == "seconds" then (
                if sec != "0"
                    resol
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "secmillisec" then (
                if sec != "0" or milli != "0"
                    resol
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "milliseconds" then (
                if milli != "0"
                    resol
                else if sec != "0"
                    "seconds"
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "millimicrosec" then (
                if milli != "0" or micro != "0"
                    resol
                else if sec != "0"
                    "seconds"
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "microseconds" then (
                if micro != "0"
                    resol
                else if milli != "0"
                    "milliseconds"
                else if sec != "0"
                    "seconds"
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "micronanosec" then (
                if micro != "0" or nano != "0"
                    resol
                else if milli != "0"
                    "milliseconds"
                else if sec != "0"
                    "seconds"
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )
            when resol == "nanoseconds" then (
                if nano != "0"
                    resol
                else if micro != "0"
                    "microseconds"
                else if milli != "0"
                    "milliseconds"
                else if sec != "0"
                    "seconds"
                else if min != "0"
                    "minutes"
                else
                    "hours"
            )

    unit = _formats[resol][0]

    # format tick with best resolution
    return switch
        when resol == "nanoseconds" then (
            signal + nano + unit
        )
        when resol == "micronanosec" then (
            signal + micro + '.' + (nano.match /.{1}/g)[0] + unit
        )
        when resol == "microseconds" then (
            signal + micro + unit
        )
        when resol == "millimicrosec" then (
            signal + milli + '.' + (micro.match /.{1}/g)[0] + unit
        )
        when resol == "milliseconds" then (
            signal + milli + unit
        )
        when resol == "secmillisec" then (
            signal + sec + '.' + (milli.match /.{1}/g)[0] + unit
        )
        when resol == "seconds" then (
            signal + sec + unit
        )
        when resol == "minsec" then (
            unit.replace(
                /(.*)%M(.*)%S(.*)/g,
                "\$1" + signal + min + "\$2" + _pad(sec) + "\$3"
            )
        )
        when resol == "minutes" then (
            unit.replace(
                /(.*)%M(.*)/g,
                "\$1" + signal + min + "\$2"
            )
        )
        when resol == "hourmin" then (
            unit.replace(
                /(.*)%H(.*)%M(.*)/g,
                "\$1" + signal + hour + "\$2" + _pad(min)  + "\$3"
            )
        )
        when resol == "hours" then (
            unit.replace(
                /(.*)%H(.*)/g,
                "\$1" + signal + hour + "\$2"
            )
        )

_get_resolution_str = (resolution, span) ->
    adjusted = resolution * 1.1
    return switch
        when adjusted < 1e-6    then (if span >= 1e-6   then "micronanosec"  else "nanoseconds" )
        when adjusted < 1e-3    then (if span >= 1e-3   then "millimicrosec" else "microseconds")
        when adjusted < 1.0     then (if span >= 1.0    then "secmillisec"   else "milliseconds")
        when adjusted < 60      then (if span >= 60     then "minsec"        else "seconds"     )
        when adjusted < 3600    then (if span >= 3600   then "hourmin"       else "minutes"     )
        else                                                 "hours"

_doFormat = (ticks, _formats, hover_tick=null) ->
    ticks_len = ticks.length
    if ticks_len == 0
        return []

    # computing ticks resolution
    span = Math.abs(ticks[ticks_len-1] - ticks[0])
    if ticks_len > 1
        r = span / (ticks_len - 1)
    else
        r = 0
    resol = _get_resolution_str(r, span)

    if hover_tick == null
        labels = ( _formatter(tick, resol, _formats) for tick in ticks )
    else
        resol_arr = [
            'nanoseconds',
            'micronanosec',
            'microseconds',
            'millimicrosec',
            'milliseconds',
            'secmillisec',
            'seconds',
            'minsec',
            'minutes',
            'hourmin',
            'hours']

        index = (resol_arr.indexOf resol)
        if index > 0
            index -= 1

        labels = ( _formatter(hover_tick, resol_arr[index], _formats) )

    # console.log " "
    # console.log "span: #{span}"
    # console.log "r: #{r}"
    # console.log "resol: #{resol}"
    # console.log "labels: [#{labels}]"
    # console.log "ticks: [#{ticks}]"

    return labels


export class TimeTickFormatter extends TickFormatter
    type: 'TimeTickFormatter'

    @define {
        nanoseconds:    [ p.Array, ['ns']               ]
        micronanosec:   [ p.Array, ['us']               ]
        microseconds:   [ p.Array, ['us']               ]
        millimicrosec:  [ p.Array, ['ms']               ]
        milliseconds:   [ p.Array, ['ms']               ]
        secmillisec:    [ p.Array, ['s']                ]
        seconds:        [ p.Array, ['s']                ]
        minsec:         [ p.Array, ['%Mm%Ss', ':%M:%S'] ]
        minutes:        [ p.Array, ['%Mm', ':%M']       ]
        hourmin:        [ p.Array, ['%Hh%Mm', '%H:%M']  ]
        hours:          [ p.Array, ['%Hh']              ]
    }

    initialize: (attrs, options) ->
        super(attrs, options)

        @_formats = {
            nanoseconds:    @nanoseconds
            micronanosec:   @micronanosec
            microseconds:   @microseconds
            millimicrosec:  @millimicrosec
            milliseconds:   @milliseconds
            secmillisec:    @secmillisec
            seconds:        @seconds
            minsec:         @minsec
            minutes:        @minutes
            hourmin:        @hourmin
            hours:          @hours
        }

    doFormat: (ticks, _formats=@_formats, hover_tick=null) ->
        return _doFormat(ticks, _formats, hover_tick)
