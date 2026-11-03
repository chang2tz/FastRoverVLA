# Numerical replay bundle

The two JSONL files contain author-exported decoded predictions, logged scalar motion
state, prepared local trajectory targets and reference outputs for 1,286 windows.
No raw camera/LiDAR records or backbone weights are included in this folder.

Each row includes `sequence_id`, `frame_index`, `observed_action`, `decoded_actions`,
`ground_truth`, `past_heading_ground_truth`, `reference_refresh`, `reference_actions`
and `reference_waypoints`. Action units are m/s and 1/m; positions are metres.
`reference_*` fields support verification and are never supplied to the runtime planner.
The `reference` replay mode intentionally uses fixed archived refresh flags for controls.

`ground_truth` preserves the archived quantitative benchmark convention.
`past_heading_ground_truth` stores the separate reference-frame sensitivity target;
see [evaluation protocol](../../docs/evaluation.md).

Source provenance and checksums are recorded in `provenance.json`. These are derived
research artifacts based on ORAD-3D and RELLIS-3D; original dataset terms still apply.
The code license does not relicense the upstream datasets or their imagery.
