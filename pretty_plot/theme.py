"""High-visibility matplotlib themes you can flip with one call.

Ships seven palettes:

- ``light`` — white background, saturated-pastel colour cycle
- ``dark``  — black background, neon colour cycle
- ``tron``  — deep-blue background, cyan / amber "grid" glow
- ``tron_orange`` — dark-amber background, orange-led Tron cycle
- ``tron_red`` — dark-crimson background, red-led Tron cycle
- ``cyber_punk`` — near-black violet background, hot-pink / yellow / cyan
- ``matrix`` — pure-black background, monospace text, shades of green

Every theme also bumps every font (title, axis labels, ticks, legend) well
above the matplotlib default, renders text in a bold family, draws ``$...$``
maths in Computer Modern (the LaTeX look, no TeX install needed), and gives the
legend an opaque framed box so it stays readable over busy / dark plots. The
"playful" themes additionally switch on a faint colour-matched grid.

You may also (optionally) make every ``errorbar`` render as bare markers so
plotting code never has to pass ``fmt`` / ``capsize``.

Typical use at the top of a notebook::

    from pretty_plot import use
    use('dark')            # or 'light', 'tron', 'tron_orange', 'tron_red',
                           # 'cyber_punk', 'matrix'

or, if you want the two steps separately::

    from pretty_plot import apply_plot_theme, patch_errorbar
    apply_plot_theme('matrix', font_scale=1.2)
    patch_errorbar()

Independently of the theme, pick a *mode* for where the figure is going::

    use('dark')                       # mode='regular' -- day-to-day notebooks
    use('tron', mode='presenter')     # slides: big bold text, thick lines, 16:9
    pretty_plot.legend(where='right')  # legend outside the axes (any mode)
    use('light', mode='paper')        # journal column: 3.5 in, serif, 9-10 pt
    use('light', mode='paper', width='page')   # full text width, same text size

The body font is the current-version default unless you ask for another::

    use('dark')                       # default font stack
    use('dark', font='Georgia')       # your font, default stack as fallback

Introspection helpers::

    from pretty_plot import current_config, theme_config
    current_config()          # what rcParams are live right now (+ detected theme)
    theme_config('tron')      # what 'tron' *would* set, without applying it

Theme names are matched case-insensitively and a few common misspellings /
variants are accepted (``'cyberpunk'``, ``'the matrix'``, ...).
"""

import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

__all__ = [
    "NEON",
    "PASTEL",
    "TRON",
    "TRON_ORANGE",
    "TRON_RED",
    "CYBER_PUNK",
    "MATRIX",
    "THEMES",
    "DEFAULT_THEME",
    "DEFAULT_SANS",
    "DEFAULT_MONO",
    "DEFAULT_SERIF",
    "MODES",
    "DEFAULT_MODE",
    "apply_plot_theme",
    "patch_errorbar",
    "use",
    "theme_config",
    "current_config",
]

# --- colour cycles -----------------------------------------------------------
# Saturated neon on dark, muted-but-saturated pastel on light, plus three
# themed cycles for the "playful" palettes.
NEON = ["#08F7FE", "#FE53BB", "#F5D300", "#00FF9C", "#FF6E27", "#B388FF", "#FF3B3B"]
PASTEL = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#37B6C4", "#E377C2"]

# Tron: electric cyan + amber, the light-cycle look.
TRON = ["#00E8F8", "#FFA300", "#7DF9FF", "#37C0DC", "#EC7600", "#B7F7FF", "#2A6F97"]

# Tron, orange-dominant (the Clu / MCP side): amber leads, cyan as the foil.
TRON_ORANGE = ["#FFA300", "#FFD166", "#00E8F8", "#FF7A00", "#EC7600", "#7DF9FF", "#8A5A00"]

# Tron, red-dominant: hot warning-red leads, amber + cyan support.
TRON_RED = ["#FF2E3A", "#FF6E27", "#FFA300", "#00E8F8", "#FF8FA0", "#C41E27", "#7DF9FF"]

# Cyberpunk: hot pink, acid yellow, glitch cyan, neon violet / green.
CYBER_PUNK = ["#F3E600", "#00F0FF", "#FF2A6D", "#B967FF", "#05D9E8", "#FF6C11", "#39FF14"]

# Matrix: rain-of-code greens, brightest first.
MATRIX = ["#00FF41", "#39FF14", "#00D400", "#65FF00", "#00A86B", "#008F11", "#B6FF9E"]

