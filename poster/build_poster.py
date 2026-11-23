"""Build the 48" x 36" Honors Thesis poster.

Reads benchmark results from ../results, generates poster.html with inline SVG
charts, then prints it to poster.pdf with headless Google Chrome.

Usage:  python3 poster/build_poster.py
"""

import csv
import math
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "results" / "refined_experiment_summary.csv"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ---------------------------------------------------------------- palette
RED = "#E21737"      # Marist template red (header + headings)
INK = "#1F1F1C"
INK2 = "#505046"     # template secondary gray
MUTED = "#77756C"
RULE = "#D9D7D5"
TINT = "#F4F2EE"
C = {                 # one color per algorithm, fixed everywhere
    "RSA": "#A08A6E",
    "ECC": "#2B7BB9",
    "ML-KEM": "#D0112B",
    "HYBRID": "#8B3D9A",
}
NAMES = {"RSA": "RSA", "ECC": "ECC", "ML-KEM": "ML-KEM", "HYBRID": "Hybrid"}
ORDER = ["RSA", "ECC", "ML-KEM", "HYBRID"]


# ---------------------------------------------------------------- data
def load():
    d = {}
    with open(RESULTS) as f:
        for r in csv.DictReader(f):
            d[(r["Experiment"], r["Algorithm"], r["Metric"])] = float(r["Value"])
    return d


D = load()
KX_ALG = {"RSA": "RSA", "ECC": "ECDH", "ML-KEM": "ML-KEM (KYBER)", "HYBRID": "HYBRID (ECC+KYBER)"}
WL_ALG = {"RSA": "RSA", "ECC": "ECC", "ML-KEM": "KYBER", "HYBRID": "HYBRID"}

kx_ms = {k: D[("key_exchange", v, "latency_ms_mean")] for k, v in KX_ALG.items()}
kx_b = {k: D[("key_exchange", v, "tx_bytes_mean")] for k, v in KX_ALG.items()}
def _handshake_share(v):
    """Share of total messaging time spent on handshakes.

    session_latency excludes the handshake, and one handshake is reused across
    several sessions, so: share = h*(1-r) / (h*(1-r) + s), r = reuse ratio.
    """
    h = D[("messaging", v, "handshake_latency_ms_mean")]
    s = D[("messaging", v, "session_latency_ms_mean")]
    per_session = h * (1 - D[("messaging", v, "reuse_ratio")])
    return per_session / (per_session + s) * 100


msg_share = {k: _handshake_share(v) for k, v in WL_ALG.items()}
msg_tput = {k: D[("messaging", v, "messages_per_sec")] for k, v in WL_ALG.items()}
ft_tput = {k: D[("file_transfer", v, "throughput_mbps_mean")] for k, v in WL_ALG.items()}
sig = {
    "sign": (D[("signatures", "ECDSA", "sign_ms_mean")], D[("signatures", "ML-DSA (Dilithium)", "sign_ms_mean")]),
    "verify": (D[("signatures", "ECDSA", "verify_ms_mean")], D[("signatures", "ML-DSA (Dilithium)", "verify_ms_mean")]),
    "size": (D[("signatures", "ECDSA", "signature_size_bytes_mean")], D[("signatures", "ML-DSA (Dilithium)", "signature_size_bytes_mean")]),
}

kem_speedup = kx_ms["ECC"] / kx_ms["ML-KEM"]
kem_bytes_x = kx_b["ML-KEM"] / kx_b["ECC"]
rsa_x = kx_ms["RSA"] / kx_ms["ECC"]
verify_ratio = sig["verify"][1] / sig["verify"][0]   # ML-DSA / ECDSA, ~1.0 = parity
sign_x = sig["sign"][1] / sig["sign"][0]
size_x = sig["size"][1] / sig["size"][0]
ft_spread = max(ft_tput.values()) - min(ft_tput.values())
hyb_ft_drop = (ft_tput["ECC"] - ft_tput["HYBRID"]) / ft_tput["ECC"] * 100


# ---------------------------------------------------------------- svg helpers
def t(x, y, s, size=22, fill=INK, weight=400, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{s}</text>')


def rbar(x, y, w, h, fill, r=4):
    """Horizontal bar anchored at x with rounded data-end only."""
    w = max(w, 1.5)
    r = min(r, w / 2, h / 2)
    return (f'<path d="M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} '
            f'V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z" fill="{fill}"/>')


def svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{label}" '
            f'font-family="Arial, Helvetica, sans-serif">{body}</svg>')


