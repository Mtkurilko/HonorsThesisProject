"""Publication figures for the thesis paper.

Each figure is drawn at the paper's full text width (7.0 in) with side-by-side
panels, one fixed color per algorithm, and direct value labels, so it can be
placed as a full-width figure in the two-column layout.

Reads results/refined_experiment_summary.csv (and the raw CSV for spreads) and
writes PDF + PNG to paper/images/.

Usage:  .venv/bin/python analysis/paper_figures.py
"""

import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = ROOT / "paper" / "images"

TEXT_WIDTH = 7.0  # inches, matches template.tex (8.5in page, 0.75in margins)

INK = "#1F1F1C"
MUTED = "#6B6960"
GRID = "#E3E0DA"
COLORS = {"RSA": "#A08A6E", "ECC": "#2B7BB9", "ML-KEM": "#D0112B", "HYBRID": "#8B3D9A"}
LABELS = {"RSA": "RSA-2048", "ECC": "ECDH P-256", "ML-KEM": "ML-KEM-512", "HYBRID": "Hybrid"}
ORDER = ["RSA", "ECC", "ML-KEM", "HYBRID"]

KX = {"RSA": "RSA", "ECC": "ECDH", "ML-KEM": "ML-KEM (KYBER)", "HYBRID": "HYBRID (ECC+KYBER)"}
WL = {"RSA": "RSA", "ECC": "ECC", "ML-KEM": "KYBER", "HYBRID": "HYBRID"}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8.5,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 6,
    "axes.labelsize": 8.5,
    "axes.labelcolor": INK,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": MUTED,
    "ytick.color": INK,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 8.5,
    "xtick.major.width": 0.6,
    "ytick.major.size": 0,
    "legend.fontsize": 7.5,
    "legend.frameon": False,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42,
})


# ------------------------------------------------------------------ data
# The project's own analysis/statistics module shadows the stdlib one here.
def mean(v):
    return sum(v) / len(v)


def stdev(v):
    m = mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def load_summary():
    d = {}
    with open(RESULTS / "refined_experiment_summary.csv") as f:
        for r in csv.DictReader(f):
            d[(r["Experiment"], r["Algorithm"], r["Metric"])] = float(r["Value"])
    return d


def load_raw(wanted):
    """Only the raw series we need (the per-message series is ~1M values each)."""
    csv.field_size_limit(sys.maxsize)
    out = {}
    with open(RESULTS / "refined_experiment_raw.csv") as f:
        for r in csv.DictReader(f):
            key = (r["Experiment"], r["Algorithm"], r["Metric"])
            if key in wanted:
                out[key] = [float(x) for x in r["RawValues"].split(";") if x]
    return out


S = load_summary()
RAW = load_raw({
    *{("file_transfer", WL[k], "throughput_mbps_raw") for k in ORDER},
    *{("hybrid_overhead", WL[k], "handshake_latency_ms_raw") for k in ("ECC", "ML-KEM", "HYBRID")},
})


# ------------------------------------------------------------------ helpers
def hbars(ax, keys, values, errs=None, fmt="{:.3f}", log=False, xmax=None, unit=""):
    """Horizontal bars in fixed algorithm order, top to bottom, with value labels."""
    y = list(range(len(keys)))[::-1]
    ax.barh(y, values, height=0.62, color=[COLORS[k] for k in keys], zorder=2,
            xerr=errs, error_kw={"elinewidth": 0.7, "capsize": 1.8, "ecolor": INK})
    ax.set_yticks(y, [LABELS[k] for k in keys])
    ax.tick_params(axis="y", pad=3)
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    if log:
        ax.set_xscale("log")
    hi = xmax if xmax else max(values) * (6 if log else 1.32)
    lo = min(values) / 2.5 if log else 0
    ax.set_xlim(lo, hi)
    for yi, v, e in zip(y, values, errs if errs is not None else [0] * len(values)):
        x = (v + e) * (1.28 if log else 1) + (0 if log else hi * 0.025)
        ax.text(x, yi, fmt.format(v) + unit, va="center", ha="left", fontsize=7.5, color=INK)
    ax.margins(y=0.08)


def plain_log_formatter(ax):
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


def save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.png", dpi=300)
    plt.close(fig)


# ------------------------------------------------------------------ figures
def fig_key_exchange():
    lat = [S[("key_exchange", KX[k], "latency_ms_mean")] for k in ORDER]
    sd = [S[("key_exchange", KX[k], "latency_ms_std")] for k in ORDER]
    tx = [S[("key_exchange", KX[k], "tx_bytes_mean")] for k in ORDER]

    fig, axes = plt.subplots(1, 3, figsize=(TEXT_WIDTH, 1.9), gridspec_kw={"width_ratios": [1.15, 1.05, 1]})
    ax = axes[0]
    hbars(ax, ORDER, lat, sd, fmt="{:.3g}", log=True, xmax=900, unit=" ms")
    plain_log_formatter(ax)
    ax.set_title("(a) Handshake latency")
    ax.set_xlabel("ms per handshake (log scale)")

    ax = axes[1]
    hbars(ax, ORDER, tx, fmt="{:,.0f}", xmax=2700, unit=" B")
    ax.set_yticklabels([])
    ax.set_title("(b) Bytes sent per handshake")
    ax.set_xlabel("bytes (public key + ciphertext)")

    ax = axes[2]
    for k, x, yv in zip(ORDER, tx, lat):
        ax.scatter(x, yv, s=34, color=COLORS[k], zorder=3, edgecolor="white", linewidth=0.8)
        dx, dy, ha = {"RSA": (60, 1.0, "left"), "ECC": (60, 1.0, "left"),
                      "ML-KEM": (-60, 1.0, "right"), "HYBRID": (-60, 1.0, "right")}[k]
        ax.annotate(LABELS[k], (x, yv), xytext=(x + dx, yv * dy), fontsize=7.5, va="center", ha=ha, color=INK)
    ax.set_yscale("log")
    plain_log_formatter(ax)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.tick_params(axis="y", labelsize=7.5, colors=MUTED, size=3)
    ax.set_xlim(0, 2300)
    ax.set_ylim(0.025, 200)
    ax.grid(color=GRID, linewidth=0.6, zorder=0)
    ax.set_title("(c) Latency vs. size")
    ax.set_xlabel("bytes per handshake")
    ax.set_ylabel("ms (log)")
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig_key_exchange")


