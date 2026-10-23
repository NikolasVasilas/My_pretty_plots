"""pretty_plot: high-visibility matplotlib themes.

Drop-in matplotlib theming for any project: themes, regular / presenter /
paper modes, legends outside the plot and neon glow.

Add new modules alongside ``theme.py`` and import them from here; the package is
meant to be installed editable (``pip install -e``), so edits take effect
without reinstalling.
"""

from .glow import GlowWarning, glow
from .legend import LegendSizeWarning, SquashedPlotWarning, legend
from .theme import (
    CYBER_PUNK,
    DEFAULT_MODE,
    DEFAULT_MONO,
    DEFAULT_SANS,
    DEFAULT_SERIF,
    DEFAULT_THEME,
    MATRIX,
    MODES,
    NEON,
    RESOLUTIONS,
    PASTEL,
    THEMES,
    TRON,
    TRON_ORANGE,
    TRON_RED,
    apply_plot_theme,
    current_config,
    patch_errorbar,
    theme_config,
    use,
)

__version__ = "0.8.0"

__all__ = [
    "__version__",
    "DEFAULT_THEME",
    "DEFAULT_SANS",
    "DEFAULT_MONO",
    "DEFAULT_SERIF",
    "THEMES",
    "MODES",
    "RESOLUTIONS",
    "DEFAULT_MODE",
    "NEON",
    "PASTEL",
    "TRON",
    "TRON_ORANGE",
    "TRON_RED",
    "CYBER_PUNK",
    "MATRIX",
    "apply_plot_theme",
    "patch_errorbar",
    "use",
    "theme_config",
    "current_config",
    "legend",
    "LegendSizeWarning",
    "SquashedPlotWarning",
    "glow",
    "GlowWarning",
]
