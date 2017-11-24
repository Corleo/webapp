from tornado.ioloop import IOLoop

from bokeh.application import Application
from bokeh.application.handlers import ScriptHandler, FunctionHandler
from bokeh.server.server import Server

import os

MODELS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'models')


def _bokeh_init():
    io_loop = IOLoop.current()

    server = Server(
        {
            '/_measure':   Application(ScriptHandler(filename='{}/palmar_grip.py'.format(MODELS_PATH))),
            '/_calibre':   Application(ScriptHandler(filename='{}/calibration.py'.format(MODELS_PATH))),
            '/_plot'   :   Application(ScriptHandler(filename='{}/plot_measure.py'.format(MODELS_PATH))),
        },
        io_loop=io_loop,
        allow_websocket_origin=["localhost:5000"]
    )
    server.start()
    io_loop.start()


if __name__ == '__main__':
    _bokeh_init()
