"""Neon glow for the data in a plot (lines, markers, error bars, scatter, bars).

Each data artist gets a stack of wide, faint strokes in its own colour drawn
underneath it (matplotlib path effects), which reads as a soft halo. Nothing
is rasterised, so PDFs stay vector; grid, spines, ticks and text are left
alone. Matching legend entries glow too.

Typical use::

    import pretty_plot as pp
    pp.use('tron')
    line, = ax.plot(x, y, label='fit')
    sc = ax.scatter(x, y2)
    pp.glow()                         # everything in the current figure
    pp.glow(ax)                       # one axes
    pp.glow(line, strength=2)         # just this line, brighter
    pp.glow([line, sc])               # a chosen set of artists
    pp.glow(sc, points=y2 > 3)        # only some of the scatter points
    pp.glow(line, points=slice(20, 40))  # only a segment of the line
    pp.glow(sc, color='magenta')      # own glow colour (e.g. colormapped scatter)

or automatically for every plot::

    pp.use('cyber_punk', glow=True)   # or glow=1.5 (strength), glow={...}
    pp.glow(line, strength=0)         # ... but not this one

Meant for the dark themes. In ``paper`` mode it is skipped with a
:class:`GlowWarning` (journals / print don't want it) unless ``force=True``;
on a light background it is applied but warned about.
"""

import warnings

import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import Collection, LineCollection, PathCollection
from matplotlib.container import Container, ErrorbarContainer
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.offsetbox import DrawingArea, OffsetBox, TextArea
from matplotlib.patches import Patch

from . import theme

__all__ = ["glow", "GlowWarning"]

# Opacity of one halo layer at strength=1; layers stack, so the halo is
# ~40% opaque right next to the line and fades to ~6% at its outer edge.
_LAYER_ALPHA = 0.06

# Artists that ``glow(ax)`` / auto-glow light up. Patches (bars, ...) only glow
# when asked for explicitly: a glowing histogram is usually too much.
_AUTO_TYPES = (Line2D, LineCollection, PathCollection)
_GLOW_TYPES = (Line2D, Collection, Patch)


class GlowWarning(UserWarning):
    """Glow skipped (paper mode) or used where it won't look good."""