DEFAULT_THEME = "dark"

# Bold-ish sans stack; falls back to DejaVu Sans (always present) if none found.
# These are the fonts the current version uses out of the box -- they stay the
# default whenever ``apply_plot_theme`` / ``use`` is called without ``font=``.
_SANS = ["Helvetica Neue", "Helvetica", "Arial", "TeX Gyre Heros", "DejaVu Sans"]
_MONO = ["JetBrains Mono", "Fira Code", "Menlo", "Consolas", "DejaVu Sans Mono"]
# Times-like serif for ``paper`` mode: matches the body text of A&A / ApJ /
# MNRAS. STIXGeneral ships with matplotlib, so this never falls through to
# DejaVu in practice; it also pairs with the ``stix`` mathtext fontset.
_SERIF = ["Times New Roman", "Times", "STIX Two Text", "STIXGeneral", "DejaVu Serif"]

# Public, read-only copies of the default stacks (matrix uses the mono one for
# its body text, ``paper`` mode the serif one, everything else the sans one).
DEFAULT_SANS = tuple(_SANS)
DEFAULT_MONO = tuple(_MONO)
DEFAULT_SERIF = tuple(_SERIF)

# rcParam that holds the stack for each ``font.family`` value -- a ``font=``
# override is put at the front of whichever one ends up active.
_STACKS = {"sans-serif": _SANS, "serif": _SERIF, "monospace": _MONO}

# theme name -> dict(style, fg, bg, cycle, [extras])
# ``style``  : matplotlib base style passed to ``plt.style.use``
# ``fg``/``bg``: foreground (text/spines/ticks) and background colours
# ``cycle``  : the ``axes.prop_cycle`` colour list
# ``extras`` : optional rcParams applied last, on top of everything else --
#              this is where a theme turns the grid on, swaps the font, etc.
_THEMES = {
    "light": {
        "style": "default",
        "fg": "#1A1A1A",
        "bg": "#FFFFFF",
        "cycle": PASTEL,
    },
    "dark": {
        "style": "dark_background",
        "fg": "#EAEAEA",
        "bg": "#0E0E0E",
        "cycle": NEON,
    },
    "tron": {
        "style": "dark_background",
        "fg": "#CDECF7",
        "bg": "#0A1721",
        "cycle": TRON,
        "extras": {
            "axes.edgecolor": "#2E6E8E",
            "axes.grid": True,
            "grid.color": "#12384A",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.7,
            "lines.linewidth": 2.0,
            "legend.edgecolor": "#00E8F8",
        },
    },
    "tron_orange": {
        "style": "dark_background",
        "fg": "#F7E4C6",
        "bg": "#1A1205",
        "cycle": TRON_ORANGE,
        "extras": {
            "axes.edgecolor": "#B5701A",
            "axes.grid": True,
            "grid.color": "#3D2A0C",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.7,
            "lines.linewidth": 2.0,
            "legend.edgecolor": "#FFA300",
        },
    },
    "tron_red": {
        "style": "dark_background",
        "fg": "#F7D6D9",
        "bg": "#1A0708",
        "cycle": TRON_RED,
        "extras": {
            "axes.edgecolor": "#B5323A",
            "axes.grid": True,
            "grid.color": "#3D1114",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.7,
            "lines.linewidth": 2.0,
            "legend.edgecolor": "#FF2E3A",
        },
    },
    "cyber_punk": {
        "style": "dark_background",
        "fg": "#F2ECFF",
        "bg": "#120421",
        "cycle": CYBER_PUNK,
        "extras": {
            "axes.edgecolor": "#FF2A6D",
            "axes.grid": True,
            "grid.color": "#2C1650",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.6,
            "lines.linewidth": 2.0,
            "legend.edgecolor": "#05D9E8",
        },
    },
    "matrix": {
        "style": "dark_background",
        "fg": "#00FF41",
        "bg": "#000000",
        "cycle": MATRIX,
        "extras": {
            "font.family": "monospace",
            "mathtext.fontset": "dejavusans",
            "axes.edgecolor": "#00B22C",
            "axes.grid": True,
            "grid.color": "#0A2A0A",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.8,
            "lines.linewidth": 1.8,
            "text.color": "#00FF41",
            "axes.labelcolor": "#00FF41",
            "axes.titlecolor": "#66FF8F",
            "xtick.color": "#00C233",
            "ytick.color": "#00C233",
            "legend.edgecolor": "#00FF41",
        },
    },
}

