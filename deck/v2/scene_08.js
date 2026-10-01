// Slide 08's live scene for animate.py: the Hamburg strike lands, the agents work it, and
// the thread scrolls down through what they prepared before settling on the still.
//
// Every fact is orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg"):
// 3 of 7 bookings call at Hamburg (SHP-001, SHP-002, SHP-005), up to 5 days of delay;
// SHP-001 rerouted, its carrier amendment to Hapag-Lloyd and its customer mail drafted;
// SHP-002 held; 6 drafts and 12 TMS changes queued, the SHP-001 changes being exactly the
// run's write-backs. Dates follow the slide's frame (ETA 10 Oct, +2 days), as build_08.py
// does. The strike and its 23-hour lead are the demo scenario, which "This run" says.
// The ops-channel heads-up is the one item the build does not draft: it shows where the
// Comms agent's work goes next (slide 09), gated like every other draft.
//
// Uniform with the still, by construction (slide 07's lesson): every new line is a clone
// of an element build_08.py drew - the agent cards, ring, name, pills, the mail card and
// its gate, the slide's own small-caps label - re-worded. The last frame is the still,
// pixel for pixel: animate.py checks it.
//
// window.scene(t) is a pure function of t, so every frame can be rendered on its own.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const ease = x => 1 - Math.pow(1 - x, 3);
  const clamp = x => Math.max(0, Math.min(1, x));
  const prog = (t, t0, d = 0.35) => ease(clamp((t - t0) / d));
  // build_08.py's tokens
  const BLUE = "#006BFF", INK = "#0A0A0A", MUT = "#6B6B6B", GREY = "#9A9A9A",
        GREY_BG = "#F3F3F3", RED = "#EA001D", RED_BG = "#FEECEC";
  const GAP = 8, STATUS_H = 26;
  // the spinner and the shine land on their resting state on the last frame
  const SPINS = 15, SHINES = 14;

  // the timeline, in seconds
  const T = {
    alert: 0.5,                 // the headline lands (animate.py: popup-news, notifications)
    stats: 1.7,                 // "This run" has risen
    calm: 3.0,                  // the alert colour settles
    reroute: 4.8, mail: 6.1, hold: 7.4, foot: 7.9,
    extras: 8.2,                // what was prepared sits below the fold
    down1: 10.0, down2: 12.9, up: 15.4,
  };

  const $ = id => document.getElementById(id);
  const texts = g => [...g.querySelectorAll(":scope > text")];
  const el = (tag, attrs) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  };
  const txt = (tpl, x, y, s, over = {}) => {
    const e = tpl.cloneNode(false);
    e.setAttribute("x", x); e.setAttribute("y", y); e.textContent = s;
    for (const k in over) over[k] === null ? e.removeAttribute(k) : e.setAttribute(k, over[k]);
    return e;
  };
  // a text's length, measured on the page even when its card is not mounted yet
  let measureRoot = null;
  const width = e => {
    if (e.isConnected) return e.getComputedTextLength();
    const c = e.cloneNode(true); measureRoot.appendChild(c);
    const w = c.getComputedTextLength(); c.remove(); return w;
  };
  const hex = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  const mix = (a, b, k) => "#" + hex(a).map((v, i) => Math.round(v + (hex(b)[i] - v) * k).toString(16).padStart(2, "0")).join("");

  let S = null;
  function init() {
    const svg = document.querySelector("svg");
    const defs = el("defs", {});
    svg.insertBefore(defs, svg.firstChild);
    measureRoot = el("g", { visibility: "hidden" }); svg.appendChild(measureRoot);
    let nShine = 0;
    const shine = () => {
      const g = el("linearGradient", { id: `shine8-${nShine++}`, gradientUnits: "userSpaceOnUse", x1: 0, x2: 0, y1: 0, y2: 0 });
      g.innerHTML = `<stop offset="0" stop-color="${GREY}"/><stop offset="0.5" stop-color="${INK}"/><stop offset="1" stop-color="${GREY}"/>`;
      defs.appendChild(g);
      return g;
    };
    const ring = g => [...g.querySelectorAll(":scope > circle")].filter(c => +c.getAttribute("r") < 2.5);
    const centre = dots => [dots.reduce((a, c) => a + +c.getAttribute("cx"), 0) / dots.length,
                            dots.reduce((a, c) => a + +c.getAttribute("cy"), 0) / dots.length];

    // ---- the alert: the headline's badge and the bell ping, the card flashes red, the bell rings
    const news = $("popup-news"), newsCard = news.querySelectorAll(":scope > rect")[1];
    const newsBadge = [...news.querySelectorAll(":scope > circle")].find(c => c.getAttribute("fill") === RED);
    const flash = newsCard.cloneNode(false);
    flash.setAttribute("fill", "none"); flash.setAttribute("stroke", RED);
    flash.setAttribute("stroke-width", "1.5"); flash.removeAttribute("stroke-opacity");
    news.appendChild(flash);
    const bell = $("notifications"), bellPath = bell.querySelector("path");
    // three red pings each: from the headline's badge, and round the bell itself, sized to
    // stay inside the app window (a ring from the bell's badge crossed the window's corner)
    const bb = bellPath.getBBox(), bellPivot = [bb.x + bb.width / 2, bb.y];
    const pings = [];
    for (const [cx, cy, r0, r1, before] of [[+newsBadge.getAttribute("cx"), +newsBadge.getAttribute("cy"), 8, 18, newsBadge],
                                             [bb.x + bb.width / 2, bb.y + bb.height / 2, 7, 16, bellPath]])
      for (let k = 0; k < 3; k++) {
        const p = el("circle", { cx, cy, r: r0, fill: "none", stroke: RED, "stroke-width": 1.5 });
        before.parentNode.insertBefore(p, before);
        pings.push([p, T.alert + 0.1 + k * 0.6, r0, r1]);
      }
    // the Risk count in the sidebar turns red while the alert is fresh
    const side = $("sidebar");
    const riskLabel = texts(side).find(e => e.textContent === "Risk");
    const riskCount = texts(side).find(e => e.textContent === "1" && +e.getAttribute("y") === +riskLabel.getAttribute("y") - 1);
    const riskPill = riskCount.previousElementSibling;
    const riskPillFill = riskPill.getAttribute("fill"), riskInk = riskCount.getAttribute("fill");
    const approvals = texts(side).find(e => e.textContent === "18");

    // ---- the Risk agent keeps working: its ring turns, "working…" shines
    const agent = $("popup-agent"), agentDots = ring(agent), agentC = centre(agentDots);
    const working = texts(agent).find(e => e.textContent === "working…");
    const workFill = working.getAttribute("fill");
    const workShine = shine();

    // ---- "This run": the figures count as the agents produce them
    const run = $("this-run");
    const figs = {};
    texts(run).forEach(e => { const v = e.textContent; if (/^(60|1|3|0|€46,500)$/.test(v) && !figs[v]) figs[v] = e; });

    // ---- the thread: the still's cards, and new ones cloned from them
    const dec = $("decisions"), win = dec.querySelector("rect");
    const rG = $("decision-reroute"), mG = $("decision-mail"), hG = $("decision-hold");
    const foot = texts(dec).find(e => e.textContent.startsWith("Cost avoided"));
    const footG = el("g", {}); dec.insertBefore(footG, foot); footG.appendChild(foot);
    const top = +rG.querySelectorAll(":scope > rect")[1].getAttribute("y");
    const viewTop = top - 2, viewBottom = +win.getAttribute("y") + +win.getAttribute("height") - 4;
    const vclip = el("clipPath", { id: "thread-view" });
    vclip.appendChild(el("rect", { x: win.getAttribute("x"), y: viewTop, width: win.getAttribute("width"), height: viewBottom - viewTop }));
    defs.appendChild(vclip);
    const scroller = el("g", { "clip-path": "url(#thread-view)" });
    win.after(scroller);

    const rTexts = texts(rG);
    const nameT = rTexts.find(e => e.getAttribute("fill") === BLUE && e.getAttribute("font-size") === "12.5");
    const subT = rTexts.find(e => e.getAttribute("font-size") === "12");
    const headT = rTexts.find(e => e.getAttribute("font-size") === "13.5");
    const lineT = rTexts.find(e => e.getAttribute("font-size") === "11.5");
    const pillR = [...rG.querySelectorAll(":scope > rect")][2], pillT = rTexts.find(e => e.getAttribute("font-size") === "10.5");
    const pillRight = +pillR.getAttribute("x") + +pillR.getAttribute("width");
    const ringC = centre(ring(rG));
    const cardOf = g => [...g.querySelectorAll(":scope > rect")].slice(0, 2);   // shadow, card
    const trailLabel = texts($("detection-trail"))[0], trailText = texts($("detection-trail"))[1];

    const sizeCard = (g, h) => cardOf(g).forEach(r => r.setAttribute("height", h));
    const subAfterName = (g, name) => {          // the grey line sits 12px after the agent's name
      const n = texts(g).find(e => e.getAttribute("fill") === BLUE && e.getAttribute("font-size") === "12.5");
      const s = texts(g).find(e => e.getAttribute("font-size") === "12");
      n.textContent = name;
      s.setAttribute("x", (+n.getAttribute("x") + width(n) + 12).toFixed(1));
      return s;
    };
    const pillAt = (g, label, fill, ink, x, y, anchorEnd = false) => {   // build_08.pill()
      const r = pillR.cloneNode(false), tx = pillT.cloneNode(false);
      const w = Math.round(label.length * 10.5 * 0.6 + 18), x0 = anchorEnd ? x - w : x;
      r.setAttribute("x", x0); r.setAttribute("y", y); r.setAttribute("width", w); r.setAttribute("fill", fill);
      tx.setAttribute("x", x0 + w / 2); tx.setAttribute("y", y + 10 + 10.5 * 0.36); tx.setAttribute("fill", ink);
      tx.textContent = label;
      g.append(r, tx);
      return w;
    };
    const mount = (g, check) => { scroller.appendChild(g); const ok = check ? check() : true; g.remove(); if (!ok) throw new Error("a line overruns its card"); };

    // an agent at work: the card's ring and name on a bare line, the action shining
    const status = (who, what) => {
      const g = el("g", {});
      ring(rG).forEach(c => g.appendChild(c.cloneNode()));
      const n = txt(nameT, nameT.getAttribute("x"), nameT.getAttribute("y"), who);
      const w = txt(nameT, 0, nameT.getAttribute("y"), what + "…", { "font-weight": 400 });
      g.append(n, w);
      scroller.appendChild(g);
      w.setAttribute("x", (+nameT.getAttribute("x") + width(n) + 6).toFixed(1));
      const sh = shine(); w.setAttribute("fill", `url(#${sh.id})`);
      const box = w.getBBox();
      g.remove();
      return { g, natY: ringC[1] - STATUS_H / 2, h: STATUS_H, spin: ring(g), shine: [sh, box.x, box.width] };
    };

    // the Risk agent's finding: the reroute card, re-worded, with the seven bookings
    const finding = () => {
      const g = rG.cloneNode(true); g.removeAttribute("id");
      const H = 86; sizeCard(g, H);
      const s = subAfterName(g, "Risk agent");
      s.textContent = "Warnstreik im Hamburger Hafen · 23 h before the international wires";
      texts(g).find(e => e.getAttribute("font-size") === "13.5").textContent = "3 of 7 bookings call at Hamburg. Up to 5 days late.";
      texts(g).find(e => e.getAttribute("font-size") === "11.5").remove();
      const pr = [...g.querySelectorAll(":scope > rect")][2], pt = texts(g).find(e => e.getAttribute("font-size") === "10.5");
      pr.remove(); pt.remove();
      pillAt(g, "high", RED_BG, RED, pillRight, +pillR.getAttribute("y"), true);
      let x = +headT.getAttribute("x");
      const y = top + 56;
      for (const [id, hit] of [["SHP-001", 1], ["SHP-002", 1], ["SHP-003", 0], ["SHP-004", 0], ["SHP-005", 1], ["SHP-006", 0], ["SHP-007", 0]])
        x += pillAt(g, id, hit ? RED_BG : GREY_BG, hit ? RED : MUT, x, y) + 6;
      const label = txt(lineT, x + 6, y + 14, "4 stay on plan");
      g.appendChild(label);
      mount(g, () => s.getBBox().x + s.getBBox().width < pillRight - 60);
      return { g, natY: top, h: H };
    };

    // a drafted message: the Comms agent's mail card, re-worded; its own channel's mark
    const draftCard = (sub, subject, body, markName, gateLabel) => {
      const g = mG.cloneNode(true); g.removeAttribute("id");
      g.querySelectorAll("[id]").forEach(e => e.removeAttribute("id"));
      const s = subAfterName(g, "Comms agent"); s.textContent = sub;
      const tt = texts(g);
      tt.find(e => e.getAttribute("font-size") === "12.5" && e.getAttribute("font-weight") === "600" && e.getAttribute("fill") === INK).textContent = subject;
      const b = tt.find(e => e.getAttribute("font-size") === "11.5"); b.textContent = body;
      const gate = tt.find(e => e.textContent === "Draft ready");
      if (gateLabel) gate.textContent = gateLabel;
      if (markName) {
        const old = g.querySelector(":scope > g");                     // the Outlook mark
        // build_08.mark(): the Outlook mark's 15px box, recovered from its transform, holds the new mark
        const m = window.MARKS[markName], o = window.MARKS.Outlook, size = 15;
        const tr = old.getAttribute("transform").match(/translate\(([\d.]+) ([\d.]+)\)/);
        const so = size / Math.max(o.w, o.h), sc = size / Math.max(m.w, m.h);
        const bx = +tr[1] - (size - o.w * so) / 2, by = +tr[2] - (size - o.h * so) / 2;
        const body8 = m.body.replace(/(id="|url\(#|href="#)([^")]+)/g, (_, a, b2) => a + "v8" + markName + "-" + b2);
        const ng = el("g", { transform: `translate(${(bx + (size - m.w * sc) / 2).toFixed(1)} ${(by + (size - m.h * sc) / 2).toFixed(1)}) scale(${sc.toFixed(4)})` });
        ng.innerHTML = body8;
        old.replaceWith(ng);
      }
      mount(g, () => b.getBBox().x + b.getBBox().width < gate.getBBox().x - 12
                     && s.getBBox().x + s.getBBox().width < +g.querySelectorAll(":scope > rect")[1].getAttribute("x") + 724 - 16);
      // a clone keeps the still card's coordinates
      return { g, natY: +cardOf(mG)[1].getAttribute("y"), h: +cardOf(mG)[1].getAttribute("height") };
    };

    // the TMS link's record: what these calls change on SHP-001, queued for approval
    const record = () => {
      const g = rG.cloneNode(true); g.removeAttribute("id");
      const H = 150; sizeCard(g, H);
      const s = subAfterName(g, "TMS link");
      s.textContent = "SHP-001 · what these calls change on the booking";
      texts(g).filter(e => ["13.5", "11.5", "10.5"].includes(e.getAttribute("font-size"))).forEach(e => e.remove());
      [...g.querySelectorAll(":scope > rect")][2].remove();
      const x0 = +headT.getAttribute("x");
      const ROWS = [["Exception flag", "none", "Hamburg strike, high"], ["Port of discharge", "HAM", "RTM"],
                    ["Routing code", "R-HAM-STD", "R-RTM-ALT"], ["ETA", "10 Oct", "12 Oct"],
                    ["Booking status", "On plan", "Rerouted, amendment pending"],
                    ["Communication log", "", "+ 2 drafts: Hapag-Lloyd, Katrin Vogel"]];
      const rows = [];
      scroller.appendChild(g);
      ROWS.forEach(([field, from, to], i) => {
        const y = top + 50 + i * 18, rg = el("g", {});
        g.appendChild(rg); rows.push(rg);
        rg.appendChild(txt(lineT, x0, y, field));
        if (from) {
          const o = txt(lineT, x0 + 130, y, from, { fill: GREY });
          rg.appendChild(o);
          rg.appendChild(el("rect", { x: x0 + 130, y: y - 4, width: width(o).toFixed(1), height: 1, fill: GREY }));
          rg.appendChild(txt(lineT, x0 + 214, y, "→", { fill: GREY }));
        }
        rg.appendChild(txt(lineT, x0 + 234, y, to, { fill: INK, "font-weight": 600 }));
      });
      // the gate, as on the mail cards: what it is, and Approve
      const mt = texts(mG), gate = mt.find(e => e.textContent === "Draft ready");
      const btn = [...mG.querySelectorAll(":scope > rect")].find(r => r.getAttribute("fill") === INK && !r.hasAttribute("fill-opacity"));
      const btnT = mt.find(e => e.textContent === "Approve");
      const dy = (top + H - 38) - +btn.getAttribute("y");
      const shift = e => { const c = e.cloneNode(false); c.textContent = e.textContent; c.setAttribute("y", +e.getAttribute("y") + dy); return c; };
      const gl = shift(gate); gl.textContent = "Queued, not written";
      g.append(gl, shift(btn), shift(btnT));
      const ok = rows.every(r => r.getBBox().x + r.getBBox().width < gl.getBBox().x - 12);
      g.remove();
      if (!ok) throw new Error("a record row overruns its card");
      return { g, natY: top, h: H, rows };
    };

    // the label over what was prepared: the slide's own small caps
    const prepared = () => {
      const g = el("g", {});
      const x = +foot.getAttribute("x");
      const a = txt(trailLabel, x, top + 13, "PREPARED FOR YOU");
      const b = txt(trailText, 0, top + 13, "6 drafts and 12 TMS changes, each waiting for your approval. Nothing is sent or written.");
      g.append(a, b);
      scroller.appendChild(g); b.setAttribute("x", (x + width(a) + 12).toFixed(1)); g.remove();
      return { g, natY: top, h: 18 };
    };
    const still = g => {
      const c = cardOf(g)[1];
      return { g, natY: +c.getAttribute("y"), h: +c.getAttribute("height") };
    };
    const footItem = { g: footG, natY: +foot.getAttribute("y") - 10, h: 14 };

    const mail = draftCard("Drafted the amendment to Hapag-Lloyd.", "HLCU-2261188: amend discharge to RTM",
                           "Please amend the booking to discharge at RTM instead of HAM, and confirm the schedule.");
    const slack = draftCard("Drafted a heads-up for the ops channel.", "#ops · Hamburg strike: SHP-001, SHP-002, SHP-005",
                            "2 reroutes via Rotterdam, 1 hold. 6 drafts and 12 TMS changes wait for your approval.", "Slack");

    const ITEMS = [
      { t0: 2.2, t1: 3.0, ...status("Risk agent", "Checking 7 bookings against the strike") },
      { t0: 3.0, ...finding() },
      { t0: 3.9, t1: T.reroute, ...status("Routing agent", "Weighing slack against up to 5 days of delay") },
      { t0: T.reroute, pinned: true, ...still(rG) },
      { t0: 5.3, t1: T.mail, ...status("Comms agent", "Drafting a mail to Katrin Vogel") },
      { t0: T.mail, ...still(mG) },
      { t0: 6.6, t1: T.hold, ...status("Routing agent", "Looking for a better route for SHP-002") },
      { t0: T.hold, ...still(hG) },
      { t0: T.foot, ...footItem },
      { t0: T.extras, extra: true, gapBefore: 22, ...prepared() },
      { t0: T.extras, extra: true, ...mail },
      { t0: T.extras, extra: true, ...slack },
      { t0: T.extras, extra: true, ...record() },
    ];
    let nClip = 0;
    for (const it of ITEMS) {
      it.outer = el("g", {});
      const cp = el("clipPath", { id: `item8-${nClip++}` });
      it.clipRect = el("rect", { x: win.getAttribute("x"), y: it.natY - 2, width: win.getAttribute("width"), height: 0 });
      cp.appendChild(it.clipRect); defs.appendChild(cp);
      it.clipG = el("g", {}); it.clipId = cp.id;
      it.outer.appendChild(it.clipG); it.clipG.appendChild(it.g);
      scroller.appendChild(it.outer);
    }
    S = { flash, pings, bellPath, bellPivot, riskPill, riskCount, riskPillFill, riskInk, approvals,
          agentDots, agentC, working, workFill, workShine, workBox: working.getBBox(), figs,
          items: ITEMS, top, viewH: viewBottom - top, viewBottom };
  }

  const sweep = (g, x, w, u, cycles) => {
    const c = x - 40 + ((u * cycles) % 1) * (w + 80);
    g.setAttribute("x1", c - 30); g.setAttribute("x2", c + 30);
    return c + 30 > x && c - 30 < x + w;                // is the highlight on the text?
  };

  window.scene = t => {
    if (!S) init();
    const u = t / window.LAST_T;                        // 0 to 1 over the video, exactly 1 at the end

    // ---- the alert
    const a = prog(t, T.alert + 0.05, 0.2) * (1 - prog(t, T.calm, 0.8));
    const pulse = t < T.alert ? 0 : 0.55 + 0.45 * Math.cos(2 * Math.PI * (t - T.alert) / 0.8);
    S.flash.setAttribute("opacity", (0.85 * pulse * a).toFixed(3));
    S.flash.setAttribute("visibility", a > 0 ? "visible" : "hidden");
    for (const [p, t0, r0, r1] of S.pings) {
      const k = clamp((t - t0) / 0.9);
      p.setAttribute("visibility", k > 0 && k < 1 ? "visible" : "hidden");
      p.setAttribute("r", (r0 + (r1 - r0) * ease(k)).toFixed(2));
      p.setAttribute("stroke-opacity", (0.6 * (1 - k)).toFixed(3));
    }
    const wob = t > T.alert && t < T.alert + 1.6 ? 16 * Math.sin(2 * Math.PI * 4.5 * (t - T.alert)) * Math.exp(-2.6 * (t - T.alert)) : 0;
    if (wob) S.bellPath.setAttribute("transform", `rotate(${wob.toFixed(2)} ${S.bellPivot[0]} ${S.bellPivot[1]})`);
    else S.bellPath.removeAttribute("transform");
    S.riskCount.setAttribute("opacity", t < T.alert ? 0 : 1);
    S.riskPill.setAttribute("opacity", t < T.alert ? 0 : 1);
    if (a > 0) { S.riskPill.setAttribute("fill", mix(S.riskPillFill, RED, a)); S.riskCount.setAttribute("fill", mix(S.riskInk, "#FFFFFF", a)); }
    else { S.riskPill.setAttribute("fill", S.riskPillFill); S.riskCount.setAttribute("fill", S.riskInk); }

    // ---- the Risk agent at work, resting exactly on the still at the end
    const ang = (360 * SPINS * u) % 360;
    for (const d of S.agentDots) ang ? d.setAttribute("transform", `rotate(${ang.toFixed(3)} ${S.agentC[0]} ${S.agentC[1]})`) : d.removeAttribute("transform");
    const lit = sweep(S.workShine, S.workBox.x, S.workBox.width, u, SHINES);
    S.working.setAttribute("fill", lit ? `url(#${S.workShine.id})` : S.workFill);

    // ---- the figures: counted as the agents produce them
    const F = S.figs;
    F["60"].textContent = String(Math.round(60 * prog(t, T.stats - 0.1, 1.0)));
    F["1"].textContent = t >= T.stats - 0.1 ? "1" : "0";
    F["3"].textContent = String(Math.round(3 * clamp((t - T.reroute + 0.3) / (T.hold - T.reroute))));
    F["€46,500"].textContent = "€" + Math.round(46500 * prog(t, T.hold, 1.2)).toLocaleString("en-US");
    S.approvals.textContent = String(Math.round(18 * clamp((t - T.reroute) / (T.extras - T.reroute))));

    // ---- the thread
    let at = 0, thread = 0, pinAt = 0;
    for (const it of S.items) {
      const pin = it.extra ? (t >= it.t0 ? 1 : 0) : prog(t, it.t0, 0.35);
      const po = it.t1 ? prog(t, it.t1, 0.3) : 0;
      it.k = pin * (1 - po); it.pin = pin;
      at += (it.gapBefore || 0) * it.k;
      if (it.pinned) pinAt = at;
      it.at = at;
      at += (it.h + GAP) * it.k;
      if (!it.extra) thread = at - GAP;
    }
    // follow the newest line; once the hold lands, the first decision sits at the top
    let scroll = Math.max(Math.max(0, thread - S.viewH), pinAt * prog(t, T.hold, 0.8));
    // then scroll down through what was prepared, and back: first to the two drafts, then
    // to the record, then home. The two stops are where those cards' feet meet the fold.
    const n = S.items.length, record = S.items[n - 1], drafts = S.items[n - 2];
    const stop = it => it.at + it.h - (scroll + S.viewH) + 6;
    const d1 = Math.max(0, stop(drafts)), d2 = Math.max(d1, stop(record));
    scroll += d1 * prog(t, T.down1, 0.9) + (d2 - d1) * prog(t, T.down2, 0.8) - d2 * prog(t, T.up, 1.0);
    for (const it of S.items) {
      const k = it.k, y = S.top - scroll + it.at;
      it.outer.setAttribute("transform", `translate(0 ${(y - it.natY).toFixed(3)})`);
      it.outer.setAttribute("visibility", k > 0.001 ? "visible" : "hidden");
      if (k >= 0.9999) it.clipG.removeAttribute("clip-path");
      else {
        it.clipG.setAttribute("clip-path", `url(#${it.clipId})`);
        it.clipRect.setAttribute("height", ((it.h + 8) * k + 2).toFixed(3));
      }
      it.g.setAttribute("opacity", k >= 0.9999 ? 1 : k.toFixed(4));
      if (it.pin < 1 && !it.extra) it.g.setAttribute("transform", `translate(0 ${((1 - it.pin) * 10).toFixed(3)})`);
      else it.g.removeAttribute("transform");
      if (it.spin) {
        const [cx, cy] = [it.spin.reduce((s, c) => s + +c.getAttribute("cx"), 0) / 8, it.spin.reduce((s, c) => s + +c.getAttribute("cy"), 0) / 8];
        for (const d of it.spin) d.setAttribute("transform", `rotate(${ang.toFixed(3)} ${cx} ${cy})`);
      }
      if (it.shine) sweep(it.shine[0], it.shine[1], it.shine[2], u, SHINES * 1.6);
      if (it.rows) it.rows.forEach((r, i) => r.setAttribute("opacity", prog(t, T.down2 + 0.25 + i * 0.12, 0.3).toFixed(3)));
    }
  };
})();