# ---------------------------------------------------------------- charts
def chart_handshake_time():
    W, X0, BW, ROW, BH = 800, 150, 450, 60, 36
    vmax = 0.30
    out = []
    # gridlines
    for v in (0, 0.1, 0.2, 0.3):
        gx = X0 + v / vmax * BW
        out.append(f'<line x1="{gx:.1f}" y1="8" x2="{gx:.1f}" y2="{8 + ROW * 4}" stroke="{RULE}" stroke-width="1.5"/>')
        out.append(t(gx, 8 + ROW * 4 + 28, f"{v:.1f} ms", 21, MUTED, anchor="middle"))
    for i, k in enumerate(ORDER):
        y = 8 + i * ROW + (ROW - BH) / 2
        out.append(t(X0 - 14, y + BH * 0.72, NAMES[k], 25, INK, 700, "end"))
        v = kx_ms[k]
        if k == "RSA":
            w = BW + 70
            out.append(rbar(X0, y, w, BH, C[k]))
            bx = X0 + BW - 40   # axis-break marks
            for dx in (0, 14):
                out.append(f'<path d="M{bx + dx - 6},{y - 5} L{bx + dx + 6},{y + BH + 5}" stroke="#FFFFFF" stroke-width="6"/>')
            out.append(t(X0 + 14, y + BH * 0.72, f"{v:.1f} ms · {rsa_x:.0f}× slower than ECC", 23, "#FFFFFF", 700))
        else:
            w = v / vmax * BW
            out.append(rbar(X0, y, w, BH, C[k]))
            note = {"ML-KEM": f"  ({kem_speedup:.1f}× faster)", "HYBRID": "", "ECC": ""}[k]
            out.append(t(X0 + w + 12, y + BH * 0.72, f"{v:.3f} ms{note}", 23, INK, 700 if k == "ML-KEM" else 400))
    return svg(W, 8 + ROW * 4 + 36, "".join(out), "Handshake time per algorithm")


def chart_handshake_bytes():
    W, X0, BW, ROW, BH = 800, 150, 430, 60, 36
    vmax = 2000
    out = []
    for v in (0, 500, 1000, 1500, 2000):
        gx = X0 + v / vmax * BW
        out.append(f'<line x1="{gx:.1f}" y1="8" x2="{gx:.1f}" y2="{8 + ROW * 4}" stroke="{RULE}" stroke-width="1.5"/>')
        out.append(t(gx, 8 + ROW * 4 + 28, f"{v:,} B", 21, MUTED, anchor="middle"))
    for i, k in enumerate(ORDER):
        y = 8 + i * ROW + (ROW - BH) / 2
        out.append(t(X0 - 14, y + BH * 0.72, NAMES[k], 25, INK, 700, "end"))
        v = kx_b[k]
        w = v / vmax * BW
        out.append(rbar(X0, y, w, BH, C[k]))
        mult = v / kx_b["ECC"]
        note = "" if k == "ECC" else f"  ({mult:.1f}×)"
        out.append(t(X0 + w + 12, y + BH * 0.72, f"{v:,.0f} B{note}", 23, INK, 700 if k == "ML-KEM" else 400))
    return svg(W, 8 + ROW * 4 + 36, "".join(out), "Bytes sent per handshake")


def chart_session_share():
    W, X0, BW, ROW, BH = 800, 150, 400, 70, 42
    out = []
    out.append(t(X0 + BW + 24, 24, "messages / sec", 20, MUTED, 700))
    for i, k in enumerate(ORDER):
        y = 40 + i * ROW
        out.append(t(X0 - 14, y + BH * 0.72, NAMES[k], 25, INK, 700, "end"))
        share = msg_share[k]
        hw = max(share / 100 * BW, 3)
        # rest of session (sending messages) – light neutral, 2px surface gap
        out.append(f'<rect x="{X0 + hw + 2:.1f}" y="{y}" width="{BW - hw - 2:.1f}" height="{BH}" rx="4" fill="#E6E3DD"/>')
        out.append(f'<rect x="{X0}" y="{y}" width="{hw:.1f}" height="{BH}" fill="{C[k]}"/>')
        lbl = f"{share:.1f}%" if share >= 10 else f"{share:.2f}%"
        if share >= 25:
            out.append(t(X0 + 12, y + BH * 0.72, lbl, 24, "#FFFFFF", 700))
        else:
            out.append(t(X0 + hw + 14, y + BH * 0.72, lbl, 24, INK, 700))
        out.append(t(X0 + BW + 24, y + BH * 0.72, f"{msg_tput[k]:,.0f}", 25, INK, 700))
    hy = 40 + ROW * 4 + 6
    # legend
    out.append(f'<rect x="{X0}" y="{hy}" width="22" height="22" fill="{INK2}"/>')
    out.append(t(X0 + 30, hy + 18, "handshake (setup)", 21, INK2))
    out.append(f'<rect x="{X0 + 225}" y="{hy}" width="22" height="22" rx="3" fill="#E6E3DD"/>')
    out.append(t(X0 + 255, hy + 18, "sending messages", 21, INK2))
    return svg(W, hy + 32, "".join(out), "Share of messaging session time spent on handshake")