# Public read-only view of the available theme names.
THEMES = tuple(_THEMES)

# Accepted misspellings / variants -> canonical name.
_ALIASES = {
    "cyberpunk": "cyber_punk",
    "cyber-punk": "cyber_punk",
    "cyber punk": "cyber_punk",
    "cyberpunck": "cyber_punk",
    "the_matrix": "matrix",
    "the matrix": "matrix",
    "matrix_theme": "matrix",
    "tron_legacy": "tron",
    "tron_blue": "tron",
    "tronred": "tron_red",
    "redtron": "tron_red",
    "red_tron": "tron_red",
    "tronorange": "tron_orange",
    "orangetron": "tron_orange",
    "orange_tron": "tron_orange",
}

# Font sizes at font_scale=1.0 (matplotlib defaults, for reference: 10 / 12 /
# 10 / 10 / large). Every value is multiplied by font_scale in apply_plot_theme.
_BASE_SIZES = {
    "font.size": 13,
    "axes.titlesize": 17,
    "axes.labelsize": 15,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 13,
    "legend.title_fontsize": 13,
    "figure.titlesize": 18,
}

# Output modes -- orthogonal to the theme. The theme picks colours; the mode
# picks sizes, weights and output settings for where the figure will end up.
# ``sizes`` replaces ``_BASE_SIZES`` (still multiplied by font_scale) and ``rc``
# is layered *after* the theme's extras, so a mode wins on line widths etc.
_MODES = {
    # Day-to-day notebook work: exactly what earlier versions did.
    "regular": {"sizes": _BASE_SIZES, "rc": {}},
    # Slides / talks: readable from the back of the room. Big bold text, thick
    # lines and spines, larger markers, 16:9 figure. The figure is ~60% of a
    # 13.33 in wide 16:9 slide, so it goes in at close to 1:1 and the
    # text-to-figure ratio (~2.5 pt per inch of width) matches ``paper``.
    # ``legend_warn``: warn at draw time when a legend covers more than
    # ``max_area`` of its axes (or figure) or has more than ``max_entries``.
    "presenter": {
        "sizes": {
            "font.size": 20,
            "axes.titlesize": 24,
            "axes.labelsize": 22,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "legend.fontsize": 18,
            "legend.title_fontsize": 18,
            "figure.titlesize": 26,
        },
        "legend_warn": {"max_area": 0.25, "max_entries": 6},
        "rc": {
            "figure.figsize": (8.0, 4.5),
            "font.weight": "bold",
            "lines.linewidth": 2.8,
            "lines.markersize": 9,
            "errorbar.capsize": 5,
            "axes.linewidth": 2.0,
            "xtick.major.width": 1.8,
            "ytick.major.width": 1.8,
            "xtick.major.size": 8,
            "ytick.major.size": 8,
            "xtick.major.pad": 6,
            "ytick.major.pad": 6,
            "axes.titlepad": 14,
            "axes.labelpad": 8,
            "legend.handlelength": 2.2,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        },
    },
    # Journal figures. Designed at the printed size -- a single column
    # (~3.5 in) with 9-10 pt text, i.e. body-text size -- then drawn ``scale``
    # times bigger (figure, fonts, lines, ticks alike): the file is a 7 in
    # figure with 20 pt text that LaTeX shrinks back with
    # ``\includegraphics[width=\columnwidth]``, giving exact 10 pt text and
    # twice the pixel detail. Serif + STIX maths to match the page, normal
    # weight, thin lines, inward ticks on all four sides with minor ticks (the
    # astro convention), frameless legend, vector-friendly export with
    # embedded TrueType fonts (what journals ask for).
    "paper": {
        "scale": 2.0,
        "sizes": {
            "font.size": 10,
            "axes.titlesize": 10,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "legend.title_fontsize": 9,
            "figure.titlesize": 11,
        },
        "rc": {
            "figure.figsize": (3.5, 2.6),
            "font.family": "serif",
            "mathtext.fontset": "stix",
            "font.weight": "normal",
            "axes.titleweight": "normal",
            "axes.labelweight": "normal",
            "figure.titleweight": "normal",
            "lines.linewidth": 1.1,
            "lines.markersize": 3.5,
            "errorbar.capsize": 2,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.minor.width": 0.6,
            "ytick.minor.width": 0.6,
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "xtick.minor.size": 2,
            "ytick.minor.size": 2,
            "axes.titlepad": 4,
            "axes.labelpad": 3,
            "grid.linewidth": 0.5,
            "legend.frameon": False,
            "legend.fancybox": False,   # square corners if frame=True
            "legend.borderpad": 0.3,
            "legend.handlelength": 1.5,
            # Notebook preview: 200 dpi at the printed size, i.e. 100 dpi once
            # ``scale`` (x2) has been applied -> ~700 px wide. Saved files:
            # PDF (vector, never blurry) when no extension is given; PNG
            # fallback at 600 dpi of the (2x) file = 1200 dpi when printed.
            "figure.dpi": 200,
            "savefig.format": "pdf",
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        },
    },
}