def _is_light(color):
    r, g, b = mpl.colors.to_rgb(color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5


def _errorbar_kinds(c):
    """``{id: kind}`` for the parts of errorbar container ``c``: ``'point'``
    for the data points (+ line through them), ``'bar'`` for whiskers + caps."""
    data_line, caplines, barlinecols = c.lines
    kinds = {id(a): "bar" for a in (*caplines, *barlinecols)}
    if data_line is not None:
        kinds[id(data_line)] = "point"
    return kinds


def _errorbar_parts(ax):
    """``{id: kind}`` for every errorbar part in ``ax`` (see above)."""
    kinds = {}
    for c in ax.containers:
        if isinstance(c, ErrorbarContainer):
            kinds.update(_errorbar_kinds(c))
    return kinds


def _multiplier(kind, markers, errorbars):
    return {"point": markers, "bar": errorbars}.get(kind, 1.0)


def _flatten(target, out):
    """Collect ``(artist, kind)`` pairs from ``target`` into ``out``; kind is
    ``'data'``, or ``'point'`` / ``'bar'`` for errorbar parts."""
    if target is None:
        target = plt.gcf()
    if isinstance(target, Figure):
        for ax in target.axes:
            _flatten(ax, out)
        return
    if isinstance(target, Axes):
        kinds = _errorbar_parts(target)
        for art in (*target.lines, *target.collections):
            if isinstance(art, _AUTO_TYPES):
                out.append((art, kinds.get(id(art), "data")))
        return
    if isinstance(target, ErrorbarContainer):
        data_line, caplines, barlinecols = target.lines
        if data_line is not None:
            out.append((data_line, "point"))
        out.extend((a, "bar") for a in (*caplines, *barlinecols))
        return
    if isinstance(target, _GLOW_TYPES):
        out.append((target, "data"))
        return
    if isinstance(target, (Container, list, tuple)):
        for t in target:
            _flatten(t, out)
        return
    raise TypeError(
        f"glow() can't light up a {type(target).__name__}; pass an Axes, "
        "Figure, artist (line / scatter / bar / error bars) or a list of them."
    )


def _color_of(art):
    """Single glow colour for ``art``, or ``None`` if it has several."""
    if isinstance(art, Line2D):
        if art.get_linestyle() in ("None", "none", "", " "):
            return art.get_markerfacecolor()
        return art.get_color()
    if isinstance(art, Patch):
        ec = art.get_edgecolor()
        return ec if art.get_linewidth() > 0 and ec[3] > 0 else art.get_facecolor()
    if isinstance(art, Collection):
        art.update_scalarmappable()  # colormapped -> real colours
    cols = (art.get_edgecolor() if isinstance(art, LineCollection)
            else art.get_facecolor())
    if len(cols) == 0:
        return None
    # A colormapped scatter has one colour per point: a single-colour halo
    # would be wrong, so leave it alone (pass color= to glow it anyway).
    if len({tuple(np.round(c[:3], 3)) for c in cols}) > 1:
        return None
    return cols[0]


def _linewidth_of(art):
    if isinstance(art, (Line2D, Patch)):
        return art.get_linewidth()
    lws = art.get_linewidth()
    return float(lws[0]) if len(lws) else 1.0


def _effects(color, lw, strength, size, layers):
    rgb = mpl.colors.to_rgb(color)
    alpha = min(1.0, _LAYER_ALPHA * strength)
    # Widest first, so narrower (denser) layers stack on top. Round ends, so
    # line ends and error-bar caps get a soft halo instead of a square block.
    return [pe.Stroke(linewidth=lw + size * i / layers, foreground=rgb, alpha=alpha,
                      capstyle="round", joinstyle="round")
            for i in range(layers, 0, -1)]


def _apply(art, strength, size, layers, color=None, halo_only=False):
    """Set the glow on one artist; ``strength <= 0`` removes it."""
    art._pp_glow = True  # also marks "leave alone" for auto-glow
    art._pp_glow_cfg = None
    if strength <= 0:
        art.set_path_effects([])
        return False
    color = color if color is not None else _color_of(art)
    if color is None:
        return False
    fx = _effects(color, _linewidth_of(art), strength, size, layers)
    art.set_path_effects(fx if halo_only else fx + [pe.Normal()])
    # Remembered so legend entries can get the same glow (own colour / width).
    art._pp_glow_cfg = (strength, size, layers, color)
    if art.figure is not None:
        art.figure._pp_glowing = True
    return True


def _subset(art, points):
    """A halo-only copy of some of ``art``'s points, drawn just beneath it."""
    ax = art.axes
    if isinstance(art, Line2D):
        sub = Line2D([], [])
        sub.update_from(art)
        sub.set_data(np.asarray(art.get_xdata())[points],
                     np.asarray(art.get_ydata())[points])
        sub.set_transform(art.get_transform())
        ax.add_line(sub)
    elif isinstance(art, PathCollection):
        art.update_scalarmappable()

        def pick(v):
            v = np.asarray(v)
            return v[points] if len(v) > 1 else v

        sub = PathCollection(
            art.get_paths(),
            sizes=pick(art.get_sizes()),
            offsets=np.asarray(art.get_offsets())[points],
            offset_transform=art.get_offset_transform(),
            facecolors=pick(art.get_facecolor()),
            edgecolors=pick(art.get_edgecolor()),
            linewidths=pick(art.get_linewidth()),
        )
        sub.set_transform(art.get_transform())
        ax.add_collection(sub, autolim=False)
    else:
        raise TypeError("points= works on a single line or scatter, "
                        f"not a {type(art).__name__}")
    sub.set_label("_nolegend_")
    sub.set_zorder(art.get_zorder() - 1e-3)
    sub._pp_glow = True
    return sub


def _legend_entries(leg):
    """``(label, [handle artists])`` for every entry of ``leg``.

    An entry is an ``HPacker(DrawingArea, TextArea)``; the DrawingArea holds
    every artist of the entry's symbol (an errorbar entry has marker, whisker
    and caps, not just the one artist in ``leg.legend_handles``).
    """
    stack = [leg._legend_handle_box]
    while stack:
        box = stack.pop()
        kids = box.get_children()
        if (len(kids) == 2 and isinstance(kids[0], DrawingArea)
                and isinstance(kids[1], TextArea)):
            yield kids[1].get_text(), kids[0].get_children()
        else:
            stack.extend(k for k in kids if isinstance(k, OffsetBox))


def _glow_sources(axes):
    """Legend label -> artist / container it stands for, in ``axes``."""
    out = {}
    for ax in axes:
        for art in (*ax.containers, *ax.lines, *ax.collections, *ax.patches):
            lab = art.get_label()
            if lab and not lab.startswith("_"):
                out.setdefault(lab, art)
    return out


def _cfg(art):
    return getattr(art, "_pp_glow_cfg", None)


def _set_handle(h, cfg):
    """Give legend artist ``h`` the glow ``cfg`` in its own colour / width."""
    if cfg is None:
        if getattr(h, "_pp_glow", False):
            h.set_path_effects([])
        return
    strength, size, layers, color = cfg
    color = _color_of(h) if color is None else color
    if color is None:
        return
    h.set_path_effects(_effects(color, _linewidth_of(h), strength, size, layers)
                       + [pe.Normal()])
    h._pp_glow = True


def _sync_legends(fig):
    """Make each legend entry glow like the artist(s) it stands for."""
    if fig is None or not getattr(fig, "_pp_glowing", False):
        return
    # An axes legend stands for its own axes (several panels may all have a
    # 'data' entry); a figure legend for every axes of the figure.
    legends = [(leg, fig.axes) for leg in fig.legends]
    legends += [(ax.get_legend(), [ax]) for ax in fig.axes if ax.get_legend()]
    for leg, axes in legends:
        sources = _glow_sources(axes)
        for label, handles in _legend_entries(leg):
            src = sources.get(label)
            if src is None:
                continue
            if isinstance(src, ErrorbarContainer):
                data_line, caplines, barlinecols = src.lines
                data_cfg = _cfg(data_line) if data_line is not None else None
                bars = [*barlinecols, *caplines]
                bar_cfg = next((_cfg(b) for b in bars if _cfg(b)), None)
                for h in handles:
                    is_bar = isinstance(h, LineCollection) or (
                        isinstance(h, Line2D) and h.get_marker() in ("|", "_")
                        and h.get_linestyle() in ("None", "none", "", " "))
                    _set_handle(h, bar_cfg if is_bar else data_cfg)
            else:
                parts = list(src) if isinstance(src, Container) else [src]
                cfg = next((_cfg(p) for p in parts if _cfg(p)), None)
                for h in handles:
                    _set_handle(h, cfg)


def glow(target=None, strength=1.0, size=None, layers=8, errorbars=1.0, markers=1.0,
         color=None, points=None, force=False):
    """Make the data in a plot -- or chosen parts of it -- glow.

    Call it after plotting. Safe to call again: a figure / axes call skips
    artists that already have a glow (so ``glow(line, strength=2)`` followed
    by ``glow()`` keeps that line brighter), while naming an artist directly
    always (re)sets its glow.

    Parameters
    ----------
    target : optional
        What to light up. Default: every line / scatter / error bar of the
        current figure. Accepts an ``Axes`` or ``Figure`` (all their lines,
        scatters and error bars), a single artist -- a ``Line2D`` from
        ``ax.plot``, the ``PathCollection`` from ``ax.scatter``, a patch --
        a container (``ax.errorbar`` / ``ax.bar`` result), or a list mixing
        any of these.
    strength : float
        Brightness of the halo (scales its opacity). ``1`` is a soft glow,
        ``2`` a strong one, ``0`` removes it (and keeps auto-glow off it).
    size : float, optional
        How far the halo reaches, as extra stroke width in points. Default
        ``4 x lines.linewidth`` of the active mode, so it scales with the
        mode (thicker halo in ``presenter``).
    layers : int
        Number of halo strokes; more = smoother fade, slower drawing.
    errorbars : float
        Strength multiplier for error-bar whiskers and caps (``1`` = same as
        the data, ``0.5`` = softer, ``0`` = no glow on error bars).
    markers : float
        Strength multiplier for the data points of error bars (the markers,
        and the line through them if any). With ``errorbars`` this sets points
        and bars independently: ``markers=0`` = only the bars glow,
        ``errorbars=0`` = only the points, ``markers=2, errorbars=0.5`` =
        bright points on softly glowing bars.
    color : color, optional
        Glow colour instead of each artist's own. Needed for a colormapped
        scatter (one colour per point), which is otherwise skipped.
    points : index array, boolean mask or slice, optional
        Glow only these points of a single line or scatter (``target`` must
        be one ``Line2D`` / ``PathCollection``). On a line this lights up
        the segment through those points.
    force : bool
        Apply even in ``paper`` mode.

    Returns
    -------
    list of Artist
        The artists that now glow (for ``points=``, the added halo artist).
    """
    if theme._ACTIVE_MODE == "paper" and not force:
        warnings.warn(
            "glow skipped in paper mode (journals / print don't want it); "
            "pass force=True to apply it anyway.",
            GlowWarning,
            stacklevel=2,
        )
        return []
    if size is None:
        size = 4 * mpl.rcParams["lines.linewidth"]

    found = []
    _flatten(target, found)

    if points is not None:
        arts = [a for a, _ in found]
        if isinstance(target, ErrorbarContainer):
            arts = [target.lines[0]]
        if len(arts) != 1:
            raise ValueError("points= needs a single line or scatter as target")
        found = [(_subset(arts[0], points), "data")]

    axes = {a.axes for a, _ in found if a.axes is not None}
    if isinstance(target, Axes):
        axes.add(target)
    if any(_is_light(ax.get_facecolor()) for ax in axes):
        warnings.warn(
            "glow on a light background looks blurry rather than neon; it "
            "is meant for the dark themes (dark, tron*, cyber_punk, matrix).",
            GlowWarning,
            stacklevel=2,
        )

    named = (points is not None or not isinstance(target, (type(None), Axes, Figure)))
    lit = []
    for art, kind in found:
        if not art.get_visible():
            continue
        if not named and getattr(art, "_pp_glow", False):
            continue
        if not getattr(art, "_pp_glow", False) and art.get_path_effects():
            continue  # the user set their own effects: don't clobber them
        s = strength * _multiplier(kind, markers, errorbars)
        if _apply(art, s, size, layers, color=color, halo_only=points is not None):
            lit.append(art)
    for fig in {a.figure for a, _ in found if a.figure is not None}:
        _sync_legends(fig)
    # Legends made (or remade) after this call are synced when drawn.
    _patch_axes_draw()
    return lit


def _patch_axes_draw():
    """At draw time: apply the auto-glow from ``use(..., glow=...)`` and make
    legend entries match their artists' glow. Idempotent."""
    if getattr(Axes.draw, "_pp_glow", False):
        return
    _orig_draw = Axes.draw

    def _draw(self, renderer):
        cfg = theme._GLOW
        if cfg:
            size = cfg["size"] if cfg["size"] is not None else 4 * mpl.rcParams["lines.linewidth"]
            kinds = _errorbar_parts(self)
            for art in (*self.lines, *self.collections):
                if (isinstance(art, _AUTO_TYPES) and art.get_visible()
                        and not getattr(art, "_pp_glow", False)
                        and not art.get_path_effects()):
                    s = cfg["strength"] * _multiplier(kinds.get(id(art)), cfg["markers"],
                                                      cfg["errorbars"])
                    _apply(art, s, size, cfg["layers"])
        _sync_legends(self.figure)
        _orig_draw(self, renderer)

    _draw._pp_glow = True
    Axes.draw = _draw