def lattice_svg():
    """2-D lattice: long 'public' basis vs the hidden short vector."""
    W, H, S = 560, 360, 20.0
    cx, cy = W / 2 - 40, H / 2 + 20
    u, v = (3, 1), (1, 2)
    pts = []
    for i in range(-12, 13):
        for j in range(-12, 13):
            x, y = i * u[0] + j * v[0], i * u[1] + j * v[1]
            px, py = cx + x * S, cy - y * S
            if 12 < px < W - 12 and 12 < py < H - 12:
                pts.append((px, py, x == 0 and y == 0))
    out = [f'<rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{TINT}"/>']
    for px, py, o in pts:
        if not o:
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#B9B5AC"/>')

    def arrow(x, y, col, wdt):
        ex, ey = cx + x * S, cy - y * S
        ang = math.atan2(ey - cy, ex - cx)
        a1 = (ex - 16 * math.cos(ang - 0.45), ey - 16 * math.sin(ang - 0.45))
        a2 = (ex - 16 * math.cos(ang + 0.45), ey - 16 * math.sin(ang + 0.45))
        return (f'<line x1="{cx}" y1="{cy}" x2="{ex - 8 * math.cos(ang):.1f}" y2="{ey - 8 * math.sin(ang):.1f}" stroke="{col}" stroke-width="{wdt}" stroke-linecap="round"/>'
                f'<path d="M{ex:.1f},{ey:.1f} L{a1[0]:.1f},{a1[1]:.1f} L{a2[0]:.1f},{a2[1]:.1f} Z" fill="{col}"/>')
    # public "bad" basis: (7,4) and (10,5) generate the same lattice
    out.append(arrow(7, 4, INK2, 4))
    out.append(arrow(10, 5, INK2, 4))
    out.append(arrow(2, -1, RED, 6))
    out.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{INK}"/>')
    halo = 'stroke="#F4F2EE" stroke-width="8" paint-order="stroke" stroke-linejoin="round"'
    out.append(t(cx + 10 * S - 6, cy - 5 * S - 20, "long basis vectors", 22, INK2, 700, "end", halo))
    out.append(t(cx + 2 * S + 14, cy + 1 * S + 30, "short vector", 22, RED, 700, extra=halo))
    return svg(W, H, "".join(out), "Two-dimensional lattice with a hidden short vector")


# ---------------------------------------------------------------- icons
def icon(name, size=1.25, col=INK):
    p = {
        "record": f'<rect x="8" y="16" width="48" height="34" rx="4" fill="none" stroke="{col}" stroke-width="4"/><path d="M8 22 L32 38 L56 22" fill="none" stroke="{col}" stroke-width="4"/><circle cx="50" cy="14" r="9" fill="{RED}"/>',
        "store": f'<ellipse cx="32" cy="14" rx="22" ry="7" fill="none" stroke="{col}" stroke-width="4"/><path d="M10 14 V48 Q32 60 54 48 V14" fill="none" stroke="{col}" stroke-width="4"/><path d="M10 31 Q32 43 54 31" fill="none" stroke="{col}" stroke-width="4"/>',
        "atom": f'<ellipse cx="32" cy="32" rx="26" ry="10" fill="none" stroke="{col}" stroke-width="4"/><ellipse cx="32" cy="32" rx="26" ry="10" fill="none" stroke="{col}" stroke-width="4" transform="rotate(60 32 32)"/><ellipse cx="32" cy="32" rx="26" ry="10" fill="none" stroke="{col}" stroke-width="4" transform="rotate(-60 32 32)"/><circle cx="32" cy="32" r="5" fill="{RED}"/>',
        "lock_open": f'<rect x="12" y="28" width="40" height="30" rx="5" fill="{col}"/><path d="M20 28 V18 A12 12 0 0 1 44 18 V12" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"/>',
        "box": f'<rect x="8" y="22" width="48" height="34" rx="3" fill="none" stroke="{col}" stroke-width="4"/><path d="M8 22 L32 10 L56 22" fill="none" stroke="{col}" stroke-width="4"/><rect x="26" y="32" width="12" height="14" rx="2" fill="{RED}"/>',
        "key": f'<circle cx="20" cy="32" r="11" fill="none" stroke="{col}" stroke-width="5"/><path d="M31 32 H58 M50 32 V42 M42 32 V40" stroke="{col}" stroke-width="5" stroke-linecap="round"/>',
    }[name]
    return f'<svg viewBox="0 0 64 64" style="width:{size}in;height:{size}in" aria-hidden="true">{p}</svg>'


