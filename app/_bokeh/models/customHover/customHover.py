from bokeh.models import HoverTool

class CustomHover(HoverTool):
    """ HoverTool with tooltips using TimeTickFormatter based on TimeAxis
    resolution.
    """
    __implementation__ = 'custom_hover.coffee'