# Named figure widths (inches) for ``width=``: A&A / ApJ / MNRAS one column
# is 3.3-3.5 in, full text width 6.9-7.1 in.
_WIDTHS = {
    "column": 3.5, "single": 3.5,
    "page": 7.1, "double": 7.1, "full": 7.1, "textwidth": 7.1,
}

# Size-like rcParams (points) that ``scale`` multiplies along with the figure
# size and the font sizes, so a scaled figure looks the same, just bigger.
_SCALED_KEYS = (
    "lines.linewidth", "lines.markersize", "lines.markeredgewidth",
    "errorbar.capsize", "axes.linewidth", "patch.linewidth", "grid.linewidth",
    "hatch.linewidth", "axes.titlepad", "axes.labelpad",
    "xtick.major.width", "ytick.major.width", "xtick.minor.width", "ytick.minor.width",
    "xtick.major.size", "ytick.major.size", "xtick.minor.size", "ytick.minor.size",
    "xtick.major.pad", "ytick.major.pad", "xtick.minor.pad", "ytick.minor.pad",
    "savefig.pad_inches",
)
# Font-size rcParams (scaled too; string sizes like 'large' follow font.size).
_FONT_KEYS = tuple(_BASE_SIZES)

# ``resolution=`` presets: dpi of saved raster files (PNG / JPG, and images
# inside a PDF). Vector output (PDF / SVG) is sharp at any size regardless.
RESOLUTIONS = {"low": 100, "medium": 300, "high": 600, "very_high": 1200}
_RESOLUTION_ALIASES = {
    "median": "medium", "med": "medium", "mid": "medium", "normal": "medium",
    "very high": "very_high", "veryhigh": "very_high", "very-high": "very_high",
    "vhigh": "very_high", "ultra": "very_high", "max": "very_high",
    "draft": "low", "lo": "low", "hi": "high",
}


def _resolve_resolution(resolution):
    """Preset name or number -> savefig dpi."""
    if isinstance(resolution, (int, float)) and not isinstance(resolution, bool):
        if resolution <= 0:
            raise ValueError(f"resolution must be > 0, got {resolution!r}")
        return resolution
    key = str(resolution).strip().lower().replace("_", " ")
    key = _RESOLUTION_ALIASES.get(key, key).replace(" ", "_")
    if key not in RESOLUTIONS:
        raise ValueError(f"unknown resolution {resolution!r}; use one of "
                         f"{list(RESOLUTIONS)} (or 'median') or a dpi number")
    return RESOLUTIONS[key]


# Mode set by the last ``apply_plot_theme`` call (``None`` before any). The
# legend size check reads this rather than guessing from rcParams, so a hand
# tweak after ``use(..., mode='presenter')`` doesn't switch the check off.
_ACTIVE_MODE = None

# Auto-glow settings from the last ``apply_plot_theme(glow=...)`` (``None`` =
# off); read by the ``Axes.draw`` hook in ``glow.py``.
_GLOW = None

# Public read-only view of the available mode names.
MODES = tuple(_MODES)
DEFAULT_MODE = "regular"

_MODE_ALIASES = {
    "default": "regular",
    "normal": "regular",
    "day": "regular",
    "everyday": "regular",
    "notebook": "regular",
    "presentation": "presenter",
    "present": "presenter",
    "slides": "presenter",
    "slide": "presenter",
    "talk": "presenter",
    "publication": "paper",
    "print": "paper",
    "journal": "paper",
    "article": "paper",
}


def _resolve(theme):
    """Map a user-supplied theme name to a canonical key in ``_THEMES``.

    Case-insensitive, and tolerant of ``-``/space vs ``_`` plus the handful of
    misspellings in ``_ALIASES``.
    """
    raw = str(theme).strip().lower()
    key = _ALIASES.get(raw, raw.replace("-", "_").replace(" ", "_"))
    key = _ALIASES.get(key, key)
    if key not in _THEMES:
        raise ValueError(
            f"theme must be one of {sorted(_THEMES)} (aliases also accepted: "
            f"{sorted(_ALIASES)}), got {theme!r}"
        )
    return key


