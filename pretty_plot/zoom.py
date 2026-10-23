"""Zoomed-in inset with connecting lines between corners you choose.

Typical use::

    import pretty_plot as pp
    axins = pp.zoom_inset(ax, xlim=(0.7, 1.01), ylim=(0, 100))
    axins.hist(values, bins=bins, histtype='step')         # draw into the inset

    # which corners to join: rectangle corner -> inset corner
    pp.zoom_inset(ax, (0.7, 1), (0, 100), corners=['bottom left', 'top right'])  # default
    pp.zoom_inset(ax, (0.7, 1), (0, 100), corners=['top left', 'top right'])
    pp.zoom_inset(ax, (0.7, 1), (0, 100),
                  corners=['top left -> bottom left', 'top right -> bottom right'])
    pp.zoom_lines(axins, 'bottom right')                    # add one more line later

A single corner name joins the same corner of the rectangle and the inset;
``'top left -> bottom right'`` (or the tuple ``('top left', 'bottom right')``
inside the list) joins the rectangle's top left to the inset's bottom right. The
rectangle and the lines follow the inset's limits, so a later
``axins.set_xlim(...)`` moves them too.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch, Rectangle

__all__ = ["zoom_inset", "zoom_lines"]

# corner name -> (x, y) as fractions of the box
_CORNERS = {
    "bottom left": (0, 0), "bottom right": (1, 0),
    "top left": (0, 1), "top right": (1, 1),
}
_WORDS = {"lower": "bottom", "upper": "top", "b": "bottom", "t": "top",
          "l": "left", "r": "right"}
_SHORT = {"bl": "bottom left", "br": "bottom right",
          "tl": "top left", "tr": "top right",
          "ll": "bottom left", "lr": "bottom right",
          "ul": "top left", "ur": "top right"}


def _corner(name):
    """``'top left'`` / ``'upper-left'`` / ``'tl'`` / ``'left top'`` -> (fx, fy)."""
    key = str(name).strip().lower().replace("-", " ").replace("_", " ")
    key = _SHORT.get(key.replace(" ", ""), key)
    words = sorted((_WORDS.get(w, w) for w in key.split()),
                   key=lambda w: w not in ("top", "bottom"))
    key = " ".join(words)
    if key not in _CORNERS:
        raise ValueError(f"unknown corner {name!r}; use 'bottom left', "
                         "'bottom right', 'top left' or 'top right'")
    return _CORNERS[key]


def _pairs(corners):
    """One spec or a list of specs -> [((fx, fy) on rectangle, (fx, fy) on inset)].

    A spec is ``'top left'`` (same corner on both), ``'top left -> bottom
    right'`` or ``('top left', 'bottom right')`` (rectangle -> inset).
    """
    if isinstance(corners, str):
        corners = [corners]
    out = []
    for c in corners:
        if isinstance(c, str):
            a, _, b = c.partition("->")
            a, b = a, (b or a)
        else:
            a, b = c
        out.append((_corner(a), _corner(b)))
    return out


def _update(axins):
    """Move the rectangle and the line ends to the inset's current limits."""
    z = axins._pp_zoom
    (x0, x1), (y0, y1) = axins.get_xlim(), axins.get_ylim()
    z["rect"].set_bounds(x0, y0, x1 - x0, y1 - y0)
    for line, (fx, fy), _ in z["lines"]:
        line.xy1 = (x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))


def zoom_inset(ax, xlim, ylim, bounds=(0.41, 0.44, 0.45, 0.45),
               corners=("bottom left", "top right"), axins=None,
               color=None, lw=None, **kwargs):
    """Add an inset that zooms into ``xlim`` x ``ylim`` of ``ax``.

    Parameters
    ----------
    ax : Axes
        The main plot.
    xlim, ylim : (float, float)
        The region to zoom into, in data units of ``ax``.
    bounds : (x0, y0, width, height)
        Where the inset sits, in fractions (0 to 1) of ``ax``.
    corners : str or list of str / (str, str)
        Which corners to join, one line each. ``'top left'`` joins the
        top-left corner of the rectangle to the top-left corner of the inset;
        ``'top left -> bottom right'`` (or ``('top left', 'bottom right')``)
        joins the rectangle's top left to the inset's bottom right. Default: bottom left and top right.
        Names: ``'bottom left'``, ``'bottom right'``, ``'top left'``,
        ``'top right'`` (also ``'lower left'``, ``'upper right'``, ``'bl'``,
        ``'tr'``, ...). ``[]`` = rectangle only.
    axins : Axes, optional
        An existing inset to use instead of creating one.
    color, lw : optional
        Colour and width of the rectangle and lines; default the theme's
        axes edge colour and ``axes.linewidth``.
    **kwargs
        Passed to the lines and the rectangle (``linestyle``, ``alpha``, ...).

    Returns
    -------
    Axes
        The inset; draw your data into it. ``axins._pp_zoom['rect']`` and
        ``['lines']`` hold the artists.
    """
    if axins is None:
        axins = ax.inset_axes(bounds)
    axins.set_xlim(xlim)
    axins.set_ylim(ylim)
    style = {"edgecolor": color or plt.rcParams["axes.edgecolor"],
             "linewidth": plt.rcParams["axes.linewidth"] if lw is None else lw,
             **kwargs}
    rect = Rectangle((0, 0), 1, 1, fill=False, zorder=4.99, **style)
    ax.add_patch(rect)
    axins._pp_zoom = {"ax": ax, "rect": rect, "lines": [], "style": style}
    axins.callbacks.connect("xlim_changed", _update)
    axins.callbacks.connect("ylim_changed", _update)
    zoom_lines(axins, corners)
    return axins


def zoom_lines(axins, corners, **kwargs):
    """Add connecting lines to an inset made by :func:`zoom_inset`.

    ``corners`` as in :func:`zoom_inset`; ``kwargs`` override the style for
    these lines only. Returns the new lines.
    """
    z = axins._pp_zoom
    style = dict(z["style"])
    style["color"] = kwargs.pop("color", None) or style.pop("edgecolor")
    style.pop("edgecolor", None)
    style.update(kwargs)
    new = []
    for rect_c, ins_c in _pairs(corners):
        line = ConnectionPatch(xyA=(0, 0), coordsA=z["ax"].transData,
                               xyB=ins_c, coordsB=axins.transAxes,
                               axesA=z["ax"], axesB=axins,
                               zorder=4.99, **style)
        z["ax"].add_artist(line)
        z["lines"].append((line, rect_c, ins_c))
        new.append(line)
    _update(axins)
    return new
