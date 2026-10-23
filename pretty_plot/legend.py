"""Legend helpers: put a legend outside the plot, and flag oversized legends.

Typical use::

    import pretty_plot as pp
    pp.use('tron', mode='presenter')
    ...
    pp.legend()                    # inside, matplotlib's 'best' spot
    pp.legend(where='right')       # outside, right of the plot, centred
    pp.legend(where='top left')    # outside, above the plot, left-aligned
    pp.legend(where='bottom')      # outside, below, entries in one row
    pp.legend(where='right', pad=20)   # ... 20 pt further from the plot
    pp.legend(where='top', frame=True) # line around the legend box (any mode)
    pp.legend(frame_width=2.5)         # ... 2.5 pt thick (implies frame=True)

In ``presenter`` mode an oversized legend triggers a
:class:`LegendSizeWarning` when the figure is drawn (shown / saved). In any
mode, an outside legend (plus its ``pad``) that leaves the plot less than half
the figure width / height triggers a :class:`SquashedPlotWarning`.
"""

import warnings

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox

from . import theme

__all__ = ["legend", "LegendSizeWarning", "SquashedPlotWarning"]


class LegendSizeWarning(UserWarning):
    """A legend is too big for the active mode (see ``legend_warn``)."""


class SquashedPlotWarning(UserWarning):
    """An outside legend leaves too little room for the plot."""


# Below this fraction of the figure width (side legend) / height (top or
# bottom legend) left for the plot panels, warn. For reference, with no legend
# the plot gets ~85%, with a default 3-entry side legend ~60%.
_MIN_PLOT_FRAC = 0.5


# Side words -> canonical side; alignment words -> canonical alignment.
_SIDES = {
    "right": "right", "left": "left",
    "top": "top", "above": "top", "upper": "top",
    "bottom": "bottom", "below": "bottom", "lower": "bottom",
}
_ALIGN = {
    "top": "top", "upper": "top",
    "bottom": "bottom", "lower": "bottom",
    "left": "left", "right": "right",
    "middle": "middle", "center": "middle", "centre": "middle",
}
_ALIGN_OK = {
    "top": ("left", "middle", "right"),
    "bottom": ("left", "middle", "right"),
    "left": ("top", "middle", "bottom"),
    "right": ("top", "middle", "bottom"),
}
# Our words -> the words matplotlib's ``loc='outside ...'`` uses.
_MPL_WORD = {"top": "upper", "bottom": "lower", "middle": "center",
             "left": "left", "right": "right"}


def _outside_loc(where):
    """Turn e.g. ``'right'`` / ``'top left'`` into matplotlib's outside loc.

    The first word is the side of the figure the legend sits on (``right``,
    ``left``, ``top``, ``bottom``); the optional second word is where along
    that side (``top``/``middle``/``bottom`` for left/right, ``left``/
    ``middle``/``right`` for top/bottom). Default alignment is ``middle``.
    """
    words = str(where).strip().lower().replace("-", " ").replace("_", " ").split()
    if not words or words[0] not in _SIDES or len(words) > 2:
        raise ValueError(
            f"where must be 'inside' or '<side> [<align>]' with side in "
            f"right / left / top / bottom, got {where!r}"
        )
    side = _SIDES[words[0]]
    align = _ALIGN.get(words[1], words[1]) if len(words) == 2 else "middle"
    if align not in _ALIGN_OK[side]:
        raise ValueError(
            f"alignment for a legend on the {side} must be one of "
            f"{_ALIGN_OK[side]}, got {words[1]!r}"
        )
    if side in ("top", "bottom"):
        return f"outside {_MPL_WORD[side]} {_MPL_WORD[align]}", side
    return f"outside {side} {_MPL_WORD[align]}", side


