// Slide 07's live scene for animate.py: counters, a spinning agent ring, a shining
// "working…", and the Ask SQRlane chat played as a conversation.
// Every line is the product's own: ask.ask("Where is MEDU-1774390?") routes to the
// Milestones agent, which reads SHP-004 from the TMS link and asks Routing if it is on
// plan; its drafted reply is the desk's real reply to the same question in IN-106.
// ask.ask("Price 2 x 40HC Shanghai to Rotterdam") routes to the Rate agent, which prices
// 8 options from the synthetic rate sheet. Dates are left out: the bookings age forward.
// window.scene(t) is a pure function of t, so every frame can be rendered on its own.
(function () {
  const ease = x => 1 - Math.pow(1 - x, 3);
  const clamp = x => Math.max(0, Math.min(1, x));
  const prog = (t, t0, d = 0.35) => ease(clamp((t - t0) / d));
  const BLUE = "#006BFF", INK = "#0A0A0A", MUT = "#6B6B6B", AMB = "#96580A";
  const byText = (root, s) => [...root.querySelectorAll("text")].find(e => e.textContent.trim().startsWith(s));

  // ------------------------------------------------------------- the conversation
  const Q1 = "Where is MEDU-1774390?", Q2 = "Price 2 x 40HC Shanghai to Rotterdam";
  const T = { type1: 2.6, send1: 3.7, chip: 9.3, send2: 10.0 };
  const ITEMS = [
    { t0: 3.7, html: bubble(Q1) },
    { t0: 4.0, t1: 4.9, html: status("Assistant", "Routing it to the Milestones agent") },
    { t0: 4.9, t1: 5.8, html: status("Milestones agent", "Reading SHP-004 from the TMS") },
    { t0: 5.8, t1: 6.6, html: status("Routing agent", "Checking the route for risk") },
    { t0: 6.6, html: answer("Milestones agent",
        "SHP-004, Shenzhen to Antwerp, is on plan. No active risk on its route, 2 days of slack.") },
    { t0: 7.2, t1: 8.4, html: status("Milestones agent", "Drafting a reply to Pieter Claes") },
    { t0: 8.4, html: draft() },
    { t0: 10.0, html: bubble(Q2) },
    { t0: 10.3, t1: 11.1, html: status("Assistant", "Routing it to the Rate agent") },
    { t0: 11.1, t1: 12.2, html: status("Rate agent", "Pricing 8 options from the rate sheet") },
    { t0: 12.2, html: rates() },
  ];

  function ring(size) {
    let c = "";
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4, r = size * 0.36;
      c += `<circle cx="${(size / 2 + r * Math.cos(a)).toFixed(1)}" cy="${(size / 2 + r * Math.sin(a)).toFixed(1)}" r="${(size * 0.1).toFixed(1)}" fill="${BLUE}" fill-opacity="${(0.3 + 0.09 * i).toFixed(2)}"/>`;
    }
    return `<svg class="spin" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}"><g>${c}</g></svg>`;
  }
  function bubble(q) {
    return `<div style="display:flex;justify-content:flex-end"><div style="background:${INK};color:#fff;border-radius:18px;padding:8px 16px;font-size:13.5px;font-weight:500">${q}</div></div>`;
  }
  function status(who, what) {
    return `<div style="display:flex;align-items:center;gap:8px;padding:4px 4px;font-size:12.5px">${ring(14)}
      <span style="font-weight:600;color:${BLUE}">${who}</span><span class="shine">${what}…</span></div>`;
  }
  function card(inner, w = 520) {
    return `<div style="width:${w}px;background:#fff;border:1px solid rgba(10,10,10,.10);border-radius:14px;padding:11px 16px;box-shadow:0 3px 0 rgba(10,10,10,.03)">${inner}</div>`;
  }
  function head(who) {
    return `<div style="display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;color:${BLUE}">${ring(14)}${who}
      <span style="margin-left:auto;font-size:10px;font-weight:700;letter-spacing:.8px;color:#0F7B3F">LIVE</span></div>`;
  }
  function answer(who, text) {
    return card(`${head(who)}<div style="margin-top:5px;font-size:13px;color:${INK}">${text}</div>`);
  }
  function draft() {
    return card(`${head("Milestones agent")}
      <div style="margin-top:8px;border:1px solid rgba(10,10,10,.10);border-radius:10px;padding:9px 12px;background:#FCFCFC;font-size:11.5px;color:${MUT};line-height:1.5">
        <div><b style="color:${INK};font-weight:600">To</b>&nbsp; Pieter Claes, Kempen Electronics &nbsp;·&nbsp; <b style="color:${INK};font-weight:600">Cc</b>&nbsp; logistics-planning</div>
        <div style="color:${INK};font-weight:600;font-size:12.5px;margin:2px 0">RE: Where is MEDU-1774390?</div>
        <div>MEDU-1774390 (electronics) is on the water on Asia → Suez → Antwerp, discharging at Antwerp. We will tell you straight away if it moves.</div>
      </div>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;margin-top:8px">
        <span style="font-size:11px;font-weight:600;color:${AMB}">Draft ready</span>
        <span style="background:${INK};color:#fff;border-radius:8px;padding:5px 14px;font-size:12px;font-weight:600">Approve</span></div>`);
  }
  function rates() {
    const rows = [["MSC", "4,660", "33 days", true], ["CMA CGM", "4,800", "33 days"], ["Maersk", "4,940", "33 days"],
                  ["MSC, via the alternate", "5,080", "34 days"]];
    const tr = rows.map(([c, p, d, best]) => `<div style="display:flex;padding:4px 8px;border-radius:6px;${best ? "background:#E8F1FF" : ""}">
        <span style="flex:1;color:${INK};font-weight:${best ? 600 : 500}">${c}${best ? ` <span style="font-size:10px;color:${BLUE};font-weight:700;margin-left:6px">BEST</span>` : ""}</span>
        <span style="width:90px;text-align:right;color:${INK};font-weight:600">€${p}</span><span style="width:80px;text-align:right;color:${MUT}">${d}</span></div>`).join("");
    return card(`${head("Rate agent")}<div style="margin:6px 0 2px;font-size:12px;color:${MUT}">2 x 40HC Shanghai to Rotterdam, priced from the rate sheet</div>
      <div style="font-size:12.5px">${tr}</div>
      <div style="margin-top:6px;font-size:10.5px;color:#9A9A9A">Synthetic rate sheet, not market rates. A quote goes out only as a draft you approve.</div>`, 520);
  }

  // ------------------------------------------------------------- set-up, once
  let S = null;
  function init() {
    const svg = document.querySelector("svg");
    for (const id of ["chat-question", "chat-answer", "chat-draft"]) document.getElementById(id).style.display = "none";
    const counts = [];
    document.querySelectorAll("#the-morning text").forEach(el => {
      if (/^\d+$/.test(el.textContent.trim())) counts.push([el, +el.textContent.trim()]);
    });
    // the agent ring in the pop-up: its eight small dots
    const pop = document.getElementById("popup-agent");
    const dots = [...pop.querySelectorAll("circle")].filter(c => +c.getAttribute("r") < 2.5);
    const rcx = dots.reduce((a, c) => a + +c.getAttribute("cx"), 0) / dots.length;
    const rcy = dots.reduce((a, c) => a + +c.getAttribute("cy"), 0) / dots.length;
    // "working…" shines: a gradient swept across it
    const work = byText(pop, "working");
    const wb = work.getBBox();
    const NS = "http://www.w3.org/2000/svg";
    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML = `<linearGradient id="shine-g" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="0" y2="0">
      <stop offset="0" stop-color="#A3A3A3"/><stop offset="0.5" stop-color="${BLUE}"/><stop offset="1" stop-color="#A3A3A3"/></linearGradient>`;
    svg.insertBefore(defs, svg.firstChild);
    // anything sliding in stays inside the app window
    const dash = document.getElementById("dashboard"), db = dash.getBBox();
    const cp = document.createElementNS(NS, "clipPath"); cp.id = "dash-clip";
    cp.innerHTML = `<rect x="${db.x - 1}" y="${db.y - 1}" width="${db.width + 2}" height="${db.height + 6}" rx="14"/>`;
    defs.appendChild(cp); dash.setAttribute("clip-path", "url(#dash-clip)");
    work.setAttribute("fill", "url(#shine-g)");
    // the input line and the suggestion chip
    const input = byText(document.getElementById("chat-input"), "Ask the desk anything");
    const chipText = byText(document.getElementById("chat-input"), Q2);
    const chipRect = chipText.previousElementSibling;
    // the chat overlay, inside the chat window, above the input
    const cw = document.getElementById("chat-window").getBBox();
    const ci = document.getElementById("chat-input").getBBox();
    const box = document.createElement("div");
    const top = cw.y + 10, h = ci.y - top - 8;
    box.style.cssText = `position:absolute;left:${cw.x + 16}px;top:${top}px;width:${cw.width - 32}px;height:${h}px;overflow:hidden;font-family:Geist;`;
    const col = document.createElement("div");
    col.style.cssText = "display:flex;flex-direction:column";
    box.appendChild(col); document.body.appendChild(box);
    const items = ITEMS.map(it => {
      const wrap = document.createElement("div");
      wrap.style.cssText = "overflow:hidden";
      const inner = document.createElement("div");
      inner.innerHTML = it.html; inner.style.paddingBottom = "8px";
      wrap.appendChild(inner); col.appendChild(wrap);
      return { ...it, wrap, inner, h: inner.getBoundingClientRect().height };
    });
    S = { counts, dots, rcx, rcy, work, wb, input, chipRect, chipFill: chipRect.getAttribute("fill"), col, items, viewH: h };
  }

  function shineHtml(el, t) {
    el.style.background = `linear-gradient(90deg,#A3A3A3 0%,#A3A3A3 35%,${INK} 50%,#A3A3A3 65%,#A3A3A3 100%)`;
    el.style.backgroundSize = "300% 100%";
    el.style.backgroundPosition = `${100 - ((t * 0.9) % 1) * 100}% 0`;
    el.style.webkitBackgroundClip = "text"; el.style.color = "transparent";
  }

  window.scene = t => {
    if (!S) init();
    // counters: 0 to their value as "This morning" rises
    const pc = prog(t, 0.5, 1.4);
    for (const [el, v] of S.counts) el.textContent = String(Math.round(v * pc));
    // the agent ring turns, the "working…" shines
    const ang = (t * 300) % 360;
    for (const d of S.dots) d.setAttribute("transform", `rotate(${ang} ${S.rcx} ${S.rcy})`);
    const sweep = S.wb.x - S.wb.width + ((t * 0.7) % 1) * S.wb.width * 3;
    const g = document.getElementById("shine-g");
    g.setAttribute("x1", sweep - 30); g.setAttribute("x2", sweep + 30);
    // the input: Q1 typed, sent; the chip pressed, Q2 sent
    let typed = "";
    if (t >= T.type1 && t < T.send1) typed = Q1.slice(0, Math.ceil(Q1.length * clamp((t - T.type1) / (T.send1 - T.type1 - 0.15))));
    if (t >= T.chip && t < T.send2) typed = Q2;
    S.input.textContent = typed || "Ask the desk anything";
    S.input.setAttribute("fill", typed ? INK : "#9A9A9A");
    S.chipRect.setAttribute("fill", t >= T.chip - 0.25 && t < T.send2 ? "#E8F1FF" : S.chipFill);
    // the conversation: each line grows in, status lines give way, the window scrolls
    let total = 0;
    for (const it of S.items) {
      const pin = prog(t, it.t0, 0.35), pout = it.t1 ? prog(t, it.t1, 0.3) : 0;
      const k = pin * (1 - pout);
      it.wrap.style.height = `${(it.h * k).toFixed(2)}px`;
      it.inner.style.opacity = k;
      it.inner.style.transform = `translateY(${(1 - pin) * 10}px)`;
      total += it.h * k;
      it.inner.querySelectorAll(".spin g").forEach(gg => gg.setAttribute("transform", `rotate(${ang} 7 7)`));
      it.inner.querySelectorAll(".shine").forEach(el => shineHtml(el, t));
    }
    S.col.style.transform = `translateY(${-Math.max(0, total - S.viewH)}px)`;
  };
})();
