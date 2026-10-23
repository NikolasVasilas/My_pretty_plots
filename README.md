# pretty_plot

High-visibility matplotlib themes for everyday plotting, slides and papers,
applied with one call. It also handles legends outside the plot and adds a neon
glow on the dark themes.

## Themes

| name | look |
|---|---|
| `light` | white background, saturated-pastel colour cycle, no grid |
| `dark` | black background, neon colour cycle, no grid |
| `tron` | deep-blue background, electric cyan / amber cycle, faint cyan grid |
| `tron_orange` | dark-amber background, orange-led Tron cycle, faint amber grid |
| `tron_red` | dark-crimson background, red-led Tron cycle, faint red grid |
| `cyber_punk` | near-black violet background, hot-pink / acid-yellow / cyan cycle, faint violet grid |
| `matrix` | pure-black background, monospace text, shades-of-green cycle, faint green grid |

Theme names are matched case-insensitively and a few variants / misspellings are
accepted (`'cyberpunk'`, `'the matrix'`, `'tron-legacy'`, `'red tron'`, …).
`pretty_plot.THEMES` is the tuple of canonical names.

Shared by every theme (values for the default `regular` mode — `presenter` and
`paper` change sizes, weights and the legend box, see [Modes](#modes)):

- `errorbar.capsize = 3`, `lines.markersize = 5`
- big fonts (base 13, scalable via `font_scale`), bold body text, `$...$`
  maths in Computer Modern (the LaTeX look, no TeX install needed — `matrix`
  uses the plain mathtext set to match its monospace body)
- opaque framed legend box so legends stay readable over busy / dark plots
  (toggle per legend with `pretty_plot.legend(frame=...)`)
- optional monkeypatch so every `errorbar()` defaults to `fmt="o"` (bare markers,
  no connecting line) — plot code never needs to pass `fmt` / `capsize`

## Install (editable)

```bash
pip install -e /Users/nvasilas/Analysis/Pretty_plot
```

Editable install means you can add new `.py` files under `pretty_plot/` or edit
the existing ones and the changes take effect immediately — no reinstall. (A
brand-new top-level module is picked up on next interpreter start / kernel
restart.)

## Use

```python
from pretty_plot import use

use('dark')          # apply theme + patch errorbar in one call
use('light')
use('tron')
use('tron_orange')
use('tron_red')
use('cyber_punk')    # 'cyberpunk' works too
use('matrix')

use('tron', mode='presenter')            # slides   (see Modes)
use('light', mode='paper')               # journals (see Modes)
```

Legends, inside or outside the plot, with or without a box (see Legends):

```python
import pretty_plot as pp
pp.legend(where='right', pad=10, frame=True)
```

Neon glow on dark themes, for the whole plot or chosen parts of it (see Glow):

```python
pp.glow()                     # everything
pp.glow(line, strength=2)     # one line
pp.use('tron', glow=True)     # every plot, automatically
```

Or the two steps separately:

```python
from pretty_plot import apply_plot_theme, patch_errorbar

apply_plot_theme('dark')   # rcParams only
patch_errorbar()           # errorbar() -> fmt="o" by default (idempotent)
```

Flip the theme any time and re-run the plot cells:

```python
apply_plot_theme('light')
```

## Modes

The theme picks the colours; the **mode** picks sizes, weights and export
settings for where the figure is going. Any theme works with any mode.

| mode | for | what changes |
|---|---|---|
| `regular` (default) | day-to-day notebooks | nothing — exactly the pre-0.5 look |
| `presenter` | slides / talks | base font 20 (labels 22, ticks 18, title 24), bold, lines 2.8, markers 9, thick spines + ticks, 16:9 figure (8 × 4.5 in), `savefig.dpi=200`, warns about oversized legends |
| `paper` | journal figures | one-column figure drawn at 2× (file 7.0 × 5.2 in, 20 pt text) that prints at 3.5 in with 10 pt text when included with `width=\columnwidth`, Times/STIX serif + STIX maths, normal weight, thin lines, inward ticks on all four sides with minor ticks, frameless legend, sharp 200-dpi notebook preview, saves to **PDF** when no extension is given, PNG fallback at 600 dpi, `bbox='tight'`, TrueType fonts embedded (`pdf.fonttype=42`) |

```python
use('dark')                      # regular
use('tron', mode='presenter')
use('light', mode='paper')       # papers: pair with 'light'
use('light', mode='paper', font_scale=1.1)   # still scalable
use('light', mode='paper', resolution='very_high')   # 1200-dpi PNGs
```

Aliases: `'slides'`, `'talk'`, `'presentation'` → `presenter`;
`'publication'`, `'journal'`, `'print'` → `paper`; `'default'`, `'normal'` →
`regular`. `pretty_plot.MODES` is the tuple of canonical names.

In `paper` mode `font=` goes to the front of the serif stack
(`DEFAULT_SERIF`).

**Getting paper figures sharp and readable in LaTeX.** `paper` mode draws
the figure **2× larger** than it is printed (file 7.0 × 5.2 in, fonts 20 pt,
lines, markers and ticks doubled too) and you let LaTeX shrink it to the
column width. Everything comes out at the right printed size (10 pt text),
and a PNG keeps twice the pixels of a natural-size figure:

```python
use('light', mode='paper')                 # one column (prints 3.5 in wide)
use('light', mode='paper', width='page')   # full text width (prints 7.1 in)
use('light', mode='paper', width=6.3)      # e.g. a thesis \textwidth, in inches
fig.savefig('lightcurve')                  # -> lightcurve.pdf (vector)
```

```latex
\includegraphics[width=\columnwidth]{lightcurve.pdf}   % width='page' -> \textwidth
```

`width=` (any mode) is always the **printed** width in inches or by name
(`'column'` / `'single'` = 3.5, `'page'` / `'double'` = 7.1); the file is
`scale` times that. It keeps the mode's aspect ratio and does **not** change
the font sizes, so text is 10 pt in print at every width. To find your
document's widths, put `\the\columnwidth` / `\the\textwidth` in the `.tex`
(pt; divide by 72.27 for inches).

`scale=` changes the drawing factor (`paper` default 2, other modes 1):
`scale=1` gives the natural-size figure (3.5 × 2.6 in, 10 pt; include it with
no `width=`), `scale=3` an even bigger one. Fonts, line widths, markers,
ticks and paddings are all multiplied, so the look never changes; only the
file gets bigger. It works in any mode (`use('tron', scale=1.5)`).
Sizes you pass yourself (`figsize=`, `pad=`, `linewidth=`, …) are in file
units, so in `paper` mode use 2× the printed value: a figure printed at
7.1 × 2.6 in is `figsize=(14.2, 5.2)`.

**Resolution.** A PDF is vector and is sharp at any zoom whatever the
resolution. For PNG / JPG output pick `resolution=` (sets `savefig.dpi`):

| `resolution` | dpi | for |
|---|---|---|
| `'low'` | 100 | quick drafts, small files |
| `'medium'` (`'median'`) | 300 | screens, most journals' minimum |
| `'high'` | 600 | print (the `paper` default) |
| `'very_high'` | 1200 | line art / zoom-in figures |

Any number works too (`resolution=450`); `pretty_plot.RESOLUTIONS` holds the
table. `fig.savefig(..., dpi=...)` still overrides it for a single file.

Absolute sizes differ between `paper` and `presenter` because the figures
end up at different physical sizes (a 3.5 in journal column vs ~60% of a
13.33 in wide slide; ratio measured in print, after the 2× shrink), but the text-to-figure ratio is matched (~2.5 pt per inch
of figure width), so both read at the same relative size. Insert slides at the
size they were made, paper figures at `width=\columnwidth`.

Applying a theme now resets rcParams to matplotlib defaults first, so switching
`paper` → `regular` doesn't leave the paper figure size or ticks behind.

## Legends

`pretty_plot.legend(where=...)` places a legend inside the axes or outside the
plot on any side, in any mode:

```python
import pretty_plot as pp

pp.legend()                    # inside, matplotlib's 'best' spot (= ax.legend())
pp.legend(where='right')       # outside right, vertically centred
pp.legend(where='right top')   # outside right, aligned with the top
pp.legend(where='top')         # above the plot, all entries in one row
pp.legend(where='bottom left') # below, left-aligned
pp.legend(where='left')
pp.legend(where='right', pad=15)   # 15 pt extra gap between plot and legend
pp.legend(where='top', frame=True) # line around the legend box
pp.legend(frame=False)             # no box (inside)
pp.legend(where='right', frame_width=2.5)            # box line 2.5 pt thick (turns the box on)
pp.legend(frame_width=0.5, edgecolor='tab:red')      # thin red box
```

`where` works the same in every mode (`regular`, `presenter`, `paper`).

`frame=True` draws a line around the legend box, inside or outside, in any
mode; `frame=False` removes it; leave it out for the mode default (framed in
`regular` / `presenter`, frameless in `paper`). The line width matches the
plot border (`axes.linewidth`) unless you pass `frame_width=` (points); the
colour is the theme foreground unless you pass `edgecolor=`. Passing
`frame_width` turns the box on by itself, so it also works in `paper` mode,
where legends have no box by default. `frame_width=0` means no box.

`pad` (points; 1 pt = 1/72 in) controls the plot–legend distance. Outside, it
is **extra** gap on top of the default ~4–5 pt, measured from the plot
including its tick and axis labels; negative values pull the legend closer.
Inside, it is the gap between the legend and the axes edge.

The legend's space comes out of the figure, so the plot shrinks to make room
(the figure size stays what you chose). If an outside legend plus its `pad`
leaves the plot less than half the figure width (side legend) or height
(top / bottom legend), drawing the figure raises a
`pretty_plot.SquashedPlotWarning` (any mode, once per legend) with suggestions:
smaller `pad`, another side, shorter labels, or a larger figure.

`where` is `'<side> [<align>]'`: side `right` / `left` / `top` / `bottom`
(`above` / `below` work too); align `top` / `middle` / `bottom` for left/right
and `left` / `middle` / `right` for top/bottom (default `middle`). Outside
legends are figure legends: they collect the entries of every panel (each label
once), so one call gives a shared legend for a multi-panel figure, and the
figure switches to the constrained layout engine to make room. Extra keyword
arguments go to matplotlib (`ncols=2`, `title='sources'`, …).

In `presenter` mode, drawing a legend that covers more than 25% of its axes or
has more than 6 entries raises a `pretty_plot.LegendSizeWarning` (once per
legend). Silence it with
`warnings.filterwarnings('ignore', category=pretty_plot.LegendSizeWarning)`.

## Glow

Make the data glow, neon style, on the dark themes (`dark`, `tron*`,
`cyber_punk`, `matrix`). Each line / marker / error bar / scatter gets a stack of
wide, faint strokes in its own colour underneath it (matplotlib path effects),
so it stays **vector** in PDF / SVG. Grid, spines, ticks and text are left
alone. Legend entries glow like the artists they stand for (the whole
errorbar symbol too), whether the legend is made before or after `pp.glow()`.

Call it after plotting:

```python
import pretty_plot as pp
pp.use('tron')
fig, ax = plt.subplots()
line, = ax.plot(x, y, label='model')
sc = ax.scatter(x, y_obs, label='data')
eb = ax.errorbar(x, y2, yerr=err)
pp.legend()

pp.glow()                            # everything in the current figure
pp.glow(ax)                          # one axes (fig / list of axes also fine)
pp.glow(line)                        # just this line
pp.glow([line, eb])                  # a chosen set: lines, scatters, errorbar / bar containers
pp.glow(sc, points=y_obs > 3)        # only some scatter points (mask / indices / slice)
pp.glow(line, points=slice(40, 60))  # only a segment of a line
pp.glow(line, strength=2, size=12)   # brighter (opacity) / wider (pt) halo
pp.glow(sc, color='magenta')         # own glow colour
pp.glow(ax, errorbars=0)            # error bars: only the points glow, plain whiskers / caps
pp.glow(ax, markers=0)              # error bars: only the whiskers / caps glow
pp.glow(ax, markers=2.5, errorbars=0.5)  # bright points on softly glowing bars
```

Or for every plot from now on — fine-tune or switch off single artists after:

```python
pp.use('cyber_punk', glow=True)      # or glow=1.5 (strength), glow={'strength': 2, 'markers': 2, 'errorbars': 0.5}
pp.glow(line, strength=0)            # ... but not this line
pp.glow(line, strength=2)            # ... and this one brighter
```

| option | default | meaning |
|---|---|---|
| `strength` | `1` | halo opacity; `2` = strong, `0` = remove |
| `size` | `4 × lines.linewidth` | halo reach in points (so it grows in `presenter`) |
| `layers` | `8` | number of strokes; more = smoother fade |
| `errorbars` | `1` | strength multiplier for error-bar whiskers / caps (`0.5` = softer, `0` = only the points glow) |
| `markers` | `1` | strength multiplier for the error-bar data points (`0` = only the bars glow, `2` = brighter points) |
| `color` | artist's own | one glow colour for everything in the call (legend follows); needed for a colormapped scatter (otherwise skipped) |
| `points` | all | glow only these points of a single line / scatter |
| `force` | `False` | apply in `paper` mode too |

Notes:

- Naming an artist always (re)sets its glow; `pp.glow()` / `pp.glow(ax)` and
  auto-glow skip artists that already have one, so per-artist settings survive.
- Bars / patches only glow when named (`pp.glow(ax.bar(...))`), not via
  `pp.glow()` — a glowing histogram is usually too much.
- In `paper` mode glow is skipped with a `pretty_plot.GlowWarning` (print /
  journals don't want it) unless `force=True`; on a light background it is
  applied but warned about (it looks blurry rather than neon there).
- Many points with error bars turn to mud fast: use `errorbars=0.5` (softer) or `0`, or glow
  only the line through them.

## Fonts

Every theme uses a built-in font stack by default (a Helvetica/Arial-led sans;
`matrix` uses a JetBrains-Mono-led monospace). That default is unchanged from
older versions — you get it whenever you don't pass `font`.

Pass `font=` to override it. Your choice goes to the front and the theme's
default stack stays on as a fallback, so text still renders if the font is
missing:

```python
use('dark', font='Georgia')
use('dark', font=['Iowan Old Style', 'Charter', 'Georgia'])
apply_plot_theme('matrix', font='Courier New')   # matrix -> feeds the mono stack
```

`DEFAULT_SANS` / `DEFAULT_MONO` / `DEFAULT_SERIF` are the default stacks (read-only tuples; serif is used by `paper` mode).

## Inspecting the configuration

```python
from pretty_plot import current_config, theme_config

current_config()          # the rcParams live right now (theme-managed subset)
current_config(full=True) # every rcParam
theme_config('tron')      # what 'tron' WOULD apply — returned, not applied
theme_config('dark', font_scale=1.3, font='Georgia')
theme_config('light', mode='paper')
```

`current_config()` returns a plain dict of rcParam → current value, plus three
extra keys: `"theme"` (name of the built-in theme whose background + colour
cycle match the current state, else `None`), `"mode"` (`'presenter'` / `'paper'`
if that mode's settings are live, else `'regular'`) and `"errorbar.patched"` (bool).
`axes.prop_cycle` comes back as a plain list of hex colours.

`theme_config(...)` is the exact dict `apply_plot_theme` would push into
`rcParams`, with one extra key `"style"` naming the matplotlib base style it
layers on first (pop it before `rcParams.update`). It does **not** touch the
live rcParams — use it to preview or diff a theme, or to grab one theme's
suggested settings and tweak them by hand.

## API

| name | what it does |
|---|---|
| `apply_plot_theme(theme='dark', font_scale=1.0, usetex=False, font=None, mode='regular', width=None, glow=False, scale=None, resolution=None)` | set matplotlib rcParams for a theme (colours, fonts, grid, legend frame) |
| `patch_errorbar(fmt='o')` | make `Axes.errorbar` default to `fmt`; idempotent |
| `use(theme='dark', patch_errorbars=True, font_scale=1.0, usetex=False, font=None, mode='regular', width=None, glow=False, scale=None, resolution=None)` | `apply_plot_theme` + `patch_errorbar` |
| `theme_config(theme='dark', font_scale=1.0, usetex=False, font=None, mode='regular', width=None, scale=None, resolution=None)` | the rcParams a theme *would* apply, returned as a dict (not applied) |
| `current_config(full=False)` | the rcParams in effect right now, + detected `theme` and `errorbar.patched` |
| `legend(where='inside', ax=None, fig=None, pad=None, frame=None, frame_width=None, **kw)` | legend inside, or outside on a chosen side / alignment, with optional box |
| `LegendSizeWarning` | warning category for oversized legends in `presenter` mode |
| `SquashedPlotWarning` | warning category for an outside legend that leaves the plot < 50% of the figure |
| `glow(target=None, strength=1, size=None, layers=8, errorbars=1, markers=1, color=None, points=None, force=False)` | neon glow on a figure / axes / single artists / some points |
| `GlowWarning` | warning category: glow skipped in `paper` mode, or used on a light background |
| `NEON`, `PASTEL`, `TRON`, `TRON_ORANGE`, `TRON_RED`, `CYBER_PUNK`, `MATRIX` | the per-theme colour-cycle lists |
| `THEMES` | tuple of canonical theme names |
| `MODES` | `('regular', 'presenter', 'paper')` |
| `RESOLUTIONS` | `{'low': 100, 'medium': 300, 'high': 600, 'very_high': 1200}` (dpi) |
| `DEFAULT_MODE` | `'regular'` |
| `DEFAULT_THEME` | `'dark'` |
| `DEFAULT_SANS`, `DEFAULT_MONO`, `DEFAULT_SERIF` | the built-in default font stacks |

- `font_scale` multiplies every font size of the chosen mode — use `mode='presenter'` / `'paper'` for slides / print and `font_scale` for fine-tuning.
- `usetex=True` switches to a real LaTeX install (`latex` + `dvipng` must be on
  PATH, else plots fail at draw time). Left off by default; the Computer Modern
  mathtext fontset already gives the LaTeX look without it.

## Extending

Add a module, e.g. `pretty_plot/panels.py`, then re-export what you want from
`pretty_plot/__init__.py`. See `docs/pretty_plot_examples.ipynb` for worked
examples.
