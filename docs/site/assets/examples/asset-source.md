# Original manuscript example panels

These files are exact rectangular renders from **Figure 6** in the authors' original manuscript figure. They are not synthesized scenes or redrawn trajectories.

- Source: `figure/qualitative_execution.pdf (author source)`
- Source SHA-256: `8797dde47c8e7bcf181447a7c3758157040e8404816483123e3780bca96f498a`
- PDF page: 1; size: 515.52002 x 349.20001 points.
- Dataset: ORAD-3D; matched frozen Qwen3-VL predictions and logged-state, open-loop evaluation.
- FDE pairs below are **Every-update / FastRoverVLA**, in metres, copied from the figure labels.
- Camera crops preserve the complete original scene and its trajectory overlays. Camera title and FDE annotation are supplied as HTML metadata rather than included in the crop.
- BEV crops preserve the full original chart, including the BEV title, grid, ticks, axis labels, trajectory overlays and vehicle markers.
- Shared legend from the figure: Ground truth (green), Every-update (muted terracotta), FastRoverVLA (teal).
- Export: PyMuPDF clipped rendering, followed by WebP encoding at quality 95. Target widths are 1000 px (camera) and 650 px (BEV); no generative editing, new trajectory interpolation or drawing was performed. Integer pixel bounds can add one or two output pixels. The original embedded camera frames are 763 px wide; export size does not claim added photographic detail.
- Rectangles use PDF points `[x0, y0, x1, y1]`, origin at the upper-left corner.

| Panel | Camera rectangle | BEV rectangle | FDE (m) |
| --- | --- | --- | --- |
| (a) Rough straight | `[8.85, 31.35, 146.49, 108.69]` | `[149.1, 21.2, 247.2, 129.0]` | 0.88 / 0.06 |
| (b) Dirt trail | `[270.75, 31.35, 408.39, 108.69]` | `[411.1, 21.2, 508.8, 129.0]` | 0.64 / 0.06 |
| (c) Night turn | `[8.85, 139.35, 146.49, 216.87]` | `[149.1, 129.27, 247.2, 237.07]` | 0.63 / 0.35 |
| (d) Confined left | `[270.75, 139.35, 408.39, 216.87]` | `[411.1, 129.27, 508.8, 237.07]` | 0.82 / 0.48 |
| (e) Snowy right | `[8.85, 247.35, 146.49, 324.87]` | `[149.1, 237.34, 247.2, 345.14]` | 0.37 / 0.15 |
| (f) Woodland trail | `[270.75, 247.35, 408.39, 324.87]` | `[411.1, 237.34, 508.8, 345.14]` | 1.11 / 0.32 |

`metadata.json` records the exact output dimensions and SHA-256 checksums. Dataset imagery remains subject to the upstream dataset terms described in the repository's `THIRD_PARTY.md`.
