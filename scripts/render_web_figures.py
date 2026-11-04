"""Draw the project's web diagrams and scientific plots from release data.

Optional authoring dependency: matplotlib. The execution core stays stdlib-only.
The hero is a conceptual terrain illustration, not a reconstructed dataset scene.
"""

import base64
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/site/assets"
INK, MUTED, LINE, ORANGE = "#1b1c1e", "#7a7b80", "#dedee1", "#f26a37"
FONT = "Arial, Helvetica, sans-serif"


def svg_open(width, height, background="white"):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="{background}"/>']


def text(parts, x, y, label, size=20, color=INK, weight=400, anchor="start", extra=""):
    parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{html.escape(label)}</text>')


def line(parts, x1, y1, x2, y2, color=LINE, width=1, extra=""):
    parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" {extra}/>')


def rect(parts, x, y, width, height, fill="white", stroke=LINE, radius=0, extra=""):
    parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" rx="{radius}" {extra}/>')


def path(parts, points, color=INK, width=1, extra=""):
    parts.append(f'<polyline points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')


def save(parts, name):
    (ASSETS / name).write_text("\n".join(parts) + "\n</svg>\n", encoding="utf-8", newline="\n")


def hero():
    width, height = 1440, 470
    p = svg_open(width, height, "#111214")
    p += ['<defs><linearGradient id="edge"><stop stop-color="#111214"/><stop offset=".25" stop-color="#111214" stop-opacity="0"/><stop offset=".75" stop-color="#111214" stop-opacity="0"/><stop offset="1" stop-color="#111214"/></linearGradient>',
          '<radialGradient id="spot"><stop stop-color="#25282b" stop-opacity=".6"/><stop offset="1" stop-color="#111214" stop-opacity="0"/></radialGradient></defs>',
          '<ellipse cx="820" cy="250" rx="700" ry="300" fill="url(#spot)"/>']

    def surface(x, y):
        # A deliberately schematic valley with a smooth, readable central route.
        return 0.1 + 0.64 * math.exp(-((x - 3.3) ** 2 / 3.3 + (y - 2.0) ** 2 / 24)) + \
            0.53 * math.exp(-((x + 3.5) ** 2 / 3 + (y + 1.3) ** 2 / 20)) + \
            0.20 * math.sin(y * 0.8 + x * 0.4) + 0.09 * math.cos(1.25 * x - 0.6 * y)

    def project(x, y, z):
        return (width / 2 + x * 79 + y * 45, height / 2 + y * 20 - x * 10 - z * 126)

    for j in range(43):
        x = -6 + j * 12 / 42
        points = [project(x, -7 + i * 14 / 120, surface(x, -7 + i * 14 / 120)) for i in range(121)]
        path(p, points, "#73767b", .65, 'opacity=".35"')
    for j in range(50):
        y = -7 + j * 14 / 49
        points = [project(-6 + i * 12 / 100, y, surface(-6 + i * 12 / 100, y)) for i in range(101)]
        path(p, points, "#8d9095", .7, 'opacity=".3"')
    for i in range(0, 43, 3):
        x = -6 + i * 12 / 42
        for j in range(0, 50, 4):
            y = -7 + j * 14 / 49
            a, b = project(x, y, surface(x, y))
            p.append(f'<circle cx="{a:.2f}" cy="{b:.2f}" r="1.1" fill="#9c9fa4" opacity=".5"/>')
    route = []
    old_route = []
    for i in range(141):
        y = 5.1 - i * 10.4 / 140
        x = 0.45 * math.sin(y * .56) - .4
        route.append(project(x, y, surface(x, y) + .06))
        old_route.append(project(x + .5 * max(0, (5 - y) / 10), y, surface(x, y) + .06))
    path(p, old_route, "#a2a5a9", 1.3, 'stroke-dasharray="4 8" opacity=".5"')
    path(p, route, ORANGE, 11, 'opacity=".08"')
    path(p, route, ORANGE, 2.8)
    for n, idx in enumerate([0, 28, 56, 84, 112, 140]):
        x, y = route[idx]
        p.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{5 if n == 0 else 4}" fill="{ORANGE}" stroke="#111214" stroke-width="2"/>')
    x, y = route[0]
    p.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="13" fill="none" stroke="{ORANGE}" opacity=".6"/>')
    line(p, x + 16, y, x + 105, y, "#777b81")
    text(p, x + 115, y + 4, "CURRENT STATE", 11, "#aaaeb5", extra='letter-spacing="2"')
    x, y = route[-1]
    line(p, x + 7, y - 10, x + 46, y - 45, ORANGE)
    text(p, x + 55, y - 48, "STATE-ALIGNED PLAN", 11, ORANGE, extra='letter-spacing="2"')
    p.append(f'<rect width="{width}" height="{height}" fill="url(#edge)"/>')
    text(p, 45, 46, "PERSISTENT STATE / SPARSE INFERENCE", 10, "#8d9096", extra='letter-spacing="2"')
    line(p, 44, 67, 205, 67, "#414349")
    text(p, 45, 423, "CONCEPTUAL TERRAIN STUDY", 9, "#65686f", extra='letter-spacing="1.8"')
    text(p, 1395, 423, "SPEED × CURVATURE", 9, "#65686f", anchor="end", extra='letter-spacing="1.8"')
    save(p, "terrain-study.svg")


