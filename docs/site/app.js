"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const state = {dataset: "rellis", cache: {}, rows: [], index: 0, timer: null};
  const palette = {grid: "#ececf0", label: "#a0a3ad", full: "#f26a37", stale: "#3e424d", gt: "#a6a9b2"};
  const ns = "http://www.w3.org/2000/svg";
  const draw = (tag, attrs, parent, text) => {
    const element = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    parent.append(element);
    return element;
  };
  function stop() {
    clearInterval(state.timer); state.timer = null;
    $("play-button").textContent = "▶";
    $("play-button").setAttribute("aria-label", "Play numerical replay");
  }
  function render() {
    const row = state.rows[state.index];
    if (!row) return;
    const svg = $("trajectory");
    svg.replaceChildren();
    draw("title", {id:"trajectory-title"}, svg, `Window ${row.frame_index}: local trajectory comparison`);
    draw("desc", {id:"trajectory-description"}, svg, "Ground truth, FastRoverVLA, and the matched-refresh control without correction during reuse. Distances are metres.");
    const paths = [row.gt, row.full, row.control];
    const points = paths.flat().concat([[0, 0]]);
    const maxX = Math.max(1, ...points.map(p => p[0])) * 1.12;
    const minX = Math.min(0, ...points.map(p => p[0]));
    const spanY = Math.max(0.45, ...points.map(p => Math.abs(p[1]))) * 1.4;
    const left = 57, top = 32, width = 620, height = 328;
    const px = x => left + (x - minX) / (maxX - minX) * width;
    const py = y => top + height / 2 - y / (2 * spanY) * height;
    for (let i = 0; i <= 5; i++) {
      const x = minX + (maxX - minX) * i / 5;
      draw("line", {x1: px(x), y1: top, x2: px(x), y2: top + height, stroke: palette.grid}, svg);
      draw("text", {x: px(x), y: top + height + 23, "text-anchor": "middle", fill: palette.label, "font-size": 10}, svg, x.toFixed(1));
    }
    for (let i = -2; i <= 2; i++) {
      const y = spanY * i / 2;
      draw("line", {x1: left, y1: py(y), x2: left + width, y2: py(y), stroke: palette.grid}, svg);
      draw("text", {x: left - 12, y: py(y) + 3, "text-anchor": "end", fill: palette.label, "font-size": 10}, svg, y.toFixed(1));
    }
    draw("text", {x: left + width / 2, y: 410, "text-anchor": "middle", fill: palette.label, "font-size": 11}, svg, "Forward distance (m)");
    draw("text", {x: 17, y: top + height / 2, transform: `rotate(-90 17 ${top + height / 2})`, "text-anchor": "middle", fill: palette.label, "font-size": 11}, svg, "Lateral distance (m)");
    [
      {points: row.gt, color: palette.gt, dash: "5 5", width: 2},
      {points: row.control, color: palette.stale, width: 2.7},
      {points: row.full, color: palette.full, width: 3.1}
    ].forEach(series => {
      const sequence = [[0, 0], ...series.points];
      draw("polyline", {points: sequence.map(p => `${px(p[0])},${py(p[1])}`).join(" "), fill: "none", stroke: series.color, "stroke-width": series.width, "stroke-linejoin": "round", "stroke-linecap": "round", ...(series.dash ? {"stroke-dasharray": series.dash} : {})}, svg);
      series.points.forEach(p => draw("circle", {cx: px(p[0]), cy: py(p[1]), r: 2.8, fill: series.color, stroke: "#ffffff", "stroke-width": 1}, svg));
    });
    draw("circle", {cx: px(0), cy: py(0), r: 5, fill: palette.full, stroke: "#ffffff", "stroke-width": 2}, svg);
    draw("text", {x: px(0) + 9, y: py(0) - 12, fill: palette.label, "font-size": 10}, svg, "Ego");
    $("frame-label").textContent = `Window ${row.frame_index}`;
    $("refresh-state").textContent = row.refresh ? "NEW PLAN ADMITTED" : "PLAN REUSE";
    $("refresh-state").classList.toggle("refreshing", row.refresh);
    $("observed-speed").textContent = `${row.speed.toFixed(2)} m/s`;
    $("reuse-age").textContent = `${row.age} / ${row.budget}`;
    $("full-fde").textContent = `${row.fde.toFixed(3)} m`;
    $("stale-fde").textContent = `${row.control_fde.toFixed(3)} m`;
    $("frame-slider").value = state.index;
    $("frame-counter").textContent = `${state.index + 1} / ${state.rows.length}`;
  }
  function setScene(id) {
    stop();
    state.rows = state.cache[state.dataset].filter(r => r.sequence === id);
    state.index = Math.min(12, state.rows.length - 1);
    $("frame-slider").max = Math.max(0, state.rows.length - 1);
    render();
  }
  async function dataset(name) {
    stop(); state.dataset = name;
    document.querySelectorAll(".dataset-button").forEach(button => {
      const active = button.dataset.dataset === name;
      button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active));
    });
    try {
      $("replay-error").hidden = true;
      $("frame-slider").disabled = true; $("play-button").disabled = true;
      if (!state.cache[name] && window.__FASTROVER_PREVIEW__?.[name]) {
        state.cache[name] = window.__FASTROVER_PREVIEW__[name];
      }
      if (!state.cache[name]) {
        const response = await fetch(`data/${name}.json`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        state.cache[name] = await response.json();
      }
      if (state.dataset !== name) return;
      const sequences = [...new Set(state.cache[name].map(r => r.sequence))];
      $("scene-select").replaceChildren(...sequences.map(sequence => {
        const option = document.createElement("option"); option.value = sequence; option.textContent = sequence; return option;
      }));
      setScene(sequences[0]);
      $("frame-slider").disabled = false; $("play-button").disabled = false;
    } catch (error) {
      $("replay-error").textContent = "Replay data could not be loaded. Serve this page over HTTP and refresh. The downloadable CPU replay remains available in the repository.";
      $("replay-error").hidden = false;
    }
  }
  document.querySelectorAll(".dataset-button").forEach(button => button.addEventListener("click", () => dataset(button.dataset.dataset)));
  $("scene-select").addEventListener("change", event => setScene(event.target.value));
  $("frame-slider").addEventListener("input", event => {stop(); state.index = Number(event.target.value); render();});
  $("play-button").addEventListener("click", () => {
    if (state.timer) return stop();
    $("play-button").textContent = "Ⅱ";
    $("play-button").setAttribute("aria-label", "Pause numerical replay");
    if (state.index >= state.rows.length - 1) state.index = 0;
    render();
    state.timer = setInterval(() => {
      if (state.index >= state.rows.length - 1) return stop();
      state.index += 1; render();
    }, 650);
  });
  document.addEventListener("visibilitychange", () => {if (document.hidden) stop();});
  const tables = {
    frozen: [["Every update", ".384", ".726", "100.0", ".387", ".820", "100.0"], ["Fixed interval", ".330", ".599", "8.2", ".289", ".584", "11.4"], ["FastRoverVLA", ".327", ".593", "5.8", ".266", ".526", "4.8"]],
    requests: [["Every update", ".385", ".727", "100.0", ".391", ".831", "100.0"], ["Fixed interval", ".330", ".599", "8.2", ".287", ".581", "11.4"], ["FastRoverVLA", ".328", ".596", "6.0", ".266", ".526", "4.8"]]
  };
  document.querySelectorAll(".result-tab").forEach(button => button.addEventListener("click", () => {
    const selected = button.dataset.table;
    document.querySelectorAll(".result-tab").forEach(tab => {const active = tab === button; tab.classList.toggle("active", active); tab.setAttribute("aria-pressed", String(active));});
    $("results-body").replaceChildren(...tables[selected].map((row, i) => {
      const tr = document.createElement("tr"); if (i === 2) tr.className = "our-row";
      row.forEach((value, j) => {const td = document.createElement(j === 0 ? "th" : "td"); if (j === 0) td.scope = "row"; td.textContent = value.startsWith(".") ? `0${value}` : value; tr.append(td);}); return tr;
    }));
    document.querySelectorAll(".rate-label").forEach(label => {label.replaceChildren(document.createTextNode(`${selected === "frozen" ? "Refresh" : "Requests"} ↓ `)); const small = document.createElement("small"); small.textContent = "%"; label.append(small);});
    $("table-note").textContent = selected === "frozen" ? "Shared frozen predictions; refresh counts are plan admissions, with zero model requests during replay. Primary archived scoring convention; see the separate past-only-heading check in the repository." : "Independent serial GPU runs with actual logical model requests. These outputs differ from frozen-prediction replay. Their reported measurements are archived paper results, not recomputed by the CPU release.";
  }));
  document.querySelectorAll("[data-copy]").forEach(button => button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText($(button.dataset.copy).textContent);
      $("copy-status").textContent = "Copied to clipboard";
    } catch (_) {$("copy-status").textContent = "Copy unavailable. Select the code and copy it manually.";}
    $("copy-status").classList.add("visible");
    setTimeout(() => $("copy-status").classList.remove("visible"), 2200);
  }));
  const dialog = $("figure-dialog");
  document.querySelectorAll("[data-image]").forEach(button => button.addEventListener("click", () => {
    $("dialog-image").src = button.dataset.image;
    $("dialog-image").alt = button.querySelector("img").alt;
    $("dialog-caption").textContent = button.dataset.caption;
    dialog.showModal();
  }));
  $("close-dialog").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => {if (event.target === dialog) {const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();}});
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    const link = document.querySelector(`.site-header nav a[href="#${entry.target.id}"]`);
    if (link) {if (entry.isIntersecting) link.setAttribute("aria-current", "location"); else link.removeAttribute("aria-current");}
  }), {rootMargin: "-15% 0px -65% 0px"});
  document.querySelectorAll("#method,#explore,#results,#release").forEach(section => observer.observe(section));
  dataset("rellis");
})();