def _resolve_mode(mode):
    """Map a user-supplied mode name to a canonical key in ``_MODES``."""
    raw = str(mode).strip().lower().replace("-", "_").replace(" ", "_")
    key = _MODE_ALIASES.get(raw, raw)
    if key not in _MODES:
        raise ValueError(
            f"mode must be one of {sorted(_MODES)} (aliases also accepted: "
            f"{sorted(_MODE_ALIASES)}), got {mode!r}"
        )
    return key


def _resolve_width(width):
    """Figure width in inches from a number or a name in ``_WIDTHS``."""
    if isinstance(width, str):
        key = width.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        key = {"singlecolumn": "single", "doublecolumn": "double"}.get(key, key)
        if key not in _WIDTHS:
            raise ValueError(f"width must be inches or one of {sorted(_WIDTHS)}, got {width!r}")
        return _WIDTHS[key]
    return float(width)


def _with_font(font, default_stack):
    """Put ``font`` at the front of ``default_stack`` (or return it unchanged).

    ``font`` may be ``None`` (keep the default stack -- what the current version
    ships), a single family name, or an iterable of family names in priority
    order. The default stack's entries are always kept *after* the caller's
    choice as a fallback, so text still renders if the requested font is not
    installed.
    """
    if font is None:
        return list(default_stack)
    chosen = [font] if isinstance(font, str) else list(font)
    return chosen + [f for f in default_stack if f not in chosen]