def framework():
    p = svg_open(1440, 575, "#fafafa")
    p += ['<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 10 5 0 10" fill="none" stroke="#a2a3a6" stroke-width="1.3"/></marker><marker id="orange-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 10 5 0 10" fill="none" stroke="#f26a37" stroke-width="1.3"/></marker></defs>']
    text(p, 42, 44, "01  /  VISUAL PLAN GENERATION", 11, MUTED, extra='letter-spacing="1.5"')
    text(p, 532, 44, "02  /  RECURRENT EXECUTION", 11, ORANGE, extra='letter-spacing="1.5"')
    line(p, 490, 28, 490, 490, "#e0e0e3", extra='stroke-dasharray="4 6"')
    # Input observation: line art, no pasted low-resolution paper graphics.
    rect(p, 43, 150, 123, 98, "#f0f0f1", "#dadade", 3)
    path(p, [(55, 225), (85, 190), (106, 206), (137, 171), (155, 188)], "#b7b8be", 1.5)
    path(p, [(64, 225), (104, 225), (137, 183)], "#74777e", 2)
    text(p, 104, 276, "Image, state, instruction", 14, MUTED, anchor="middle")
    line(p, 181, 199, 218, 199, "#a2a3a6", 1.5, 'marker-end="url(#arrow)"')
    rect(p, 235, 126, 207, 148, "#1b1c1e", "#1b1c1e", 4)
    # A restrained icon for frozen computation, drawn as geometry.
    for angle in [0, math.pi/3, 2*math.pi/3]:
        dx, dy = math.cos(angle)*10, math.sin(angle)*10
        line(p, 339-dx, 158-dy, 339+dx, 158+dy, "#d7d7db", 1)
    text(p, 338, 205, "Frozen VLA", 26, "white", 500, "middle")
    text(p, 338, 234, "Decode on refresh", 13, "#b3b4bb", anchor="middle")
    line(p, 442, 199, 534, 199, "#a2a3a6", 1.5, 'marker-end="url(#arrow)"')
    # Six-slot action buffer. One accent, no pastel box taxonomy.
    text(p, 550, 125, "ACTION BUFFER", 11, MUTED, extra='letter-spacing="1.4"')
    for i in range(6):
        x = 550 + i*45
        rect(p, x, 151, 37, 96, "#f6f6f7" if i else "#fff3ed", "#d9d9dd" if i else ORANGE, 2)
        line(p, x+10, 188, x+27, 188, ORANGE if i == 0 else "#85878e", 3)
        line(p, x+10, 205, x+27, 205, ORANGE if i == 0 else "#85878e", 3)
    text(p, 682, 276, "Speed–curvature actions", 15, MUTED, anchor="middle")
    line(p, 829, 199, 867, 199, "#a2a3a6", 1.5, 'marker-end="url(#arrow)"')
    rect(p, 883, 137, 222, 124, "#fff", ORANGE, 4)
    text(p, 994, 188, "State alignment", 23, INK, 500, "middle")
    text(p, 994, 223, "Blend · speed bound", 13, MUTED, anchor="middle")
    line(p, 994, 339, 994, 279, "#8c8e94", 1.3, 'marker-end="url(#arrow)"')
    text(p, 994, 365, "Measured motion", 15, INK, 500, "middle")
    text(p, 994, 389, "vₜ  ·  κₜ", 15, MUTED, anchor="middle")
    line(p, 1106, 199, 1150, 199, "#a2a3a6", 1.5, 'marker-end="url(#arrow)"')
    # Integrated trajectory; schematic curve with exactly six action endpoints.
    line(p, 1175, 263, 1359, 263, "#dadade")
    line(p, 1175, 263, 1175, 120, "#dadade")
    points=[(1175,263),(1202,253),(1230,238),(1253,216),(1273,187),(1291,153),(1302,119)]
    path(p, points, ORANGE, 2.5)
    for x,y in points[1:]: p.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{ORANGE}"/>')
    text(p, 1270, 302, "Local trajectory", 17, INK, 500, "middle")
    text(p, 1270, 328, "6 waypoints · 3 seconds", 13, MUTED, anchor="middle")
    # Persistence loop explicitly returns a corrected tail, not a new visual plan.
    p.append(f'<path d="M1090 261 V434 H682 V284" fill="none" stroke="{ORANGE}" stroke-width="1.7" marker-end="url(#orange-arrow)"/>')
    rect(p, 735, 415, 230, 36, "#fafafa", "none")
    text(p, 850, 438, "Consume → write back", 17, ORANGE, 500, "middle")
    text(p, 850, 478, "Retain the corrected remainder", 13, MUTED, anchor="middle")
    # Budgeted refresh is a separate control path; this is not an async claim.
    line(p, 42, 521, 1398, 521)
    text(p, 43, 552, "REFRESH RULE", 10, MUTED, extra='letter-spacing="1.2"')
    text(p, 211, 553, "Plan roughness → bounded reuse budget → request a fresh plan", 15, INK)
    text(p, 1396, 553, "TRAINING-FREE", 10, MUTED, anchor="end", extra='letter-spacing="1.2"')
    save(p, "framework-web.svg")


