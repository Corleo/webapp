from bokeh.model import Model
from bokeh.core.properties import Any


class VarModel(Model):
    """ Model to track a python global variable at both server and client
    side. Using this model a variable can be passed to others object's
    CustomJS callbacks as well as having defined it's own callback.

    Args:
        value (Any):
            A value for this variable of type Any().
    """
    __implementation__ = 'varModel.coffee'

    value = Any(default=None, help="A value for this variable of type Any().")
