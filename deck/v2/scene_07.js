// Slide 07's live scene for animate.py: counters, the Customs agent at work, and the Ask
// SQRlane chat played as a conversation.
//
// Every line is the product's own. ask.ask("Price 2 x 40HC Shanghai to Rotterdam") routes
// to the Rate agent, which prices 8 options from the synthetic rate sheet;
// ask.ask("Where is MEDU-1774390?") routes to the Milestones agent, which reads SHP-004
// from the TMS link and asks Routing whether it is on plan; its drafted reply is the
// desk's real reply to the same question in IN-106. Dates are left out: the bookings
// age forward.
//
// Uniform with the still, by construction: nothing here is drawn in HTML or in a style
// of its own. Every new line is a clone of an element build_07.py already drew (the
// question bubble, the agent card, its ring, its name, the draft's rule and lines), so
// font, size, weight, radius, border and card width are the slide's. The rate card is
// the Milestones card, taller. The conversation runs rate question first, so the chat
// ends exactly where the still shows it: the last frame is the static slide.
//
// window.scene(t) is a pure function of t, so every frame can be rendered on its own.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const ease = x => 1 - Math.pow(1 - x, 3);
  const clamp = x => Math.max(0, Math.min(1, x));
  const prog = (t, t0, d = 0.35) => ease(clamp((t - t0) / d));
  // build_07.py's tokens
  const BLUE = "#006BFF", BLUE_BG = "#E8F1FF", INK = "#0A0A0A", MUT = "#6B6B6B",
        GREY = "#9A9A9A", GREY_BG = "#F3F3F3";

  const Q1 = "Where is MEDU-1774390?", Q2 = "Price 2 x 40HC Shanghai to Rotterdam";
  // slidIn: the pop-ups have arrived (animate.py: popup-agent at 1.8 s, plus its 0.6 s)
  const T = { slidIn: 2.5, chip: 2.3, fill2: 2.45, send2: 3.0, customsDone: 6.2, type1: 7.4, send1: 8.6 };
  const GAP = 6;            // the still's gap between chat items (bubble 34 + 6, card 52 + 6)
  const STATUS_H = 26, RATE_H = 150;
  const RATES = [["MSC", "€4,660", "33 days", true], ["CMA CGM", "€4,800", "33 days"],
                 ["Maersk", "€4,940", "33 days"], ["MSC, via the alternate", "€5,080", "34 days"]];

  const $ = id => document.getElementById(id);
  const texts = g => [...g.querySelectorAll(":scope > text")];
  const byText = (root, s) => [...root.querySelectorAll("text")].find(e => e.textContent.trim().startsWith(s));
  const el = (tag, attrs) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  };
  // a clone of a template text, moved and re-worded; everything else (font, size, weight,
  // fill, tracking) stays the template's unless named
  const txt = (tpl, x, y, s, over = {}) => {
    const e = tpl.cloneNode(false);
    e.setAttribute("x", x); e.setAttribute("y", y); e.textContent = s;
    for (const k in over) over[k] === null ? e.removeAttribute(k) : e.setAttribute(k, over[k]);
    return e;
  };
  const width = e => e.getComputedTextLength();

  // ------------------------------------------------------------- set-up, once
  let S = null;
  function init() {
    const svg = document.querySelector("svg");
    const defs = el("defs", {});
    svg.insertBefore(defs, svg.firstChild);

    // anything sliding in stays inside the app window. Only while something slides: a clip
    // on the whole window softens its rounded corners, and the last frame must be the still.
    const dash = $("dashboard"), db = dash.getBBox();
    const dclip = el("clipPath", { id: "dash-clip" });
    dclip.appendChild(el("rect", { x: db.x - 1, y: db.y - 1, width: db.width + 2, height: db.height + 6, rx: 14 }));
    defs.appendChild(dclip);

    // a shine: grey text with an ink highlight sweeping across it. One look for every
    // "working" line in the scene.
    let nShine = 0;
    const shine = () => {
      const g = el("linearGradient", { id: `shine-${nShine++}`, gradientUnits: "userSpaceOnUse", x1: 0, x2: 0, y1: 0, y2: 0 });
      g.innerHTML = `<stop offset="0" stop-color="${GREY}"/><stop offset="0.5" stop-color="${INK}"/><stop offset="1" stop-color="${GREY}"/>`;
      defs.appendChild(g);
      return g;
    };

    // ---- the counters in "This morning"
    const counts = [];
    $("the-morning").querySelectorAll("text").forEach(e => {
      if (/^\d+$/.test(e.textContent.trim())) counts.push([e, +e.textContent.trim()]);
    });

    // ---- the Customs pop-up: a "working" pill in the "done" pill's shape, over the
    // finished state (the static slide is the finished state)
    const pop = $("popup-agent"), doneG = $("customs-done"), resG = $("customs-result");
    const ring = g => [...g.querySelectorAll(":scope > circle")].filter(c => +c.getAttribute("r") < 2.5);
    const centre = dots => [dots.reduce((a, c) => a + +c.getAttribute("cx"), 0) / dots.length,
                            dots.reduce((a, c) => a + +c.getAttribute("cy"), 0) / dots.length];
    const popDots = ring(pop), popC = centre(popDots);
    const doneRect = doneG.querySelector("rect"), doneText = doneG.querySelector("text");
    const workG = el("g", {});
    const workT = txt(doneText, 0, doneText.getAttribute("y"), "working…");
    workG.appendChild(workT); pop.appendChild(workG);
    const ph = +doneRect.getAttribute("height"), right = +doneRect.getAttribute("x") + +doneRect.getAttribute("width");
    const ww = Math.round(width(workT) + 18);       // build_07.pill(): text + 18
    const workR = el("rect", { x: right - ww, y: doneRect.getAttribute("y"), width: ww, height: ph, rx: ph / 2, fill: GREY_BG });
    workG.insertBefore(workR, workT);
    workT.setAttribute("x", right - ww / 2);
    const workShine = shine(); workT.setAttribute("fill", `url(#${workShine.id})`);
    const prep = txt(resG.querySelector("text"), resG.querySelector("text").getAttribute("x"),
                     resG.querySelector("text").getAttribute("y"), "Preparing the entry for France.");
    pop.appendChild(prep);

    // ---- the Ask box: the input line, the suggestion chip, the send button
    const inputG = $("chat-input");
    const input = byText(inputG, "Ask the desk anything");
    const inputFill = input.getAttribute("fill");
    const chipText = byText(inputG, Q2), chipRect = chipText.previousElementSibling;
    const chipFill = chipRect.getAttribute("fill"), chipInk = chipText.getAttribute("fill");
    const sendC = [...inputG.querySelectorAll("circle")].find(c => +c.getAttribute("r") === 15);
    const sendArrow = sendC.nextElementSibling;
    const caret = el("rect", { width: 1.5, height: 15, fill: INK, opacity: 0 });
    inputG.appendChild(caret);

    // ---- the conversation: the still's three items, and new ones cloned from them
    const qG = $("chat-question"), aG = $("chat-answer"), dG = $("chat-draft");
    const top = +qG.querySelector("rect").getAttribute("y");                // first item's top
    const win = $("chat-window").querySelector("rect");
    const inputTop = +inputG.querySelector("rect").getAttribute("y");     // the Ask box's shadow rect
    // what scrolls away disappears 2px above the first message, so nothing scrolled past
    // (the rate card's foot and shadow) is left showing at the top of the still
    const viewBottom = inputTop - 6, viewTop = top - 2;
    const vclip = el("clipPath", { id: "chat-view" });
    vclip.appendChild(el("rect", { x: win.getAttribute("x"), y: viewTop,
                                   width: win.getAttribute("width"), height: viewBottom - viewTop }));
    defs.appendChild(vclip);
    const scroller = el("g", { "clip-path": "url(#chat-view)" });
    inputG.parentNode.insertBefore(scroller, inputG);

    const aTop = +aG.querySelector("rect").getAttribute("y") - 3;          // the shadow sits 3 below
    const aCard = aG.querySelectorAll(":scope > rect")[1];
    const aTexts = texts(aG);
    const nameT = aTexts.find(e => e.getAttribute("fill") === BLUE);
    const liveT = aTexts.find(e => e.textContent === "LIVE");
    const bodyT = aTexts.find(e => e !== nameT && e !== liveT);
    const dTexts = texts(dG);
    const lineT = dTexts.find(e => e.getAttribute("font-size") === "11.5");
    const smallT = dTexts.find(e => e.textContent === "Draft ready");
    const ruleR = [...dG.querySelectorAll(":scope > rect")].find(r => r.getAttribute("height") === "1");
    const ringC = centre(ring(aG));

    // a question bubble, the still's own, re-worded; same padding either side
    const bubble = q => {
      const g = qG.cloneNode(true); g.removeAttribute("id");
      const r = g.querySelector("rect"), tx = g.querySelector("text");
      const q1r = qG.querySelector("rect"), q1t = qG.querySelector("text");
      const pad = (+q1r.getAttribute("width") - width(q1t)) / 2;
      const rightEdge = +q1r.getAttribute("x") + +q1r.getAttribute("width");
      tx.textContent = q;
      scroller.appendChild(g);
      const w = Math.round(width(tx) + 2 * pad);
      r.setAttribute("x", rightEdge - w); r.setAttribute("width", w); tx.setAttribute("x", rightEdge - w / 2);
      g.remove();
      return { g, natY: top, h: +q1r.getAttribute("height") };
    };
    // an agent at work: the card's ring and name on a bare line, the action shining
    const status = (who, what) => {
      const g = el("g", {});
      ring(aG).forEach(c => g.appendChild(c.cloneNode()));
      const n = txt(nameT, nameT.getAttribute("x"), nameT.getAttribute("y"), who);
      const w = txt(nameT, 0, nameT.getAttribute("y"), what + "…", { "font-weight": 400 });
      g.append(n, w);
      scroller.appendChild(g);
      w.setAttribute("x", +nameT.getAttribute("x") + width(n) + 6);
      const sh = shine(); w.setAttribute("fill", `url(#${sh.id})`);
      const box = w.getBBox();
      g.remove();
      // the line's top sits so the ring and name land where they do in a card
      return { g, natY: ringC[1] - STATUS_H / 2, h: STATUS_H, spin: ring(g), shine: [sh, box.x, box.width] };
    };
    // the Rate agent's card: the Milestones card, taller, with the draft's rule and lines
    const rateCard = () => {
      const g = aG.cloneNode(true); g.removeAttribute("id");
      g.querySelectorAll(":scope > rect").forEach(r => r.setAttribute("height", RATE_H));
      const [n, , b] = [texts(g).find(e => e.getAttribute("fill") === BLUE), 0,
                        texts(g).find(e => e.getAttribute("font-size") === "13")];
      n.textContent = "Rate agent";
      b.textContent = "Best of 8 options for 2 x 40HC, Shanghai to Rotterdam.";
      const x0 = +bodyT.getAttribute("x"), xr = +liveT.getAttribute("x"), by = +bodyT.getAttribute("y");
      const rule = ruleR.cloneNode(); rule.setAttribute("y", by + 10); g.appendChild(rule);
      scroller.appendChild(g);
      RATES.forEach(([carrier, price, days, best], i) => {
        const y = by + 28 + i * 17;
        if (best) g.appendChild(el("rect", { x: x0 - 8, y: y - 13, width: xr - x0 + 16, height: 18, rx: 5, fill: BLUE_BG }));
        const c = txt(lineT, x0, y, carrier, { fill: INK, "font-weight": best ? 600 : 500 });
        g.appendChild(c);
        if (best) g.appendChild(txt(liveT, x0 + width(c) + 8, y - 0.5, "BEST", { fill: BLUE, "text-anchor": null }));
        g.appendChild(txt(lineT, xr - 72, y, price, { fill: INK, "font-weight": 600, "text-anchor": "end" }));
        g.appendChild(txt(lineT, xr, y, days, { "text-anchor": "end" }));
      });
      const foot = txt(smallT, x0, by + 97, "Synthetic rate sheet, not market rates. Any quote is a draft you approve.",
                       { fill: GREY, "font-weight": 400, "text-anchor": null });
      g.appendChild(foot);
      const fits = foot.getBBox().x + foot.getBBox().width <= xr && by + 97 + 11 <= aTop + RATE_H + 3;
      g.remove();
      if (!fits) throw new Error("rate card overruns its box");
      return { g, natY: aTop, h: RATE_H };
    };
    const still = g => {
      const r = g.querySelector("rect");
      // a card's first rect is its shadow, 3 below its top
      const y = +r.getAttribute("y") - (r.getAttribute("fill-opacity") === "0.04" ? 3 : 0);
      const h = g === qG ? +r.getAttribute("height") : +g.querySelectorAll(":scope > rect")[1].getAttribute("height");
      return { g, natY: y, h };
    };

    const ITEMS = [
      { t0: T.send2, ...bubble(Q2) },
      { t0: 3.3, t1: 4.1, ...status("Assistant", "Routing it to the Rate agent") },
      { t0: 4.1, t1: 5.0, ...status("Rate agent", "Pricing 8 options from the rate sheet") },
      { t0: 5.0, ...rateCard() },
      { t0: T.send1, q1: true, ...still(qG) },
      { t0: 8.9, t1: 9.7, ...status("Assistant", "Routing it to the Milestones agent") },
      { t0: 9.7, t1: 10.5, ...status("Milestones agent", "Reading SHP-004 from the TMS") },
      { t0: 10.5, t1: 11.3, ...status("Routing agent", "Checking SHP-004 is on plan") },
      { t0: 11.3, ...still(aG) },
      { t0: 11.9, t1: 12.9, ...status("Milestones agent", "Drafting a reply to Pieter Claes") },
      { t0: 12.9, ...still(dG) },
    ];
    // each item: outer <g> places it, a clipped <g> reveals it as its slot opens, the
    // item itself fades and rises
    let nClip = 0;
    for (const it of ITEMS) {
      it.outer = el("g", {});
      const cp = el("clipPath", { id: `item-${nClip++}` });
      it.clipRect = el("rect", { x: win.getAttribute("x"), y: it.natY - 2, width: win.getAttribute("width"), height: 0 });
      cp.appendChild(it.clipRect); defs.appendChild(cp);
      it.clipG = el("g", {}); it.clipId = cp.id;
      it.outer.appendChild(it.clipG); it.clipG.appendChild(it.g);
      scroller.appendChild(it.outer);
    }
    S = { dash, counts, popDots, popC, workG, workShine, workBox: workT.getBBox(), prep, doneG, resG,
          input, inputFill, chipRect, chipText, chipFill, chipInk, sendC, sendArrow, caret,
          items: ITEMS, top, viewH: viewBottom - top, viewTop, viewBottom, scroller, scrollClip: scroller.getAttribute("clip-path") };
  }

  const sweep = (g, x, w, t) => {
    const c = x - 40 + ((t * 0.8) % 1) * (w + 80);
    g.setAttribute("x1", c - 30); g.setAttribute("x2", c + 30);
  };
  const press = (e, cx, cy, k) => e.setAttribute("transform", `translate(${cx} ${cy}) scale(${k}) translate(${-cx} ${-cy})`);

  window.scene = t => {
    if (!S) init();
    if (t < T.slidIn) S.dash.setAttribute("clip-path", "url(#dash-clip)");
    else S.dash.removeAttribute("clip-path");
    // counters: 0 to their value as "This morning" rises
    const pc = prog(t, 0.5, 1.4);
    for (const [e, v] of S.counts) e.textContent = String(Math.round(v * pc));

    const ang = (t * 300) % 360;
    // the Customs agent: working, then done with its result
    const pout = prog(t, T.customsDone, 0.2), pd = prog(t, T.customsDone + 0.2, 0.35);
    const cang = t < T.customsDone ? ang : (T.customsDone * 300) % 360 * (1 - pd);
    for (const d of S.popDots) d.setAttribute("transform", `rotate(${cang} ${S.popC[0]} ${S.popC[1]})`);
    S.workG.setAttribute("opacity", 1 - pout); S.prep.setAttribute("opacity", 1 - pout);
    S.doneG.setAttribute("opacity", pd); S.resG.setAttribute("opacity", pd);
    S.resG.setAttribute("transform", `translate(0 ${(1 - pd) * 4})`);
    sweep(S.workShine, S.workBox.x, S.workBox.width, t);

    // the Ask box: the chip pressed fills the input and sends; then Q1 is typed and sent
    const pressed = t >= T.chip && t < T.send2;
    S.chipRect.setAttribute("fill", pressed ? "#E8F1FF" : S.chipFill);
    S.chipText.setAttribute("fill", pressed ? BLUE : S.chipInk);
    let typed = "";
    if (t >= T.fill2 && t < T.send2) typed = Q2;
    if (t >= T.type1 && t < T.send1) typed = Q1.slice(0, Math.ceil(Q1.length * clamp((t - T.type1) / (T.send1 - T.type1 - 0.2))));
    S.input.textContent = typed || "Ask the desk anything";
    S.input.setAttribute("fill", typed ? INK : S.inputFill);
    const caretOn = t >= T.type1 - 0.6 && t < T.send1 && (t >= T.type1 || Math.floor(t * 2.5) % 2 === 0);
    S.caret.setAttribute("opacity", caretOn ? 1 : 0);
    if (caretOn) {
      const x = +S.input.getAttribute("x") + (typed ? S.input.getComputedTextLength() + 1.5 : 0);
      S.caret.setAttribute("x", x); S.caret.setAttribute("y", +S.input.getAttribute("y") - 11.5);
    }
    const pk = Math.min(prog(t, T.send2 - 0.15, 0.15) * (1 - prog(t, T.send2, 0.2)),
                        1) + Math.min(prog(t, T.send1 - 0.15, 0.15) * (1 - prog(t, T.send1, 0.2)), 1);
    const sc = 1 - 0.12 * pk, cx = +S.sendC.getAttribute("cx"), cy = +S.sendC.getAttribute("cy");
    if (pk > 0) { press(S.sendC, cx, cy, sc); press(S.sendArrow, cx, cy, sc); }
    else { S.sendC.removeAttribute("transform"); S.sendArrow.removeAttribute("transform"); }

    // the conversation: each item's slot opens, status lines give way to what they
    // produced, and the window scrolls. A sent question is pinned to the top, as a chat does.
    let total = 0, q1At = 0;
    for (const it of S.items) {
      const pin = prog(t, it.t0, 0.35), po = it.t1 ? prog(t, it.t1, 0.3) : 0;
      it.k = pin * (1 - po); it.pin = pin;
      if (it.q1) q1At = total;
      it.at = total;
      total += (it.h + GAP) * it.k;
    }
    total -= GAP;
    const scroll = Math.max(Math.max(0, total - S.viewH), q1At * prog(t, T.send1, 0.7));
    let straddle = false;
    for (const it of S.items) {
      const k = it.k, y = S.top - scroll + it.at;
      it.outer.setAttribute("transform", `translate(0 ${(y - it.natY).toFixed(3)})`);
      // wholly outside the view: hidden. Half in: the view's clip is needed this frame.
      const lo = y - 2, hi = y + (k >= 0.9999 ? it.h + 4 : (it.h + 8) * Math.max(k, 0));
      const out = hi <= S.viewTop || lo >= S.viewBottom;
      if (k > 0.001 && !out && (lo < S.viewTop || hi > S.viewBottom)) straddle = true;
      it.outer.setAttribute("visibility", k > 0.001 && !out ? "visible" : "hidden");
      if (k >= 0.9999) it.clipG.removeAttribute("clip-path");
      else {
        it.clipG.setAttribute("clip-path", `url(#${it.clipId})`);
        it.clipRect.setAttribute("height", ((it.h + 8) * k + 2).toFixed(3));
      }
      it.g.setAttribute("opacity", k >= 0.9999 ? 1 : k.toFixed(4));
      if (it.pin < 1) it.g.setAttribute("transform", `translate(0 ${((1 - it.pin) * 10).toFixed(3)})`);
      else it.g.removeAttribute("transform");
      if (it.spin) {
        const [ccx, ccy] = [it.spin.reduce((a, c) => a + +c.getAttribute("cx"), 0) / 8,
                            it.spin.reduce((a, c) => a + +c.getAttribute("cy"), 0) / 8];
        for (const d of it.spin) d.setAttribute("transform", `rotate(${ang} ${ccx} ${ccy})`);
      }
      if (it.shine) sweep(it.shine[0], it.shine[1], it.shine[2], t);
    }
    if (straddle) S.scroller.setAttribute("clip-path", S.scrollClip);
    else S.scroller.removeAttribute("clip-path");
  };
})();