def legend(where="inside", ax=None, fig=None, pad=None, frame=None,
           frame_width=None, **kwargs):
    """Draw a legend inside the axes, or outside the plot on a chosen side.

    Parameters
    ----------
    where : str
        ``'inside'`` (default): a normal ``ax.legend`` -- ``loc`` etc. go
        through ``kwargs``. Otherwise ``'<side> [<align>]'``, e.g.
        ``'right'``, ``'left top'``, ``'top'``, ``'bottom right'``: a figure
        legend outside the axes on that side (``above`` / ``below`` and
        ``center`` also accepted). Room is made automatically by switching the
        figure to the constrained layout engine if it has none.
    ax : Axes, optional
        Axes whose entries to show (inside) / whose figure to use (outside).
        Defaults to ``plt.gca()``.
    fig : Figure, optional
        Figure for an outside legend; defaults to ``ax.figure``. An outside
        legend collects the entries of **every** axes in the figure (duplicate
        labels shown once), so one shared legend serves a multi-panel figure.
    pad : float, optional
        Distance between plot and legend, in points (1 pt = 1/72 in).
        Outside: **extra** gap added to the layout's default spacing between
        the plot (incl. its tick / axis labels) and the legend; negative
        values pull the legend closer. Inside: gap between the legend and the
        axes edge (sets ``borderaxespad``). ``None`` keeps the default.
    frame : bool, optional
        ``True``: draw a line around the legend box, inside or outside.
        ``False``: no box. ``None`` (default): the mode's default (framed in
        ``regular`` / ``presenter``, frameless in ``paper``). Line colour is
        the theme's foreground unless you pass ``edgecolor=``.
    frame_width : float, optional
        Line width of the box (points). Defaults to the axes spine width
        (``axes.linewidth``), so the legend border matches the plot border.
        Giving a width turns the box on (also in ``paper`` mode) unless
        ``frame=False``; ``frame_width=0`` = no box.
    **kwargs
        Passed to ``Axes.legend`` / ``Figure.legend`` (``ncols``, ``title``,
        ``handles``/``labels``, ...). Outside on the top / bottom, ``ncols``
        defaults to all entries in one row.

    Returns
    -------
    matplotlib.legend.Legend
    """
    if frame is None and frame_width is not None:
        frame = frame_width > 0  # asking for a line width means "draw the box"
    if frame is not None:
        kwargs.setdefault("frameon", bool(frame))
    if str(where).strip().lower() == "inside":
        if pad is not None:
            size = kwargs.get("fontsize", plt.rcParams["legend.fontsize"])
            if isinstance(size, str):
                from matplotlib.font_manager import FontProperties
                size = FontProperties(size=size).get_size_in_points()
            kwargs.setdefault("borderaxespad", pad / size)
        return _style_frame((ax or plt.gca()).legend(**kwargs), frame_width)

    loc, side = _outside_loc(where)
    fig = fig or (ax or plt.gca()).figure
    handles = kwargs.pop("handles", None)
    labels = kwargs.pop("labels", None)
    if handles is None:
        seen = {}
        for a in fig.axes:
            for h, lab in zip(*a.get_legend_handles_labels()):
                seen.setdefault(lab, h)
        labels = labels or list(seen)
        handles = [seen[lab] for lab in labels]
    if side in ("top", "bottom"):
        kwargs.setdefault("ncols", max(len(handles), 1))
    # 'outside' locations only reserve space under the constrained engine.
    if fig.get_layout_engine() is None:
        fig.set_layout_engine("constrained")
    leg = fig.legend(handles, labels, loc=loc, **kwargs)
    leg._pp_side, leg._pp_pad = side, pad
    if pad:
        _pad_outside(leg, side, pad)
    return _style_frame(leg, frame_width)


def _style_frame(leg, frame_width):
    """Set the legend box line width (matplotlib has no rcParam for it)."""
    if leg.get_frame_on():
        lw = plt.rcParams["axes.linewidth"] if frame_width is None else frame_width
        leg.get_frame().set_linewidth(lw)
    return leg