# ---------------------------------------------------------------- html
def build_html():
    css = f"""
@page {{ size: 48in 36in; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 48in; height: 36in; background: #FFFFFF; }}
body {{ font-family: Arial, Helvetica, sans-serif; color: {INK};
        font-size: 28.5pt; line-height: 1.32; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.poster {{ position: relative; width: 48in; height: 36in; overflow: hidden; }}

/* header */
header {{ position: absolute; left: 0; top: 0; width: 48in; height: 6.35in; background: {RED};
          display: flex; align-items: center; padding: 0 0.9in 0 0.75in; gap: 0.6in; color: #fff; }}
.seal {{ flex: 0 0 5.3in; height: 5.3in; border-radius: 50%; background: #fff; display: flex;
         align-items: center; justify-content: center; }}
.seal img {{ width: 5.0in; height: 5.0in; }}
.titles {{ flex: 1; }}
.titles h1 {{ font-size: 104pt; line-height: 1.0; font-weight: 700; }}
.titles .sub {{ font-size: 50pt; font-weight: 400; margin-top: 0.16in; line-height: 1.12; }}
.titles .name {{ font-size: 68pt; font-weight: 700; margin-top: 0.34in; line-height: 1.0; letter-spacing: 0.3pt; }}
.titles .by {{ font-size: 38pt; margin-top: 0.16in; font-weight: 400; opacity: 0.96; }}
.titles .by b {{ font-weight: 700; }}
.lockup {{ flex: 0 0 7.4in; display: flex; justify-content: flex-end; }}
.lockup img {{ width: 7.4in; }}
.band {{ position: absolute; top: 6.35in; left: 0; width: 48in; height: 0.27in; background: {RULE}; }}

/* body grid */
main {{ position: absolute; top: 7.05in; left: 0.75in; right: 0.75in; bottom: 3.42in;
        display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; column-gap: 0.9in; }}
.col {{ position: relative; display: flex; flex-direction: column; gap: 0.32in; }}
.nw {{ white-space: nowrap; }}
.voice {{ font-size: 25pt; line-height: 1.32; }}
.voice p + p {{ margin-top: 0.12in; }}
.col + .col::before {{ content: ""; position: absolute; left: -0.45in; top: 0.1in; bottom: 0;
                       width: 2pt; background: {RULE}; }}
h2 {{ font-size: 60pt; line-height: 1.0; color: {RED}; font-weight: 700;
      margin-bottom: 0.16in; }}
h3 {{ font-size: 31pt; color: {INK}; font-weight: 700; margin-bottom: 0.08in; }}
p + p {{ margin-top: 0.14in; }}
b, strong {{ font-weight: 700; }}
.lead {{ font-size: 34pt; line-height: 1.26; }}
.small {{ font-size: 23.5pt; line-height: 1.3; color: {INK2}; }}
.cite {{ color: {MUTED}; font-size: 0.8em; }}
.red {{ color: {RED}; }}

/* hand-made components */
.steps {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.22in; margin-top: 0.12in; }}
.step {{ background: {TINT}; border-radius: 0.04in; padding: 0.22in 0.2in 0.24in; text-align: center; }}
.step .k {{ font-size: 25pt; font-weight: 700; color: {RED}; }}
.step .d {{ font-size: 23pt; line-height: 1.22; margin-top: 0.06in; }}
.step svg {{ display: block; margin: 0.08in auto 0; }}

.mosca {{ border: 3pt solid {INK}; border-radius: 0.04in; padding: 0.26in 0.32in 0.28in; }}
.eq {{ display: flex; align-items: center; justify-content: center; gap: 0.16in; margin: 0.14in 0 0.12in; }}
.eq .term {{ text-align: center; }}
.eq .v {{ font-size: 68pt; font-weight: 700; line-height: 1; }}
.eq .l {{ font-size: 21pt; line-height: 1.15; color: {INK2}; margin-top: 0.06in; width: 2.75in; }}
.eq .op {{ font-size: 54pt; font-weight: 400; color: {MUTED}; padding-bottom: 0.45in; }}

.rq {{ background: {INK}; color: #fff; border-radius: 0.04in; padding: 0.32in 0.36in 0.36in; }}
.rq h3 {{ color: #fff; }}
.rq p {{ font-size: 32pt; line-height: 1.26; font-weight: 400; font-style: italic; }}

.eqs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.22in; margin-top: 0.14in; }}
.eqbox {{ background: {TINT}; border-radius: 0.04in; padding: 0.2in 0.24in; }}
.eqbox .k {{ font-size: 24pt; font-weight: 700; color: {INK2}; }}
.eqbox .m {{ font-family: "Times New Roman", Times, serif; font-size: 34pt; line-height: 1.35; margin: 0.06in 0; }}
.eqbox .r {{ font-size: 23pt; font-weight: 700; }}

.flow {{ display: flex; flex-direction: column; gap: 0.16in; margin-top: 0.1in; }}
.fstep {{ display: grid; grid-template-columns: 1.3in 1fr; gap: 0.24in; align-items: center; }}
.fstep .ic {{ width: 1.3in; height: 1.3in; border-radius: 50%; background: {TINT};
              display: flex; align-items: center; justify-content: center; }}
.fstep .tx {{ font-size: 26.5pt; line-height: 1.26; }}
.fstep .tx b.n {{ color: {RED}; }}

.hybrid {{ display: flex; align-items: center; gap: 0.16in; margin: 0.12in 0 0.1in; }}
.chip {{ border-radius: 0.04in; padding: 0.14in 0.24in; font-size: 24.5pt; font-weight: 700; color: #fff; text-align: center; line-height: 1.15; }}
.plus {{ font-size: 40pt; color: {MUTED}; font-weight: 400; }}

.layers {{ display: flex; flex-direction: column; gap: 0.1in; margin-top: 0.12in; }}
.layer {{ display: grid; grid-template-columns: 2.9in 1fr; border-radius: 0.04in; overflow: hidden; align-items: stretch; }}
.layer .nm {{ background: {INK2}; color: #fff; font-weight: 700; font-size: 26pt; padding: 0.16in 0.2in; line-height: 1.12; display: flex; align-items: center; }}
.layer .nm span {{ display: block; font-weight: 400; font-size: 20pt; opacity: 0.9; margin-top: 0.04in; }}
.layer .ct {{ background: {TINT}; font-size: 23.5pt; padding: 0.16in 0.22in; line-height: 1.25; }}
.layer .ct i {{ color: {INK2}; }}
.layer.crypto .nm {{ background: {RED}; }}

.stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.2in; }}
.stat {{ border-top: 6pt solid {INK}; padding-top: 0.1in; }}
.stat .v {{ font-size: 68pt; font-weight: 700; line-height: 1.0; }}
.stat .l {{ font-size: 22.5pt; line-height: 1.22; margin-top: 0.06in; }}
.stat .s {{ font-size: 21pt; color: {MUTED}; margin-top: 0.04in; }}
.stat.good {{ border-top-color: {C['ECC']}; }}
.stat.cost {{ border-top-color: {C['RSA']}; }}

.figcap {{ font-size: 23pt; font-weight: 700; color: {INK2}; margin: 0.06in 0 0.04in; }}
.figcap span {{ font-weight: 400; color: {MUTED}; }}

.callout {{ border-left: 8pt solid {RED}; padding: 0.04in 0 0.04in 0.26in; font-size: 27pt; line-height: 1.28; }}

.road {{ display: flex; flex-direction: column; gap: 0; margin-top: 0.08in; }}
.phase {{ display: grid; grid-template-columns: 0.95in 1fr; gap: 0.22in; position: relative; padding-bottom: 0.2in; }}
.phase::before {{ content: ""; position: absolute; left: 0.455in; top: 0.8in; bottom: 0; width: 3pt; background: {RULE}; }}
.phase:last-child::before {{ display: none; }}
.phase:last-child {{ padding-bottom: 0; }}
.phase .num {{ width: 0.95in; height: 0.95in; border-radius: 50%; background: {INK}; color: #fff;
               font-size: 34pt; font-weight: 700; display: flex; align-items: center; justify-content: center; }}
.phase.hot .num {{ background: {RED}; }}
.phase .pt {{ font-size: 27pt; font-weight: 700; line-height: 1.15; padding-top: 0.06in; }}
.phase .pd {{ font-size: 23pt; line-height: 1.25; margin-top: 0.03in; }}
.phase .gate {{ font-size: 21pt; color: {RED}; font-weight: 700; margin-top: 0.04in; }}

.take {{ background: {RED}; color: #fff; border-radius: 0.04in; padding: 0.3in 0.36in 0.34in; }}
.take h3 {{ color: #fff; }}
.take p {{ font-size: 28pt; line-height: 1.28; font-weight: 400; }}

.gloss {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.16in 0.34in; margin-top: 0.06in; }}
.gloss div {{ font-size: 25pt; line-height: 1.26; }}
.gloss b {{ color: {RED}; }}

footer {{ position: absolute; left: 0.75in; right: 0.75in; bottom: 0.45in; height: 2.72in;
          border-top: 3pt solid {RULE}; padding-top: 0.16in; display: grid;
          grid-template-columns: 9.2in 1fr; column-gap: 0.7in; }}
footer h3 {{ font-size: 24pt; color: {RED}; margin-bottom: 0.06in; }}
footer .ack {{ font-size: 21pt; line-height: 1.3; }}
footer ol {{ columns: 3; column-gap: 0.5in; column-fill: balance; font-size: 19pt; line-height: 1.18; color: {INK}; padding-left: 0.4in; }}
footer li {{ break-inside: avoid; margin-bottom: 0.04in; padding-left: 0.04in; }}
"""

    lat = lattice_svg()

    col1 = f"""
<section>
  <h2>Introduction</h2>
  <p class="lead">Public-key cryptography is one of the quiet assumptions behind almost every modern system. Online banking, messaging, software updates, and logins all rely on <b>RSA</b> and <b>elliptic-curve cryptography (ECC)</b>.</p>
  <p style="margin-top:0.18in">RSA is secure because factoring very large numbers is slow, and ECC relies on a related hard problem. A large enough quantum computer running Shor’s algorithm could solve both <span class="cite">[1]</span>. RSA and ECC are not broken today, but their security margin is not future-proof.</p>
</section>

<section>
  <h3>Harvest Now, Decrypt Later</h3>
  <div class="steps">
    <div class="step"><div class="k">Today</div>{icon("record")}<div class="d">Encrypted traffic is recorded</div></div>
    <div class="step"><div class="k">Stored</div>{icon("store")}<div class="d">The data is kept for years</div></div>
    <div class="step"><div class="k">Later</div>{icon("atom")}<div class="d">A quantum computer decrypts it</div></div>
  </div>
  <p class="small" style="margin-top:0.16in">Health, legal, financial, and government records need to stay private for decades, so they are at risk before the hardware even exists.</p>
</section>

<section class="mosca">
  <h3 style="text-align:center">Mosca’s Inequality</h3>
  <div class="eq">
    <div class="term"><div class="v">X</div><div class="l">years the data must stay secret</div></div>
    <div class="op">+</div>
    <div class="term"><div class="v">Y</div><div class="l">years it takes to migrate</div></div>
    <div class="op">&gt;</div>
    <div class="term"><div class="v red">Z</div><div class="l">years until a quantum break</div></div>
  </div>
  <p class="small" style="text-align:center">If this is true, the data is already at risk <span class="cite">[2]</span>. Breaking RSA-2048 is still estimated to need millions of qubits <span class="cite">[3]</span>, but waiting for an exact date is a poor plan.</p>
</section>

<section class="rq">
  <h3>Research Question</h3>
  <p>How can NIST-selected post-quantum algorithms be integrated into real application workflows while keeping performance and deployment risk manageable?</p>
</section>

<section class="voice">
  <h3>Motivation</h3>
  <p>I chose this topic after exploring current technology problems that felt both important and genuinely interesting to me. I wanted something that blended math and computer science, and post-quantum cryptography stood out because it has both deep theory and real-world urgency.</p>
  <p>The biggest thing I learned is that adoption is not as simple as picking a new algorithm and replacing the old one.</p>
</section>
"""

    col2 = f"""
<section>
  <h2>Background</h2>
  <p>In 2024, NIST published two post-quantum standards: <b>ML-KEM</b> (FIPS 203) for establishing shared keys <span class="cite">[4]</span> and <b>ML-DSA</b> (FIPS 204) for digital signatures <span class="cite">[5]</span>. Both are based on <b>lattices</b>.</p>
</section>

<section>
  <h3>Lattice Problems</h3>
  <div style="display:grid;grid-template-columns:5.5in 1fr;gap:0.28in;align-items:center;margin-top:0.08in">
    <div>{lat}</div>
    <p style="font-size:24pt;line-height:1.28">Imagine being dropped into a city with millions of nearly identical streets and asked to find one tiny shortcut using noisy map coordinates. In 2D this is manageable. In hundreds of dimensions (ML-KEM-512 uses 512), it becomes computationally hard.</p>
  </div>
</section>

<section>
  <h3>Learning With Errors</h3>
  <div class="eqs">
    <div class="eqbox"><div class="k">Without noise</div><div class="m">3<i>x</i> + 2<i>y</i> = 12<br><i>x</i> + 4<i>y</i> = 14</div><div class="r">Solution: <i>x</i> = 2, <i>y</i> = 3</div></div>
    <div class="eqbox"><div class="k">With small errors</div><div class="m">3<i>x</i> + 2<i>y</i> ≈ 13<br><i>x</i> + 4<i>y</i> ≈ 13</div><div class="r red">No exact solution</div></div>
  </div>
  <p style="margin-top:0.16in">Each equation has a small random error added. Without the errors the system is easy to solve, but with them, recovering the hidden values becomes hard in high dimensions <span class="cite">[6]</span>.</p>
</section>

<section>
  <h3>ML-KEM Key Exchange</h3>
  <div class="flow">
    <div class="fstep"><div class="ic">{icon("lock_open", 0.85)}</div><div class="tx"><b class="n">1. Key generation.</b> The receiver creates a public key (like an open padlock) and a private key.</div></div>
    <div class="fstep"><div class="ic">{icon("box", 0.85)}</div><div class="tx"><b class="n">2. Encapsulation.</b> The sender uses the public key to lock up a random shared secret and sends it.</div></div>
    <div class="fstep"><div class="ic">{icon("key", 0.85)}</div><div class="tx"><b class="n">3. Decapsulation.</b> The receiver uses the private key to recover the same secret.</div></div>
  </div>
</section>

<section>
  <h3>Hybrid Key Exchange</h3>
  <div class="hybrid">
    <div class="chip" style="background:{C['ECC']}">ECDH secret</div><div class="plus">+</div>
    <div class="chip" style="background:{C['ML-KEM']}">ML-KEM secret</div><div class="plus">→</div>
    <div class="chip" style="background:{C['HYBRID']}">session key</div>
  </div>
  <p>The hybrid mode derives the session key from both a classical and a post-quantum secret, so security does not rely on only one assumption.</p>
</section>

<section>
  <h3>Key Terms</h3>
  <div class="gloss">
    <div><b>Handshake:</b> the setup step where two devices agree on a secret before sending data.</div>
    <div><b>Signature:</b> proof that data came from the claimed sender and was not modified.</div>
    <div><b>Latency:</b> time for one operation (lower is better).</div>
    <div><b>Throughput:</b> work completed per second (higher is better).</div>
  </div>
</section>
"""

    col3 = f"""
<section>
  <h2>Methods</h2>
  <p>I built a Python benchmarking framework that runs the same tests with <b>RSA-2048, ECC (P-256), ML-KEM-512, ML-DSA-44,</b> and a <b>hybrid ECC + ML-KEM</b> handshake. Each benchmark was repeated 1,000 times.</p>
  <div class="layers">
    <div class="layer"><div class="nm">Workload layer</div><div class="ct">Messaging sessions, file transfer, and TLS-style handshakes</div></div>
    <div class="layer"><div class="nm">Benchmark layer</div><div class="ct">Latency, throughput, bytes sent, and memory, exported to CSV</div></div>
    <div class="layer crypto"><div class="nm">Crypto layer</div><div class="ct">One shared interface, so algorithms can be swapped without rewriting the application</div></div>
  </div>
  <p class="small" style="margin-top:0.14in">Keeping the layers separate made it possible to test each algorithm without changing the workload code, which is a practical example of crypto-agility.</p>
</section>

<section>
  <h2>Results: Key Exchange</h2>
  <div class="stats">
    <div class="stat good"><div class="v">{kem_speedup:.1f}×</div><div class="l">faster handshake (ML-KEM vs. ECDH)</div></div>
    <div class="stat cost"><div class="v">{kem_bytes_x:.1f}×</div><div class="l">more bytes sent (ML-KEM vs. ECDH)</div></div>
    <div class="stat cost"><div class="v">{rsa_x:.0f}×</div><div class="l">slower (RSA vs. ECDH, new key each time)</div></div>
  </div>
  <div class="figcap" style="margin-top:0.24in">Figure 1. Time per handshake <span>(lower is better)</span></div>
  {chart_handshake_time()}
  <div class="figcap" style="margin-top:0.12in">Figure 2. Bytes sent per handshake <span>(lower is better)</span></div>
  {chart_handshake_bytes()}
  <p class="callout" style="margin-top:0.16in">If classical handshakes are like sending a short postcard, post-quantum handshakes are like sending a padded envelope. One envelope is fine, but millions per day change cost and latency, especially on mobile and edge networks <span class="cite">[8]</span>.</p>
</section>

<section>
  <h3>Limitations</h3>
  <p class="small">All tests ran on one machine without a real network and used a simplified message cipher, so the results compare algorithms rather than predict a live system. Future work includes network emulation, AES-GCM, ML-KEM-768, and hardware accelerators <span class="cite">[9]</span>.</p>
</section>
"""

    col4 = f"""
<section>
  <h2>Results: Workloads</h2>
  <p>With session reuse, post-quantum handshakes took <b>less than 1%</b> of total messaging time, while RSA handshakes took <b>{msg_share['RSA']:.0f}%</b>.</p>
  <div class="figcap" style="margin-top:0.14in">Figure 3. Share of messaging time spent on handshakes <span>(1,000 sessions)</span></div>
  {chart_session_share()}
  <p class="small" style="margin-top:0.08in">File transfer throughput was about {statistics.mean(ft_tput.values()):.0f} Mbps for every algorithm. The {ft_spread:.1f} Mbps spread was smaller than the normal run-to-run variation.</p>
</section>

<section>
  <h3>Signatures (ML-DSA vs. ECDSA)</h3>
  <div class="stats" style="margin-top:0.1in">
    <div class="stat good"><div class="v">{verify_ratio:.1f}×</div><div class="l">verification time (about the same)</div></div>
    <div class="stat cost"><div class="v">{sign_x:.1f}×</div><div class="l">slower signing</div></div>
    <div class="stat cost"><div class="v">{size_x:.0f}×</div><div class="l">larger signatures</div><div class="s">{sig['size'][0]:.0f} B → {sig['size'][1]:,.0f} B</div></div>
  </div>
  <p class="small" style="margin-top:0.14in">Verifying an ML-DSA signature costs about the same as ECDSA. The main cost is size, which affects certificates, storage, and bandwidth.</p>
</section>

<section>
  <h2>Migration Roadmap</h2>
  <div class="road">
    <div class="phase"><div class="num">0</div><div><div class="pt">Inventory and baseline</div><div class="pd">Map where RSA and ECC are used and record current metrics.</div><div class="gate">Gate: baseline data is complete and reproducible</div></div></div>
    <div class="phase"><div class="num">1</div><div><div class="pt">Crypto-agility refactor</div><div class="pd">Make algorithms swappable at the interface level.</div><div class="gate">Gate: swaps need no application rewrites</div></div></div>
    <div class="phase hot"><div class="num">2</div><div><div class="pt">Targeted hybrid deployment</div><div class="pd">Use hybrid first on long-lived, high-value channels.</div><div class="gate">Gate: error rates and latency stay in budget</div></div></div>
    <div class="phase hot"><div class="num">3</div><div><div class="pt">Post-quantum preferred</div><div class="pd">Default to post-quantum where support is stable, with a fallback.</div><div class="gate">Gate: stable and interoperable in production</div></div></div>
    <div class="phase"><div class="num">4</div><div><div class="pt">Governance and re-testing</div><div class="pd">Enforce crypto policy in CI/CD and re-benchmark over time.</div></div></div>
  </div>
</section>

<section class="take">
  <h3>Conclusion</h3>
  <p>Post-quantum algorithms are already fast enough for real systems. The main costs are larger messages and the engineering work of migrating safely, so the transition should be treated as a systems engineering program, not only a cryptographic substitution task.</p>
</section>
"""

    footer = """
<footer>
  <div>
    <h3>Acknowledgements</h3>
    <p class="ack">I would like to thank my Honors Thesis advisor, <b>Dr. Joseph Kirtland</b>, for his continuous support on this project, from explaining the core mathematical theory to helping me shape and refine the paper direction.</p>
  </div>
  <div>
    <h3>References</h3>
    <ol>
      <li>P. W. Shor, “Algorithms for quantum computation: discrete logarithms and factoring,” <i>Proc. 35th FOCS</i>, IEEE, 1994.</li>
      <li>M. Mosca, “Cybersecurity in an era with quantum computers: Will we be ready?” <i>IEEE Security &amp; Privacy</i>, 2018.</li>
      <li>C. Gidney and M. Ekerå, “How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits,” <i>Quantum</i>, 2021.</li>
      <li>NIST, <i>FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard</i>, 2024.</li>
      <li>NIST, <i>FIPS 204: Module-Lattice-Based Digital Signature Standard</i>, 2024.</li>
      <li>G. Chhetri et al., “Post-quantum cryptography and quantum-safe security: A comprehensive survey,” arXiv:2510.10436, 2025.</li>
      <li>M. Abbasi et al., “A practical performance benchmark of post-quantum cryptography across heterogeneous computing environments,” <i>Cryptography</i>, 2025.</li>
      <li>O. Alnaseri et al., “Complexity of post-quantum cryptography in embedded systems and its optimization strategies,” <i>IWCMC</i>, IEEE, 2025.</li>
      <li>H. Yan et al., “Lattice-based cryptographic accelerators for the post-quantum era,” <i>Electronics</i>, 2026.</li>
    </ol>
  </div>
</footer>
"""

    header = """
<header>
  <div class="seal"><img src="assets/honors_seal.png" alt="Marist University Honors Program seal"></div>
  <div class="titles">
    <h1>Post-Quantum Cryptography in Practice</h1>
    <div class="sub">Benchmarking, Protocol Integration, and Migration Strategy for Real Systems</div>
    <div class="name">Michael Kurilko</div>
    <div class="by">Thesis Mentor: Dr. Joseph Kirtland &nbsp;|&nbsp; Marist University Honors Program</div>
  </div>
  <div class="lockup"><img src="assets/marist_honors_white.png" alt="Marist University Honors Program"></div>
</header>
<div class="band"></div>
"""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>PQC Honors Thesis Poster</title>
<style>{css}</style></head>
<body><div class="poster">
{header}
<main>
  <div class="col">{nowrap(col1)}</div>
  <div class="col">{nowrap(col2)}</div>
  <div class="col">{nowrap(col3)}</div>
  <div class="col">{nowrap(col4)}</div>
