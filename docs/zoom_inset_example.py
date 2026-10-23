"""Histogram with a zoomed-in inset (inset_axes + indicate_inset_zoom)."""

import matplotlib.pyplot as plt
import numpy as np

# --- fake data shaped like the example (replace with your own arrays) -------
rng = np.random.default_rng(1)
data = {
    "hard":         rng.gamma(4, 0.022, 3000),
    "interm":       np.concatenate([rng.uniform(0.08, 0.9, 7000), rng.beta(6, 2, 800)]),
    "soft":         np.concatenate([1 - rng.exponential(0.035, 2800), rng.uniform(0.58, 0.95, 1200)]),
    "vhs":          np.concatenate([rng.normal(0.07, 0.02, 1100), rng.uniform(0.02, 0.7, 2700),
                                    rng.normal(0.97, 0.01, 60)]),
    "Strange Soft": rng.beta(14, 1.6, 400),
}
data = {k: v[(v >= 0) & (v <= 1)] for k, v in data.items()}

bins = np.linspace(0, 1, 81)            # same bins in the main plot and the zoom

# --- main plot ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))
for label, values in data.items():
    ax.hist(values, bins=bins, histtype="step", lw=2, label=label)
ax.set_xlabel("Disk Fraction", fontsize=18)
ax.set_ylabel("Frequency", fontsize=18)
ax.set_ylim(0, 1000)
ax.legend(loc="upper left", fontsize=14)

# --- zoomed inset ------------------------------------------------------------
# [x0, y0, width, height] in axes fractions (0..1) of the main plot
axins = ax.inset_axes([0.41, 0.44, 0.45, 0.45])
for label, values in data.items():
    axins.hist(values, bins=bins, histtype="step", lw=2)
axins.set_xlim(0.70, 1.01)              # the region to zoom into
axins.set_ylim(0, 100)

# draws the rectangle on the main plot + the two connecting lines
ax.indicate_inset_zoom(axins, edgecolor="black", alpha=1, lw=1)

fig.savefig("zoom_hist.png", dpi=200, bbox_inches="tight")
plt.show()