def theme_config(theme=DEFAULT_THEME, font_scale=1.0, usetex=False, font=None,
                 mode=DEFAULT_MODE, width=None, scale=None, resolution=None):
    """Build the rcParams for a theme and return them -- **without applying**.

    This is the single source of truth for what a theme looks like;
    :func:`apply_plot_theme` is just ``theme_config`` + ``rcParams.update``.
    Use it to preview / diff a theme, or to grab the "suggested configuration"
    for one theme and tweak it yourself.

    The returned ``dict`` is plain rcParam name -> value, with one extra
    non-rcParam entry:

    ``"style"``
        name of the matplotlib base style (:func:`matplotlib.style.use`) that
        :func:`apply_plot_theme` selects *before* applying everything else.
        Pop it before feeding the dict to ``matplotlib.rcParams.update``.

    Parameters
    ----------
    theme : {'light', 'dark', 'tron', 'tron_orange', 'tron_red', 'cyber_punk', 'matrix'}
        Which theme. Matched case-insensitively; common variants accepted.
    font_scale : float
        Multiplies every font size (see ``_BASE_SIZES``).
    usetex : bool
        Sets ``text.usetex`` (needs a real LaTeX install on PATH).
    font : str or list of str, optional
        Body font. ``None`` (default) keeps the stack the current version uses
        (:data:`DEFAULT_SANS`; :data:`DEFAULT_MONO` for ``matrix``;
        :data:`DEFAULT_SERIF` in ``paper`` mode). Give a family name (or a
        priority list) to override it; the default stack is still appended as
        a fallback.
    mode : {'regular', 'presenter', 'paper'}
        Where the figure is going. ``'regular'`` (default) is the day-to-day
        notebook look; ``'presenter'`` makes everything bigger and bolder for
        slides; ``'paper'`` sizes text for a single journal column, in serif.
        Independent of ``theme``.
    width : float or {'column', 'page'}, optional
        Width the figure is **printed / shown** at, in inches or by name
        (``'column'`` = 3.5 in, ``'page'`` = 7.1 in; ``'single'`` /
        ``'double'`` also work). The mode's aspect ratio is kept and font
        sizes are **not** changed. The file itself is ``width x scale`` wide.
        ``None`` keeps the mode's default.
    scale : float, optional
        Draw everything -- figure size, fonts, line widths, markers, ticks,
        paddings -- this many times bigger, so the figure looks identical,
        just larger (more detail when shrunk back in LaTeX / on a slide).
        ``None`` = the mode's default: ``2`` in ``paper`` (include with
        ``\\includegraphics[width=\\columnwidth]`` / ``[width=\\textwidth]``
        to get the designed 10 pt text), ``1`` otherwise. ``scale=1`` in
        ``paper`` gives a figure meant to be included at natural size.
    resolution : {'low', 'medium', 'high', 'very_high'} or float, optional
        dpi of saved raster files (``savefig.dpi``): ``'low'`` = 100,
        ``'medium'`` (or ``'median'``) = 300, ``'high'`` = 600,
        ``'very_high'`` = 1200, or a number. Matters for PNG / JPG (and
        images / ``rasterized=True`` parts inside a PDF); PDF / SVG lines
        and text are vector and sharp at any size anyway. ``None`` = the
        mode's default (600 in ``paper``, 200 in ``presenter``).
    """
    spec = _THEMES[_resolve(theme)]
    style, fg, bg, cycle = spec["style"], spec["fg"], spec["bg"], spec["cycle"]
    extras = spec.get("extras", {})
    mode_spec = _MODES[_resolve_mode(mode)]

    rc = {
        # --- colours -------------------------------------------------------
        "figure.facecolor": bg,
        "axes.facecolor": bg,
        "savefig.facecolor": bg,
        "text.color": fg,
        "axes.labelcolor": fg,
        "axes.titlecolor": fg,
        "axes.edgecolor": fg,
        "xtick.color": fg,
        "ytick.color": fg,
        "axes.grid": False,
        "axes.prop_cycle": mpl.cycler(color=list(cycle)),
        # --- markers / lines ---------------------------------------------
        "errorbar.capsize": 3,
        "lines.markersize": 5,
        "axes.linewidth": 1.2,
        "xtick.major.width": 1.1,
        "ytick.major.width": 1.1,
        "xtick.major.size": 5,
        "ytick.major.size": 5,
        # --- fonts: bold sans body, Computer Modern maths ---------------
        "font.family": "sans-serif",
        "font.sans-serif": list(_SANS),
        "font.serif": list(_SERIF),
        "font.monospace": list(_MONO),
        "font.weight": "medium",
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
        "figure.titleweight": "bold",
        "axes.titlepad": 10,
        "axes.labelpad": 6,
        "mathtext.fontset": "cm",
        "text.usetex": bool(usetex),
        # --- legend: opaque framed box so it reads over busy plots ------
        "legend.frameon": True,
        "legend.framealpha": 0.92,
        "legend.facecolor": bg,
        "legend.edgecolor": fg,
        "legend.fancybox": True,
        "legend.borderpad": 0.6,
        "legend.labelspacing": 0.5,
        "legend.handlelength": 1.8,
    }
    rc.update({k: v * font_scale for k, v in mode_spec["sizes"].items()})
    # Per-theme overrides (grid, font family, accent spines, ...), then the
    # mode's sizing / output settings on top.
    rc.update(extras)
    rc.update(mode_spec["rc"])
    if width is not None:
        w0, h0 = rc.get("figure.figsize", mpl.rcParamsDefault["figure.figsize"])
        w = _resolve_width(width)
        rc["figure.figsize"] = (w, w * h0 / w0)

    k = mode_spec.get("scale", 1.0) if scale is None else float(scale)
    if k <= 0:
        raise ValueError(f"scale must be > 0, got {scale!r}")
    if k != 1:
        w, h = rc.get("figure.figsize", mpl.rcParamsDefault["figure.figsize"])
        rc["figure.figsize"] = (w * k, h * k)
        for key in (*_FONT_KEYS, *_SCALED_KEYS):
            v = rc.get(key, mpl.rcParamsDefault[key])
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                rc[key] = v * k
        # Same on-screen size in the notebook as the unscaled figure.
        rc["figure.dpi"] = rc.get("figure.dpi", mpl.rcParamsDefault["figure.dpi"]) / k
    if resolution is not None:
        rc["savefig.dpi"] = _resolve_resolution(resolution)

    # A caller-supplied ``font`` goes to the front of whichever stack ends up
    # active (sans by default, mono for ``matrix``, serif in ``paper`` mode).
    family = rc["font.family"]
    rc[f"font.{family}"] = _with_font(font, _STACKS[family])
    rc["style"] = style
    return rc


