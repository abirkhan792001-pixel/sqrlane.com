// Slide 01's live scene for animate.py: the cover's two flows, played as they happen.
//
// The desk: four mails on SHP-001 arrive in the inbox one after another, each is
// tagged with the agent that owns it, travels to the desk agents, and lands on the
// record as the field it fills.
// The lane: SHP-001 sails up the Channel towards Hamburg while the watched places
// pulse as they are read. The Hamburg strike lights up, reaches the risk agents, the
// leg to Hamburg breaks and the reroute into Rotterdam is drawn while the ship is still
// at sea; the record takes the new discharge port, the ETA and the drafted carrier
// mail, and the change waits in the approval gate. Then the loop resets.
//
// Nothing here is new content: every word on screen is the static slide's own; the
// script only decides when each part appears. window.scene(t) is a pure function of
// t, so every frame can be rendered on its own and the last frame meets the first.
(function () {
  const LOOP = 14;
  const INK = "#0A0A0A", MUT = "#6E6E66", AMB = "#96580A", CARD = "#FBF8F3";
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.querySelector("svg");
  const $ = id => document.getElementById(id);
  const ease = x => 1 - Math.pow(1 - x, 3);
  const clamp = x => Math.max(0, Math.min(1, x));
  const prog = (t, t0, d = 0.4) => ease(clamp((t - t0) / d));
  // 0 before t0, 1 at its peak, back to 0 by t0 + d: a flash or a pulse
  const bump = (t, t0, d) => { const x = (t - t0) / d; return x < 0 || x > 1 ? 0 : Math.sin(Math.PI * x); };
  const el = (tag, attrs, parent = svg) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    parent.appendChild(e);
    return e;
  };
  const mix = (a, b, p) => {
    const h = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
    const [x, y] = [h(a), h(b)];
    return "rgb(" + x.map((v, i) => Math.round(v + (y[i] - v) * p)).join(",") + ")";
  };
  const at = (path, f) => path.getPointAtLength(path.getTotalLength() * clamp(f));

  // Everything that builds up over the loop fades back together at the end.
  const RESET = 12.9;
  const keep = t => 1 - prog(t, RESET, 0.6);

  // ----------------------------------------------------------------- overlay
  const top = el("g", { id: "motion" });
  function dot(r, fill, halo) {
    const g = el("g", {}, top);
    if (halo) el("circle", { r: r * 2.6, fill, "fill-opacity": 0.18 }, g);
    el("circle", { r, fill, stroke: CARD, "stroke-width": 1.5 }, g);
    g.style.opacity = 0;
    return g;
  }
  function travel(g, path, f, show) {
    const p = at(path, f);
    g.setAttribute("transform", `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})`);
    g.style.opacity = show;
  }

  // ----------------------------------------------------------------- the desk
  const MAIL = ["rate-request", "booking-request", "bill-of-lading", "carrier-invoice"];
  const FIELDS = ["quote", "booking", "bl", "invoice"];
  const ARRIVE = MAIL.map((_, i) => 0.4 + 0.75 * i);
  const win = $("inbox-window").getBBox();
  const deskNode = $("desk-node"), riskNode = $("risk-node");
  const deskArrow = $("desk-arrow"), laneArrow = $("lane-arrow");
  for (const n of [deskNode, riskNode]) { n.style.transformBox = "fill-box"; n.style.transformOrigin = "center"; }
  const nodeBox = n => n.querySelector("rect").getBBox();

  const rows = MAIL.map((m, i) => {
    const row = $("mail-" + m), tag = $("owner-" + m), line = $("desk-line-" + m);
    const y = line.getPointAtLength(0).y;
    const hl = document.createElementNS(NS, "rect");
    for (const [k, v] of Object.entries({ x: win.x + 6, y: y - 17, width: win.width - 12, height: 34, rx: 8, fill: "#EFE6D8" }))
      hl.setAttribute(k, v);
    $("inbox").insertBefore(hl, $("inbox-window").nextSibling);
    tag.style.transformBox = "fill-box"; tag.style.transformOrigin = "center";
    return { row, tag, line, hl, pulse: dot(3.2, INK, true), out: dot(3.2, INK, true), t0: ARRIVE[i] };
  });

  // A record field before it is filled shows a placeholder, then flashes as it fills.
  function field(id, placeholder, tone) {
    const g = $("val-" + id), txt = g.querySelector("text");
    const x = +txt.getAttribute("x"), y = +txt.getAttribute("y");
    const ph = el("text", { x, y, "text-anchor": "end", "font-family": "Geist", "font-size": 14,
      "font-weight": placeholder === "HAM" ? 500 : 400, fill: placeholder === "HAM" ? INK : MUT });
    ph.textContent = placeholder;
    g.parentNode.insertBefore(ph, g);
    const card = $("tms-record").querySelector("rect").getBBox();
    const fl = document.createElementNS(NS, "rect");
    for (const [k, v] of Object.entries({ x: card.x + 14, y: y - 21, width: card.width - 28, height: 30, rx: 7,
      fill: tone === "lane" ? AMB : INK, "fill-opacity": tone === "lane" ? 0.12 : 0.06 })) fl.setAttribute(k, v);
    g.parentNode.insertBefore(fl, g.parentNode.firstChild);
    return { g, ph, fl };
  }
  const deskFields = FIELDS.map(f => field(f, "—", "desk"));
  const laneFields = [field("discharge", "HAM", "lane"), field("eta", "as booked", "lane"), field("carrier-mail", "—", "lane")];

  function fill(f, t, t0) {
    const p = prog(t, t0, 0.35) * keep(t);
    f.g.style.opacity = p;
    f.ph.style.opacity = 1 - p;
    f.fl.style.opacity = bump(t, t0 - 0.1, 1.1);
  }

  function nodeKick(n, t, times, col) {
    let s = 0;
    for (const t0 of times) s = Math.max(s, bump(t, t0, 0.35));
    n.style.transform = `scale(${1 + 0.12 * s})`;
  }

  // ----------------------------------------------------------------- the lane
  const STRIKE = 4.7;                       // the walkout is read
  const DECIDE = 5.6;                       // the risk agents have it
  const sea = $("lane-sea"), toRtm = $("lane-reroute-rotterdam"), toHam = $("lane-planned-hamburg");
  // the planned leg, as it looked before the strike: the same dotted ink as the sea lane
  const planned = toHam.cloneNode(false);
  planned.removeAttribute("id");
  for (const [k, v] of Object.entries({ stroke: INK, "stroke-opacity": 0.55, "stroke-dasharray": "1 5", "stroke-width": 1.8 }))
    planned.setAttribute(k, v);
  toHam.parentNode.insertBefore(planned, toHam);
  const rtmLen = toRtm.getTotalLength();
  toRtm.setAttribute("stroke-dasharray", `${rtmLen} ${rtmLen}`);

  // the ship sails inside the map, under its fades, so it emerges out of the haze.
  // A heading arrow, turned along the lane, so it never reads as one of the pins.
  const ship = el("g", {}, $("lane"));
  el("circle", { r: 14, fill: INK, "fill-opacity": 0.07 }, ship);
  el("path", { d: "M8 0 L-6 -6.5 L-3 0 L-6 6.5 Z", fill: INK, stroke: CARD, "stroke-width": 1.6, "stroke-linejoin": "round" }, ship);
  const dock = el("circle", { r: 6, fill: "none", stroke: INK, "stroke-width": 1.4 }, $("lane"));

  // Hamburg: neutral until the strike is read, then the slide's own amber
  const hamPill = $("pill-ham"), hamPin = $("pin-ham"), hamSpoke = $("spoke-ham");
  const calm = hamPill.cloneNode(true);
  calm.removeAttribute("id");
  calm.querySelector("rect").setAttribute("fill", CARD);
  calm.querySelector("rect").setAttribute("stroke", INK);
  calm.querySelector("rect").setAttribute("stroke-opacity", 0.12);
  calm.querySelector("circle").setAttribute("fill", MUT);
  calm.querySelector("text").setAttribute("fill", MUT);
  hamPill.parentNode.insertBefore(calm, hamPill);
  $("strike-rings").style.display = "none";
  const hx = +hamPin.getAttribute("cx"), hy = +hamPin.getAttribute("cy");
  const rings = [0, 1].map(() => el("circle", { cx: hx, cy: hy, r: 6, fill: AMB }, $("signal-ham")));
  $("signal-ham").insertBefore(rings[0], hamPin); $("signal-ham").insertBefore(rings[1], hamPin);

  // the places the risk agents keep reading: a ring at the pin, a signal along the spoke
  const WATCHED = [["rtm", 0.9], ["rhine", 2.1], ["frinl", 3.0]];
  const watch = WATCHED.map(([id, phase]) => {
    const pin = $("pin-" + id);
    const ring = el("circle", { cx: pin.getAttribute("cx"), cy: pin.getAttribute("cy"), r: 5, fill: "none", stroke: INK, "stroke-width": 1.2 },
      $("signal-" + id));
    return { spoke: $("spoke-" + id), ring, sig: dot(2.6, INK, false), phase };
  });
  const strikeSig = dot(3.4, AMB, true), laneOut = dot(3.4, AMB, true);

  const gate = $("approval-gate"), gateDot = $("gate-dot");
  gate.style.transformBox = "fill-box"; gate.style.transformOrigin = "left center";
  const GATE = 7.6;
  const gateRing = el("circle", { cx: gateDot.getAttribute("cx"), cy: gateDot.getAttribute("cy"), r: 4, fill: "none", stroke: AMB, "stroke-width": 1.4 }, gate);

  // ----------------------------------------------------------------- one frame
  window.scene = function (T) {
    const t = ((T % LOOP) + LOOP) % LOOP;
    const k = keep(t);

    // desk: arrive, get an owner, travel to the agents, land on the record
    rows.forEach((r, i) => {
      const a = r.t0;
      const p = prog(t, a, 0.45) * k;
      r.row.style.opacity = p;
      r.row.style.transform = `translateX(${-14 * (1 - p)}px)`;
      const tp = prog(t, a + 0.3, 0.3);
      r.tag.style.transform = `scale(${0.7 + 0.3 * tp})`;
      r.tag.style.opacity = tp;
      r.hl.style.opacity = Math.min(prog(t, a, 0.3), 1 - prog(t, a + 1.25, 0.5)) * k;
      const go = clamp((t - (a + 0.45)) / 0.5);
      travel(r.pulse, r.line, ease(go), go > 0 && go < 1 ? 1 : 0);
      r.line.setAttribute("stroke-opacity", (0.38 + 0.5 * bump(t, a + 0.4, 0.7)) * (0.3 + 0.7 * p));
      const out = clamp((t - (a + 1.0)) / 0.38);
      travel(r.out, deskArrow, ease(out), out > 0 && out < 1 ? 1 : 0);
      fill(deskFields[i], t, a + 1.38);
    });
    nodeKick(deskNode, t, rows.map(r => r.t0 + 0.95), INK);

    // lane: the ship, Shanghai's lane up the Channel, then into Rotterdam
    const SAIL = 6.6, IN = 7.8;
    // where the ship is, as a path and a distance along it; the heading is the
    // direction from there to a point a few pixels further on
    let path = sea, d = sea.getTotalLength() * (0.06 + 0.94 * (t / SAIL)), shipOp = 1;
    if (t >= SAIL) { path = toRtm; d = rtmLen * (t < IN ? ease((t - SAIL) / (IN - SAIL)) : 1); }
    if (t > RESET) shipOp = 1 - prog(t, RESET, 0.4);
    if (t > RESET + 0.6) { path = sea; d = sea.getTotalLength() * 0.06; shipOp = prog(t, LOOP - 0.5, 0.45); }
    const L = path.getTotalLength();
    const pos = path.getPointAtLength(Math.min(d, L));
    const a = path.getPointAtLength(Math.max(0, Math.min(d, L) - 4)), b = path.getPointAtLength(Math.min(L, Math.max(d, 4) + 4));
    const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
    ship.setAttribute("transform", `translate(${pos.x.toFixed(1)} ${pos.y.toFixed(1)}) rotate(${ang.toFixed(1)})`);
    ship.style.opacity = shipOp;
    const docked = bump(t, IN - 0.05, 1.0);
    const end = toRtm.getPointAtLength(rtmLen);
    dock.setAttribute("cx", end.x); dock.setAttribute("cy", end.y);
    dock.setAttribute("r", 6 + 14 * clamp((t - IN + 0.05) / 1.0));
    dock.style.opacity = 0.5 * docked;

    // the watched places, read over and over
    for (const w of watch) {
      const c = ((t - w.phase) % 3.5 + 3.5) % 3.5;
      w.ring.setAttribute("r", 5 + 13 * clamp(c / 1.2));
      w.ring.style.opacity = 0.4 * (1 - clamp(c / 1.2));
      const s = clamp((c - 0.25) / 0.9);
      travel(w.sig, w.spoke, ease(s), s > 0 && s < 1 ? 0.55 : 0);
    }

    // the strike: Hamburg lights, the signal reaches the risk agents
    const lit = prog(t, STRIKE, 0.35) * k;
    hamPill.style.opacity = lit;
    calm.style.opacity = 1 - lit;
    hamPin.setAttribute("fill", mix(INK, AMB, lit));
    hamSpoke.setAttribute("stroke", mix(INK, AMB, lit));
    hamSpoke.setAttribute("stroke-opacity", 0.22 + 0.78 * lit);
    hamSpoke.setAttribute("stroke-width", 1.5 + 0.5 * lit);
    rings.forEach((ring, j) => {
      const c = ((t - STRIKE - 0.6 * j) % 1.2 + 1.2) % 1.2;
      ring.setAttribute("r", 6 + 16 * (c / 1.2));
      ring.style.opacity = t >= STRIKE ? 0.32 * (1 - c / 1.2) * lit : 0;
    });
    const sg = clamp((t - (STRIKE + 0.25)) / 0.6);
    travel(strikeSig, hamSpoke, ease(sg), sg > 0 && sg < 1 ? 1 : 0);
    nodeKick(riskNode, t, [STRIKE + 0.85], AMB);

    // the decision: the leg to Hamburg breaks, the reroute is drawn
    const broke = prog(t, DECIDE, 0.4) * k;
    toHam.style.opacity = broke;
    planned.style.opacity = 1 - broke;
    const drawn = prog(t, DECIDE + 0.2, 0.7);
    toRtm.setAttribute("stroke-dashoffset", (rtmLen * (1 - drawn)).toFixed(1));
    toRtm.style.opacity = k;

    // the record takes it, field by field
    const lo = clamp((t - (DECIDE + 0.35)) / 0.4);
    travel(laneOut, laneArrow, ease(lo), lo > 0 && lo < 1 ? 1 : 0);
    fill(laneFields[0], t, DECIDE + 0.8);
    fill(laneFields[1], t, DECIDE + 1.2);
    fill(laneFields[2], t, DECIDE + 1.6);

    // and waits for a person
    const gp = prog(t, GATE, 0.35) * k;
    gate.style.opacity = gp;
    gate.style.transform = `scale(${0.92 + 0.08 * gp})`;
    const gc = ((t - GATE) % 1.6 + 1.6) % 1.6;
    gateRing.setAttribute("r", 4 + 8 * (gc / 1.6));
    gateRing.style.opacity = t > GATE + 0.3 ? 0.5 * (1 - gc / 1.6) * k : 0;
  };
})();
