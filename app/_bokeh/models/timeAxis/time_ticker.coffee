import {CompositeTicker} from "models/tickers/composite_ticker"
import {AdaptiveTicker} from "models/tickers/adaptive_ticker"

ONE_NANO   = 1e-9
ONE_MILLI  = 1e-3
ONE_SECOND = 1.0
ONE_MINUTE = 60.0 * ONE_SECOND
ONE_HOUR   = 60 * ONE_MINUTE


export class TimeTicker extends CompositeTicker
    type: 'TimeTicker'

    @override {
        num_minor_ticks: 4
        tickers: () -> [
            # Sub-seconds.
            new AdaptiveTicker({
                mantissas: [1, 2, 5],
                base: 10,
                min_interval: ONE_NANO,
                max_interval: 500 * ONE_MILLI,
                num_minor_ticks: 5
            }),

            # Seconds, minutes.
            new AdaptiveTicker({
                mantissas: [1, 2, 5, 10, 15, 20, 30],
                base: 60,
                min_interval: ONE_SECOND,
                max_interval: 30 * ONE_MINUTE,
                num_minor_ticks: 4
            }),

            # Hours.
            new AdaptiveTicker({
                mantissas: [1, 2, 4, 6, 8, 12],
                base: 24,
                min_interval: ONE_HOUR,
                max_interval: null,
                num_minor_ticks: 4
            })
        ]
    }