def apply_plot_theme(theme=DEFAULT_THEME, font_scale=1.0, usetex=False, font=None,
                     mode=DEFAULT_MODE, width=None, glow=False, scale=None,
                     resolution=None):
    """Apply a plot theme via matplotlib rcParams.

    Thin wrapper over :func:`theme_config`: selects the base style, then pushes
    the theme's rcParams into ``matplotlib.rcParams``.

    Parameters
    ----------
    theme : {'light', 'dark', 'tron', 'tron_orange', 'tron_red', 'cyber_punk', 'matrix'}
        Which theme to apply. Defaults to :data:`DEFAULT_THEME`. Matched
        case-insensitively; a few common variants (``'cyberpunk'``,
        ``'the matrix'``, ...) are accepted too.
    font_scale : float
        Multiplies every font size (see ``_BASE_SIZES``). ``1.0`` gives a
        base size of 13; pass e.g. ``1.3`` for slides / print.
    usetex : bool
        If true, set ``text.usetex`` so text is rendered by a real LaTeX
        install. Requires ``latex`` + ``dvipng`` on PATH -- without them every
        plot fails at draw time, so this is off by default. When false, maths
        still gets the LaTeX *look* via the Computer Modern mathtext fontset.
    font : str or list of str, optional
        Override the body font. Leave as ``None`` to keep the font the current
        version uses; pass e.g. ``font="Georgia"`` or
        ``font=["Iowan Old Style", "Georgia"]`` to change it. The theme's own
        default stack is kept as a fallback.
    mode : {'regular', 'presenter', 'paper'}
        Sizing / output preset, independent of the colours. See
        :func:`theme_config`.
    width : float or {'column', 'page'}, optional
        Default figure width (inches or name), fonts unchanged. See
        :func:`theme_config`.
    scale, resolution :
        File size multiplier and saved-raster dpi preset. See
        :func:`theme_config`.
    glow : bool, float or dict
        Make every line / scatter / error bar glow automatically when drawn
        (see :func:`pretty_plot.glow`). ``True`` = default glow, a number =
        that ``strength``, a dict = keyword arguments of ``glow``
        (``strength``, ``size``, ``layers``, ``errorbars``, ``markers``).
        Ignored with a warning in ``paper`` mode.
    """
    cfg = theme_config(theme, font_scale=font_scale, usetex=usetex, font=font,
                       mode=mode, width=width, scale=scale, resolution=resolution)
    # Reset to matplotlib defaults first so switching e.g. paper -> regular
    # does not leave the paper figsize / tick settings behind.
    plt.style.use(["default", cfg.pop("style")])
    mpl.rcParams.update(cfg)
    global _ACTIVE_MODE
    _ACTIVE_MODE = _resolve_mode(mode)
    from .legend import _patch_legend_draw   # late import: legend imports theme
    _patch_legend_draw()
    _set_glow(glow)


def _set_glow(glow):
    """Store the auto-glow settings for the ``Axes.draw`` hook."""
    from .glow import GlowWarning, _patch_axes_draw
    global _GLOW
    _GLOW = None
    if glow is False or glow is None:
        return
    if _ACTIVE_MODE == "paper":
        warnings.warn("glow ignored in paper mode (journals / print don't want it).",
                      GlowWarning, stacklevel=3)
        return
    cfg = {"strength": 1.0, "size": None, "layers": 8, "errorbars": 1.0, "markers": 1.0}
    if isinstance(glow, dict):
        unknown = set(glow) - set(cfg)
        if unknown:
            raise ValueError(f"unknown glow option(s) {sorted(unknown)}; use {sorted(cfg)}")
        cfg.update(glow)
    elif glow is not True:
        cfg["strength"] = float(glow)
    _GLOW = cfg
    _patch_axes_draw()


def patch_errorbar(fmt="o"):
    """Make every ``Axes.errorbar`` default to ``fmt`` (markers, no line).

    After this, plot cells never need to pass ``fmt`` / ``capsize`` to get
    point-with-error-bar plots. Idempotent: calling it again (e.g. on a
    notebook re-run) does not stack wrappers.

    Parameters
    ----------
    fmt : str
        Format string used whenever ``errorbar`` is called without an explicit
        (non-empty) ``fmt``. Defaults to ``'o'``.
    """
    if getattr(Axes.errorbar, "_fmt_default", False):
        return

    _orig_errorbar = Axes.errorbar

    def _errorbar(self, *args, fmt=fmt, **kwargs):
        return _orig_errorbar(self, *args, fmt=(fmt or "o"), **kwargs)

    _errorbar._fmt_default = True
    Axes.errorbar = _errorbar