def refresh_diagram():
    p = svg_open(1040, 365, "#fafafa")
    text(p, 40, 42, "ONE DECISION AT REFRESH", 11, MUTED, extra='letter-spacing="1.5"')
    text(p, 40, 99, "Plan variation", 25, INK, 500)
    # These signal shapes explain the mechanism; they are explicitly schematic.
    path(p, [(40+i*7, 154-11*math.sin(i*.8)-i*.18) for i in range(25)], "#8e9096", 1.8)
    path(p, [(40+i*7, 205-12*math.sin(i*.6+.4)) for i in range(25)], "#45474e", 1.8)
    text(p, 40, 251, "Speed + curvature differences", 13, MUTED)
    line(p, 240, 172, 283, 172, "#a2a3a6", 1.5)
    rect(p, 303, 124, 160, 98, "#fff", "#d4d4d9", 3)
    text(p, 383, 161, "Normalize", 19, INK, 500, "middle")
    text(p, 383, 193, "validation P90", 12, MUTED, anchor="middle")
    line(p, 463, 172, 506, 172, "#a2a3a6", 1.5)
    text(p, 526, 99, "Bounded reuse", 25, INK, 500)
    text(p, 526, 141, "HIGHER VARIATION", 10, MUTED, extra='letter-spacing="1.3"')
    text(p, 984, 141, "K = 8", 13, INK, 500, "end")
    text(p, 526, 229, "LOWER VARIATION", 10, MUTED, extra='letter-spacing="1.3"')
    text(p, 984, 229, "K = 24", 13, INK, 500, "end")
    for y,k in [(166,8),(254,24)]:
        for i in range(26):
            active = i % (k+1) == 0
            rect(p, 526+i*17.6, y, 10, 22, ORANGE if active else "#e0e0e4", "none", 1)
    rect(p, 526, 304, 8, 8, ORANGE, "none")
    text(p, 544, 313, "fresh plan", 11, MUTED)
    rect(p, 658, 304, 8, 8, "#dedee3", "none")
    text(p, 677, 313, "state-conditioned reuse", 11, MUTED)
    text(p, 40, 329, "Illustrative signals · RELLIS budget configuration", 11, MUTED)
    save(p, "refresh-web.svg")