</main>
{footer}
</div>
<script>
addEventListener("load", () => {{
  const r = [];
  document.querySelectorAll(".col").forEach((c, i) => {{
    let m = 0;
    c.querySelectorAll(":scope > section").forEach(s => m = Math.max(m, s.getBoundingClientRect().bottom));
    r.push("col" + (i + 1) + "=" + ((document.querySelector("main").getBoundingClientRect().bottom - m) / 96).toFixed(2));
  }});
  const f = document.querySelector("footer");
  let fm = 0;
  f.querySelectorAll("li, p").forEach(e => fm = Math.max(fm, e.getBoundingClientRect().bottom));
  r.push("footer=" + ((f.getBoundingClientRect().bottom - fm) / 96).toFixed(2));
  const ol = f.querySelector("ol");
  r.push("refs_spill=" + (ol.scrollWidth - ol.clientWidth));
  const h = document.querySelector(".titles");
  r.push("titles_w=" + (h.scrollWidth - h.clientWidth));
  document.body.setAttribute("data-fit", r.join(" "));
}});
</script>
</body></html>"""


def nowrap(html):
    """Keep algorithm names like ML-KEM from breaking at the hyphen (text only, not SVG)."""
    import re
    parts = re.split(r"(<svg.*?</svg>)", html, flags=re.S)
    pat = re.compile(r"(ML-KEM-512|ML-DSA-44|ML-KEM|ML-DSA|RSA-2048|ECC \(P-256\)|CI/CD)")
    return "".join(p if p.startswith("<svg") else pat.sub(r'<span class="nw">\1</span>', p) for p in parts)


def main():
    html = HERE / "poster.html"
    pdf = HERE / "Kurilko_Honors_Thesis_Poster.pdf"
    html.write_text(build_html(), encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000",
                    f"--print-to-pdf={pdf}", html.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
                          "--dump-dom", html.as_uri()], capture_output=True, text=True).stdout
    import re
    fit = re.search(r'data-fit="([^"]*)"', dom)
    print(f"wrote {html}\nwrote {pdf}")
    print("free space in inches (negative = overflow):", fit.group(1) if fit else "n/a")


if __name__ == "__main__":
    main()