def use(theme=DEFAULT_THEME, patch_errorbars=True, font_scale=1.0, usetex=False, font=None,
        mode=DEFAULT_MODE, width=None, glow=False, scale=None, resolution=None):
    """Apply a theme and (by default) patch ``errorbar`` in one call.

    Parameters
    ----------
    theme : {'light', 'dark', 'tron', 'tron_orange', 'tron_red', 'cyber_punk', 'matrix'}
        Passed to :func:`apply_plot_theme`.
    patch_errorbars : bool
        If true (default), also call :func:`patch_errorbar`.
    font_scale, usetex, font, mode, width, glow, scale, resolution :
        Passed straight through to :func:`apply_plot_theme`. Leave ``font`` as
        ``None`` to keep the current-version default; pass a family name (or
        list) to override it. ``mode`` is ``'regular'``, ``'presenter'`` or
        ``'paper'``. ``glow=True`` makes every plot glow (dark themes).
    """
    apply_plot_theme(theme, font_scale=font_scale, usetex=usetex, font=font, mode=mode,
                     width=width, glow=glow, scale=scale, resolution=resolution)
    if patch_errorbars:
        patch_errorbar()


# Keys any theme touches -- the "pretty_plot-managed" slice of rcParams. Built
# once from the themes themselves so it can never drift out of sync.
_MANAGED_KEYS = None


def _managed_keys():
    """Frozenset of every rcParam name some theme sets (cached)."""
    global _MANAGED_KEYS
    if _MANAGED_KEYS is None:
        keys = set()
        for name in _THEMES:
            for mode in _MODES:
                cfg = theme_config(name, mode=mode)
                cfg.pop("style", None)
                keys.update(cfg)
        _MANAGED_KEYS = frozenset(keys)
    return _MANAGED_KEYS


def _detect_theme():
    """Best-effort name of the theme currently in rcParams, else ``None``.

    Matches on background colour + colour cycle, which together are unique
    across the built-in themes.
    """
    try:
        bg = mpl.colors.to_hex(mpl.rcParams["figure.facecolor"]).lower()
        cyc = [mpl.colors.to_hex(c).lower()
               for c in mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])]
    except (ValueError, KeyError):
        return None
    for name, spec in _THEMES.items():
        if (mpl.colors.to_hex(spec["bg"]).lower() == bg
                and [mpl.colors.to_hex(c).lower() for c in spec["cycle"]] == cyc):
            return name
    return None


def _is_switch(v):
    """True for non-numeric settings (strings, bools): unaffected by scale."""
    return isinstance(v, (str, bool))


def _detect_mode():
    """Best-effort name of the mode currently in rcParams.

    A non-regular mode is reported when every one of its non-numeric
    settings (except font family) is live, so ``paper`` with a custom font,
    ``width=``, ``scale=`` or ``resolution=`` still detects; anything else
    counts as ``'regular'``.
    """
    for name, spec in _MODES.items():
        rc = {k: v for k, v in spec["rc"].items()
              if k != "font.family" and _is_switch(v)}
        if rc and all(mpl.rcParams[k] == (list(v) if isinstance(v, tuple) else v)
                      for k, v in rc.items()):
            return name
    return "regular"


def current_config(full=False):
    """Return the plot configuration in effect **right now**.

    Reads live ``matplotlib.rcParams``, so it reflects whatever the notebook /
    script has actually applied (a pretty_plot theme, a hand tweak, or the
    matplotlib defaults).

    Parameters
    ----------
    full : bool
        ``False`` (default): only the rcParams pretty_plot manages -- the keys
        any theme sets. ``True``: every rcParam.

    Returns
    -------
    dict
        rcParam name -> current value, plus three convenience keys that are
        *not* rcParams:

        ``"theme"``
            name of the built-in theme whose background + colour cycle match
            the current state, or ``None``.
        ``"mode"``
            ``'presenter'`` / ``'paper'`` if that mode's settings are live,
            else ``'regular'``.
        ``"errorbar.patched"``
            whether :func:`patch_errorbar` is currently active.

        ``axes.prop_cycle`` is returned as its plain list of colours (hex
        strings), not as a ``Cycler``.
    """
    keys = list(mpl.rcParams) if full else _managed_keys()
    out = {}
    for k in keys:
        if k == "axes.prop_cycle":
            out[k] = [mpl.colors.to_hex(c) for c in
                      mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])]
        else:
            out[k] = mpl.rcParams[k]
    out["theme"] = _detect_theme()
    out["mode"] = _detect_mode()
    out["errorbar.patched"] = bool(getattr(Axes.errorbar, "_fmt_default", False))
    return out