def fig_hybrid():
    keys = ["ECC", "ML-KEM", "HYBRID"]
    raw = [RAW[("hybrid_overhead", WL[k], "handshake_latency_ms_raw")] for k in keys]
    lat = [mean(v) for v in raw]
    sd = [stdev(v) for v in raw]
    tx = [S[("hybrid_overhead", WL[k], "tx_bytes_mean")] for k in keys]

    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH, 1.45))
    hbars(axes[0], keys, lat, sd, fmt="{:.3f}", xmax=0.37, unit=" ms")
    axes[0].set_title("(a) Handshake latency")
    axes[0].set_xlabel("ms per handshake")
    hbars(axes[1], keys, tx, fmt="{:,.0f}", xmax=2500, unit=" B")
    axes[1].set_yticklabels([])
    axes[1].set_title("(b) Bytes sent per handshake")
    axes[1].set_xlabel("bytes")
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig_hybrid")


def fig_signatures():
    algs = [("ECC", "ECDSA", "ECDSA P-256"), ("ML-KEM", "ML-DSA (Dilithium)", "ML-DSA-44")]
    keys = [a[0] for a in algs]
    names = {a[0]: a[2] for a in algs}

    def series(metric):
        return [S[("signatures", a[1], metric)] for a in algs]

    panels = [
        ("(a) Sign time", series("sign_ms_mean"), series("sign_ms_std"), "{:.3f}", " ms", "ms per signature", 0.36),
        ("(b) Verify time", series("verify_ms_mean"), series("verify_ms_std"), "{:.3f}", " ms", "ms per verification", 0.07),
        ("(c) Signature size", series("signature_size_bytes_mean"), None, "{:,.0f}", " B", "bytes", 3300),
    ]
    saved = dict(LABELS)
    LABELS.update(names)
    fig, axes = plt.subplots(1, 3, figsize=(TEXT_WIDTH, 1.25))
    for i, (ax, (title, vals, errs, fmt, unit, xl, xmax)) in enumerate(zip(axes, panels)):
        hbars(ax, keys, vals, errs, fmt=fmt, xmax=xmax, unit=unit)
        ax.set_title(title)
        ax.set_xlabel(xl)
        if i:
            ax.set_yticklabels([])
    LABELS.clear()
    LABELS.update(saved)
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig_signatures")


def fig_messaging():
    def share(v):
        h = S[("messaging", v, "handshake_latency_ms_mean")]
        s = S[("messaging", v, "session_latency_ms_mean")]
        per = h * (1 - S[("messaging", v, "reuse_ratio")])
        return per / (per + s) * 100

    tput = [S[("messaging", WL[k], "messages_per_sec")] / 1000 for k in ORDER]
    shares = [share(WL[k]) for k in ORDER]

    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH, 1.75))
    hbars(axes[0], ORDER, tput, fmt="{:.1f}", xmax=25.5, unit="k msg/s")
    axes[0].set_title("(a) Messaging throughput")
    axes[0].set_xlabel("thousand messages per second")

    ax = axes[1]
    hbars(ax, ORDER, shares, fmt="{:.2f}", log=True, xmax=200, unit="%")
    ax.texts[0].set_text(f"{shares[0]:.1f}%")
    plain_log_formatter(ax)
    ax.set_yticklabels([])
    ax.set_title("(b) Share of total time spent on handshakes")
    ax.set_xlabel("% of messaging time (log scale)")
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig_messaging")


def fig_file_transfer():
    tp_raw = [RAW[("file_transfer", WL[k], "throughput_mbps_raw")] for k in ORDER]
    tp = [mean(v) for v in tp_raw]
    tp_sd = [stdev(v) for v in tp_raw]
    hs = [S[("file_transfer", WL[k], "handshake_latency_ms_mean")] for k in ORDER]

    fig, axes = plt.subplots(1, 2, figsize=(TEXT_WIDTH, 1.75))
    ax = axes[0]
    hbars(ax, ORDER, tp, tp_sd, fmt="{:.1f}", xmax=55, unit=" Mbps")
    ax.set_title("(a) File-transfer throughput (mean ± SD)")
    ax.set_xlabel("Mbps, 5 MB file")

    ax = axes[1]
    hbars(ax, ORDER, hs, fmt="{:.3g}", log=True, xmax=900, unit=" ms")
    plain_log_formatter(ax)
    ax.set_yticklabels([])
    ax.set_title("(b) Setup (handshake) latency")
    ax.set_xlabel("ms per handshake (log scale)")
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig_file_transfer")


def main():
    fig_key_exchange()
    fig_hybrid()
    fig_signatures()
    fig_messaging()
    fig_file_transfer()
    print(f"Wrote paper figures to {OUT}")


if __name__ == "__main__":
    main()
