import {LinearAxis, LinearAxisView} from "models/axes/linear_axis"
import {TimeTickFormatter} from "./time_tick_formatter"
import {TimeTicker} from "./time_ticker"

export class TimeAxisView extends LinearAxisView

export class TimeAxis extends LinearAxis
    default_view: TimeAxisView
    type: 'TimeAxis'

    @override {
        ticker:    () -> new TimeTicker()
        formatter: () -> new TimeTickFormatter()
    }