def plot_results():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from fastrovervla.evaluation import load_config, load_rows, replay
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#d1d1d6", "xtick.color": "#787a80",
                         "ytick.color": "#787a80", "axes.labelcolor": "#787a80",
                         "svg.fonttype": "none", "axes.titleweight": "normal"})
    fig, axes = plt.subplots(1,2,figsize=(13.8,4.9))
    fig.patch.set_facecolor("#fafafa")
    for ax, ds, title in zip(axes,["orad","rellis"],["ORAD-3D","RELLIS-3D"]):
        ax.set_facecolor("#fafafa")
        cfg, rule=load_config(ROOT/f"configs/{ds}_qwen3.json")
        rows=load_rows(ROOT/f"data/benchmark/{ds}.jsonl")
        for mode,label,color,style,lw in [("every","Every update","#96989f","--",1.5),
                                           ("fixed","Fixed interval","#4b4e55","-",1.7),
                                           ("adaptive","FastRoverVLA",ORANGE,"-",2.5)]:
            _,rr=replay(rows,cfg,rule,mode=mode)
            x=np.sort([r['fde'] for r in rr]); y=np.arange(1,len(x)+1)/len(x)
            # ECDF is a step function. No KDE, smoothing or invented confidence band.
            ax.step(x,y,where="post",label=label,color=color,linestyle=style,lw=lw)
        ax.set_title(title,loc="left",fontsize=18,pad=19,color=INK)
        ax.set_xlim(0,2.5);ax.set_ylim(0,1.02)
        ax.set_xticks([0,.5,1,1.5,2,2.5]);ax.set_yticks([0,.25,.5,.75,1],['0%','25%','50%','75%','100%'])
        ax.tick_params(length=0,pad=9)
        ax.grid(axis='y',color='#e9e9ec',lw=.7,zorder=0)
        ax.set_xlabel("Final displacement error (m)",labelpad=16)
        ax.set_ylabel("Share of windows",labelpad=12)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=3,frameon=False,bbox_to_anchor=(.5,-.008),columnspacing=3,handlelength=2.5)
    fig.subplots_adjust(left=.065,right=.98,bottom=.23,top=.84,wspace=.27)
    fig.savefig(ASSETS/'error-profile.svg',facecolor=fig.get_facecolor(),metadata={'Title':'Empirical error distributions from frozen Qwen3 replay'})
    vector = ASSETS/'error-profile.svg'
    vector.write_text('\n'.join(line.rstrip() for line in vector.read_text(encoding='utf-8').splitlines())+'\n', encoding='utf-8', newline='\n')
    fig.savefig(ASSETS/'error-profile.png',dpi=160,facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    hero();framework();refresh_diagram();plot_results()
    print("Drew conceptual hero, method diagram, refresh diagram and measured error ECDFs")