def _pad_outside(leg, side, pad):
    """Grow ``leg``'s tight bbox by ``pad`` points on the side facing the plot.

    The constrained layout engine reserves "legend tight bbox + its own
    padding" at the figure edge for an outside legend, and the legend is drawn
    against the edge -- so the extra ``pad`` ends up as gap between legend and
    plot. Only the plot-facing side grows, so ``bbox_inches='tight'`` crops
    the same as before.
    """
    orig = leg.get_tightbbox

    def _padded(*args, **kwargs):
        bb = orig(*args, **kwargs)
        if bb is None:
            return bb
        d = pad * leg.figure.dpi / 72
        x0, y0, x1, y1 = bb.extents
        if side == "right":
            x0 -= d
        elif side == "left":
            x1 += d
        elif side == "top":
            y0 -= d
        else:
            y1 += d
        return Bbox.from_extents(x0, y0, x1, y1)

    leg.get_tightbbox = _padded


def _check_size(leg, renderer):
    """Warn (once per legend) if ``leg`` breaks the active mode's limits."""
    limits = theme._MODES.get(theme._ACTIVE_MODE, {}).get("legend_warn")
    if not limits or getattr(leg, "_pp_size_checked", False):
        return
    leg._pp_size_checked = True
    parent = leg.parent
    pbox = (parent.get_window_extent(renderer) if isinstance(parent, Axes)
            else parent.bbox)
    lbox = leg.get_window_extent(renderer)
    frac = (lbox.width * lbox.height) / max(pbox.width * pbox.height, 1)
    n = len(leg.texts)
    what = "axes" if isinstance(parent, Axes) else "figure"
    problems = []
    if frac > limits["max_area"]:
        problems.append(f"covers {frac:.0%} of the {what} "
                        f"(limit {limits['max_area']:.0%})")
    if n > limits["max_entries"]:
        problems.append(f"has {n} entries (limit {limits['max_entries']})")
    if problems:
        warnings.warn(
            f"legend {' and '.join(problems)} -- hard to read on a slide. "
            "Try fewer entries, ncols=2, a shorter title, or "
            "pretty_plot.legend(where='right').",
            LegendSizeWarning,
            stacklevel=2,
        )


def _check_squash(leg):
    """Warn (once per legend) if an outside legend squashes the plot."""
    side = getattr(leg, "_pp_side", None)
    if side is None or getattr(leg, "_pp_squash_checked", False):
        return
    leg._pp_squash_checked = True
    boxes = [a.get_position() for a in leg.figure.axes if a.get_visible()]
    if not boxes:
        return
    horizontal = side in ("left", "right")
    if horizontal:
        frac = max(b.x1 for b in boxes) - min(b.x0 for b in boxes)
    else:
        frac = max(b.y1 for b in boxes) - min(b.y0 for b in boxes)
    if frac >= _MIN_PLOT_FRAC:
        return
    dim = "width" if horizontal else "height"
    size = leg.figure.get_size_inches()[0 if horizontal else 1]
    pad = getattr(leg, "_pp_pad", None)
    hints = []
    if pad and pad > 0:
        hints.append(f"a smaller pad (now {pad:g} pt)")
    hints.append("where='top' / 'bottom'" if horizontal else "where='right'")
    hints += ["shorter labels", f"a larger figure {dim} (now {size:.2g} in)"]
    warnings.warn(
        f"outside legend squashes the plot: the plot gets only {frac:.0%} of "
        f"the figure {dim} (warning below {_MIN_PLOT_FRAC:.0%}). "
        f"Try {', '.join(hints)}.",
        SquashedPlotWarning,
        stacklevel=2,
    )


def _patch_legend_draw():
    """Hook the size check into ``Legend.draw``; idempotent."""
    if getattr(Legend.draw, "_pp_checked", False):
        return
    _orig_draw = Legend.draw

    def _draw(self, renderer):
        _orig_draw(self, renderer)
        if self.get_visible():
            _check_size(self, renderer)
            _check_squash(self)

    _draw._pp_checked = True
    Legend.draw = _draw
