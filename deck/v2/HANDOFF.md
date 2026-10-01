# Deck v2 redesign: handoff

Read this first. It carries everything decided so far in the redesign of the SQRlane
pitch deck, so a new session can continue without the old conversation.

Branch: `claude/intelligent-planck-1ma092`. Work, commit and push here.

## The job

The owner (no coding experience) is redesigning the investor deck **one slide at a
time**. The source was a Figma Slides deck exported to PDF (11 pages; pages 10 and 11
were another company's (Zeit AI) slides and are **cut**). For each slide: build it,
render it, look at it, fix collisions, commit, push, send the preview PNG and the SVG
with `SendUserFile`, then wait for feedback. Do not build ahead.

Output: one **editable SVG per slide, 1920x1080**, for import into Figma.

## Status

| # | File | Status |
|---|---|---|
| 01 | `slide-01-cover.svg` (hand-written, no builder) | final |
| 02 | `build_02.py` → `slide-02-introduction.svg` | final |
| 03 | `build_03.py` → `slide-03-the-what.svg` | final |
| 04 | `build_04.py` → `slide-04-the-why.svg` | final |
| 05 | `build_05.py` → `slide-05-the-job-1.svg` | final |
| 06 | `build_06.py` → `slide-06-the-job-2.svg` (version A, the owner's pick) | final |
| 07 | `build_07.py` → `slide-07-the-how-1.svg` (rebuilt: the desk) | built, awaiting feedback |
| 08 | `build_08.py` → `slide-08-the-how-2.svg` (the risk layer) | built, awaiting feedback |
| 09 | `build_09.py` → `slide-09-integrations.svg` (integrations) | built, awaiting feedback |
| 10 | `build_10.py` → `slide-10-who-am-i.svg` (option A, the proof stack) | final draft, all logos in; awaiting the owner's review |
| A | Appendix: sources for slide 06 (`SOURCES` list in `build_06.py`) | later, not now |

Slide 06 version B (callout map + takeaway strip) was deleted from the repo; it lives
in git at `d4af2cc:deck/v2/slide-06-the-job-2-b.svg` if the owner asks again.

## Slide 07, current version (fourth rebuild, 2026-09-30)

- **Left, the Today view (sixth pass):** sidebar with counts; a bell with a red badge in
  the app bar; beside the "Today" title, **two pop-ups** joined by an arrow: the Outlook
  mail (IN-111, Maison Cardelle, arrival notice MEDU-2209471) and "Customs agent ·
  working… Preparing the entry for France." (its finished output is "Entry prepared for
  France. Not filed."). **"This morning"** in one line with a coloured tag under each
  figure: 13 mails in (8 end to end, green) › 100 agent messages (on record, blue) › 8
  Playbook fixes (checked, amber) › 24 waiting for you (you decide, blue) › 0 sent or
  written (until you approve, green). Then the **chat window** laid out like the owner's
  reference: tinted body, the question bubble, a Milestones agent card (LIVE), the draft
  card "Drafted a reply to Pieter Claes, Kempen Electronics." with the real IN-106 reply,
  "Draft, not sent" and Approve, and the input with the paperclip and "Ask SQRlane".
  Three suggested questions sit as chips inside the Ask box, above the input line. The dashboard keeps the product's bright blue (owner's choice); the right panel uses the same bright blue.
- **Risk layer band** fades out to the right (a white gradient over its right half), on
  the owner's instruction.
- **The "Demo run · synthetic inbox" label was removed on the owner's instruction.** The
  figures are still counts from one run on the synthetic inbox, so say that out loud when
  presenting. The remaining disclosures: "14 live · Planner scripted · TMS link demo" in
  the right panel, and "Queued, not written" on the agent card.
- **Right, "How the work is structured":** the second version's panel, restored at the
  owner's request, with the risk layer in light grey and an agent-count chip on every
  step. Colour has one job each: **blue = an agent** (the bright #006BFF, same as the dashboard; the muted blue was tried and undone on the owner's call) (every count chip, as in the Ask
  box), **amber = the Playbook's check** (band, ticks, "sends it back"), **black = the one
  thing a person does: approve** ("You approve" is the only black block). Inbox,
  Assistant and the TMS link are white cards; step numbers are grey.
- Closing line: "Ask the desk anything. Every step recorded, and approved by you."
  "Built for the 40%" is gone.

## Slide 08, the risk layer (second pass, 2026-09-30)

Same frame as slide 07. Left, the Risk view: bell; pop-ups with the official **NDR mark**
(simple-icons, CC0, added to `channel_marks.json`), "Regional source · NDR Hamburg,
Warnstreik im Hamburger Hafen", then "Risk agent · working… Checking 7 bookings against
it."; "This run": 60 sources watched (live) › 1 event (strike, high) › 3 decisions (2
reroute, 1 hold) › **€46,500 cost avoided** (vs doing nothing) › 0 sent or written. The
decisions: SHP-001 rerouted via Rotterdam (12 Oct, due 14 Oct); the Comms agent's mail to
Katrin Vogel ("Draft ready", Approve); SHP-002 held - "Hold the boxes instead of
discharging into the strike" - with the hold instruction to Maersk and the notice to
Nordmed Pharma drafted. Under them: "Cost avoided = €141,100 if nothing is done, minus
€94,600 with these calls. From each synthetic booking's own terms." (`today.at_stake`;
SHP-001 avoids €29,196, SHP-005 €17,304, SHP-002 €0 - the hold saves nothing, it only
tells people early). Right: WATCH with the six families, then "Coming live soon" -
AIS vessel positions, freight indices, prediction markets, port calls - as dashed chips
fading out; then Risk, Routing, Comms, Planner (scripted) on one uniform grid; the desk
faded; You approve → TMS link; the detection trail (demo scenario).

Fourth pass (owner's notes): no highlight box on the €46,500 in the dashboard; the working
Risk agent keeps a thin, light blue outline (0.8px, 45%); the cost impact is one row on the
agents' grid, under Routing, in light green: "Cost impact · −€46,500 · €141,100 if nothing
is done, €94,600 with these calls" (the two-bar version took too much room). Both drafts end
in the same "Draft ready" + Approve pair.

Fifth pass: the cost impact row has the same gap and arrow as the others and a green
gradient fading right; a green dot marks the 60 live sources, a grey dot "Coming soon".
A "Confidence, building" grid (from the Hamburg trail) was tried top right and removed on the owner's instruction.

"Draft, not sent" now reads "Draft ready" on slides 07 and 08, on the owner's instruction;
the Approve button still carries the gate, and nothing is ever sent.

## Slide 09, integrations (second version, rebuilt from scratch, 2026-09-30)

The owner rejected the first version (a TMS-link dashboard mock; in git at `e1f3feb`) and
asked for: less text, cleaner, the Zauber/Peec integration stack, logos in an orbit
around each agent, and a neural-network flow of how the agents talk. Now: headline
"Works inside the tools you already run.", subline "Each agent works where its job
already lives. They all talk on one bus." Eight agent nodes on an ellipse round a black
SQRlane centre ("16 agents · one bus"); faint dashed spokes to the centre are the bus;
blue curves with message dots are real handoffs (Inbox→Docs/Rate/Playbook,
Docs→TMS link, Rate→Playbook, Playbook→Comms, Risk→TMS link/Comms,
Assistant→TMS link/Risk). Orbits: Inbox (Outlook, Gmail), Docs (PDF, Word, Excel,
image, XML), Playbook (Word, OneDrive, Google Drive), Rate (Excel, Google Sheets), TMS
link (CargoWise icon clipped from its wordmark, SAP, Oracle, Descartes), Comms (Teams,
Slack, WhatsApp, WeChat), Assistant (Claude, Cursor, VS Code, via MCP), Risk (NDR, DW,
NASA, +57). One grey line at the foot: live today are the 60 sources and MCP; TMS and
mail are read from exports and files; native links come next.

Owner's notes (2026-10-01): logos bigger (bubbles 56px, marks 30px, orbits widened) and
the dashed spokes to the centre removed. Open question put to the owner: the blue links
read as random; options proposed are in the session reply (work-order ring, one real
thread highlighted with its messages).

Third version (2026-10-01, owner's go on "work order + IN-108"): nine agents spaced evenly
along the ring (by arc length, not angle) in work order, clockwise from the left: Inbox,
Booking (new, no tools), Docs, Rate, Playbook, TMS link, Comms, Assistant, Risk. Other real
handoffs are faint grey; the **IN-108 thread** is drawn bold with numbered steps on the
edges, and its messages sit in a card top right ("One mail, IN-108"): 1 Inbox→Booking
"Booking request · Nordmed Pharma", 2 Docs→Booking "7 fields read", 3 Rate→Booking "Best:
ONE · €3,880", 4 Playbook→Booking (amber) "ONE not approved · use Maersk or Hapag-Lloyd",
5 Playbook→TMS link "Rebooked Hapag-Lloyd · queued for you". Logos uniform and larger
(circles r=31, marks 34px; all TMS wordmark pills 128px wide). The Assistant's ring now
holds Claude, ChatGPT (openai-icon) and Codex (both from @iconify-json/logos) and Cursor;
VS Code and XML dropped for room.

**Models, re-picked "strong" on the owner's request** - the strong end of the options
the whitepaper already gives, plus a vision model where the job needs one: Inbox and
Assistant Gemma-3-27B (whitepaper: "Qwen3.5-9B or Gemma-3-27B"); Risk Qwen3-235B
(multilingual prose, few calls per run); Comms Llama-3.3-70B; Playbook Qwen3-235B (turns
a customer's written SOP into checkable rules; the checks stay code); Docs Qwen2.5-VL-72B
(scanned PDFs and photos need vision - the whitepaper says so but names no model, so this
pick is new); Booking, Rate and TMS link code only (prices and records must be exact).
**The whitepaper's agent table still lists the smaller picks** - align it if these stay.

**Colour pass** (owner: "the deck is brown, this slide was very blue"): blue now marks only
an agent (the dot-ring icons); lines, arrows and the bus are ink grey; agent boxes have the
plain card border; layer labels are brown small caps; the decision path (bus → You approve
→ TMS link → the TMS row) and the "+ any TMS" chip are amber #96580A / #F6EEE3.

**Three layers, second pass** (owner's go on the recommended set): arrowheads show work
flowing down from each tool group to its agents and from the bus to the TMS; a black **You
approve** pill sits on that last line; the model chips came off this slide (the whitepaper
holds them); each tool card ends in "+ more" ("+ any MCP client" for AI assistants, "+ 57
more" for Sources); the bottom layer is "ANY TMS, BY EXPORT OR API" - the TMS link with
CargoWise, SAP, Oracle and Descartes, then plain name chips (no official marks) for Riege
Scope, AEB, DAKOSY, Portbase, "Freight exchanges" TIMOCOM and Transporeon, and a dashed
"+ any TMS with an export or API". One footnote: logos are examples; live today the 60
sources and MCP; the TMS is read from an export or its API and approved changes go back
the same way; native connectors next. Never write "custom integrations built for your
stack" - no such onboarding exists.

**Current version: three layers** (2026-10-01, the owner's pick of four proposed layouts;
the network ring before it is in git at the previous commits). Top, YOUR TOOLS in six
grouped cards, each directly above the agents that use it: Mail (Outlook, Gmail) over
Inbox; Documents (PDF, Word, Excel, image) over Booking and Docs; Sheets & files (Google
Sheets, OneDrive, Google Drive) over Rate and Playbook; Chat (Teams, Slack, WhatsApp,
WeChat) over Comms; AI assistants (Claude, ChatGPT, Cursor - Codex removed on the owner's
note) over Assistant; Sources (NDR, DW, NASA, +57) over Risk. Middle, eight agents in work
order with their model chips, every one dropping onto one blue bus ("SQRlane · 16 agents on
one bus · every handoff between them recorded"; the other seven named at the right).
Bottom, YOUR TMS: the TMS link (code only) on the bus, with CargoWise, SAP, Oracle and
Descartes on one line through it. Every logo the same size (r=22 circle, 28px mark). The
IN-108 card was removed on the owner's note. Write "&amp;" in any label: a bare "&"
blanked this slide once more.

Not shown, on purpose: SharePoint and BBC (their marks were withdrawn from simple-icons,
so there is no official file to inline) and the rate-management vendors in the Zauber
reference (no official marks, and SQRlane prices from a rate sheet, not an RMS). New
marks in `channel_marks.json`: PDF, Word, Excel, Image, XML (vscode-icons, MIT),
OneDrive, Google Drive, Cursor, VS Code, Claude (logos, CC0), Google Sheets, DW, NASA,
MCP (simple-icons, CC0, brand hex filled in for `currentColor`).

## Slide 10, who am I (third pass, 2026-10-01)

Four founder layouts were previewed as an artifact (A proof stack, B the bet, C built not
planned, D the team this round builds); the owner picked **A**, then gave notes twice.

- **Header:** "08 · WHO AM I", "Seen the gap. Built the product. Mapped the buyers.", "One
  founder. Every proof here is already done."
- **Top left, the founder card (horizontal):** the owner's photo (`people/abir-khan.jpg`,
  cropped 4:5 from the file they sent, rounded by a clip), **Abir Khan**, "Founder,
  SQRlane", then EXPERIENCE: "Shaped the investment thesis of a VC fund." (**the $170M
  figure was removed on the owner's instruction** - do not put it back) and "Advised Fortune
  500 CEOs on restructuring liabilities above $100M."; on the foot, LinkedIn's official mark
  (logos set, CC0) and linkedin.com/in/khan-abir, wrapped in an `<a href>` to
  https://www.linkedin.com/in/khan-abir/ (Figma may drop the link on import; re-add it on
  the text). No QR code.
- **Top right, three linked tiles** (the owner found tick rows boring), joined by chevron
  circles, each a label, a picture, a hairline, one bold line and one grey line:
  Seen the gap - a three-step bar with square corners (owner's note), ALERT (risk tools) /
  DECIDE (nobody, amber) / ACT (execution), "That is my bet." / "Nobody owns the step
  between."; Built the product - two stat rows split by a hairline, "14 · Live agents · of
  16 agents" and "60 · Live sources · in six families" (side by side the figures read as
  one number, "14 60", which the owner caught), figures left on the content edge, each
  label led by a green live dot with a soft halo (#0F7B3F, the deck's live green), "Runs
  today, end to end." / "Every change waits for you."; Mapped the buyers - three equal steps, Forwarder ICP list →
  Enriched in Apollo → Events lined up, "Next: outreach." / "The groundwork is done." The
  Apollo list is confirmed as SQRlane's own work.
- **One grid for the top row** (owner: "make sure alignments are uniform"): all four cards
  use 32 px padding; the tile labels' squares start at the photo's top; every picture is
  centred on one line (`HC`) and the joins sit on it; one hairline (`FOOT_RULE`) runs at
  the same height through all four cards; the bold lines and the LinkedIn link share a
  baseline (`BOLD_BASE`); the grey lines sit level with the photo's foot (`LAST_BASE`).
  Change a line in one place and every card follows.
- **Logo band, one horizontal row** (owner: "instead of vertical, keep it horizontal"):
  Education (Nova SBE, CEMS MIM), Work (Alvarez &amp; Marsal, SCAILE, Biome VC),
  Institutions (UN Foundation, Manage and More, Hack-Nation). Logos sit at their natural
  width and an optical height set by eye (`LOGO_H`); the three groups share the free space
  equally around two dividers.
- **Logos are the owner's own files** in `deck/v2/logos/`: cropped to the mark, the ones
  that came on white made transparent (colour-to-alpha against white), capped at 210 px
  tall. Nothing redrawn. SCAILE's file is small (204 x 47 px); ask for a larger one.
- **All eight logos are in** (the last four arrived on the third try as attachments). UN
  Foundation came on a light grey ground and Hack-Nation and Manage and More on white; all
  made transparent against their own ground. **Biome came only as white on navy**, which
  would vanish on the white band: the navy was made transparent and the white wordmark
  recoloured to that same navy (#1B293C), the coral mark untouched, and the cut-off tagline
  under the word cropped away. If Biome supplies an official dark-on-light file, use it.
- Closing line: "I've helped shape a fund's thesis. This is the company I'd back."
- `build_10.py` measures every string against Geist (PIL, variable font) and stops on an
  overrun.

## Motion: slides 07 and 08 as videos (2026-10-01)

Figma drops SVG animation on import, so `animate.py` renders motion to MP4 for Figma
Slides: it opens the slide's own SVG in headless Chromium, hides the listed layers and
reveals them on a timeline (rise, drop, slide in, pop), captures 30 fps at 2x (3840x2160, 4K, so small text stays sharp in Figma and on a projector) and encodes H.264 High at
level 5.1, CRF 12, BT.709. **Level 5.1 is checked on every file**: the first renders were
level 6.0 (-tune animation doubles the reference frames, past 5.1's buffer at 4K), which many
players and Figma will not play; `-refs 4` keeps it inside 5.1
(`slide-07-the-how-1.mp4` and `slide-07-the-desk.mp4` 16 s, `slide-08-the-how-2.mp4` and
`slide-08-the-desk.mp4` 18 s,
ending on the finished slide so they loop). The arrow drawn just before a layer arrives with it. Chat messages
and decision cards are their own named layers now (`chat-question`, `chat-answer`,
`chat-draft`, `chat-input`, `decision-reroute`, `decision-mail`, `decision-hold`); the
static slides are pixel-identical. **After any change to slide 07 or 08, re-run
`python3 animate.py 07 07-desk 08 08-desk`** (pip: playwright, imageio-ffmpeg, pillow). In Figma, upload the MP4
onto the slide with autoplay and loop; it plays in presentation mode, not in grid view.

**Slide 07 video, third version (16 s), and the desk on its own (2026-10-01).** The owner
asked for "only this part" - the dashboard - as a video, with "the font style, size, and
shape uniform across all". The second version drew its chat in HTML: cards 552 px wide
against the still's 480, a mail preview laid out differently from the still's draft card,
and a last frame (the rate table) that was not the slide. So `scene_07.js` was rewritten:

- **Nothing in it is drawn in a style of its own.** Every new line is a clone of an element
  `build_07.py` drew - the question bubble, the agent card and its ring, name, LIVE tag and
  body, the draft's rule, lines and "Draft ready" - re-worded, so font, size, weight,
  radius, border, shadow and card width are the slide's. The rate card is the Milestones
  card made 150 px tall; status lines are that card's ring and name on a bare line, so
  they sit on the cards' own x. The Customs "working" state is a grey pill in the "done"
  pill's shape. One shine (grey text, an ink highlight) for every "working" line.
- **The conversation runs rate question first.** The chip "Price 2 x 40HC Shanghai to
  Rotterdam" is pressed and sent; Assistant routes it, the Rate agent prices 8 options,
  the rate card lands (MSC €4,660 best, CMA CGM €4,800, Maersk €4,940, MSC via the
  alternate €5,080; synthetic rate sheet). Then "Where is MEDU-1774390?" is typed and sent;
  the chat scrolls it to the top, as a chat does; Assistant routes it, Milestones reads
  SHP-004 from the TMS, Routing checks it is on plan, the answer lands, "Drafting a reply
  to Pieter Claes", the draft lands. Those three items are the still's own groups, moved,
  so **the last frame is the static slide**. All from `ask.ask()` and the IN-106 draft; no
  dates. The Customs pop-up works from 1.8 s and shows its result at 6.2 s.
- **`animate.py` checks it**: it renders the finished slide on its own and fails if the
  last frame differs by a single pixel. It loads Geist from `static/fonts/` with
  `@font-face`, so no machine renders a video in a fallback font, and fails if it does
  not load.

Outputs: `slide-07-the-how-1.mp4` (the whole slide, 3840x2160) and
**`slide-07-the-desk.mp4`** (`python3 animate.py 07-desk`): the dashboard alone with a
12 px margin of slide background - x 84, y 294, 1024 x 608 on the slide - at 3.5x, so
3584x2128: the largest size at this aspect inside 4K UHD with both sides a multiple of 16.
Placed at that box on slide 07 in Figma it sits exactly over the static mock.

**Slide 08 video, the risk layer on its own (2026-10-01, 18 s).** The owner asked for the
window only, with slide 07's lessons, plus "the agents output or findings based on the
event trigger", "a sense of urgency or heightened awareness when a news like that pops in",
and "a scroll down effect and preview of what the agents have built, prepared or drafted".
`scene_08.js` plays it, cloned from the still like slide 07's scene, and `animate.py 08-desk`
crops the same 1024 x 608 window (`slide-08-the-desk.mp4`, 3584x2128); `animate.py 08`
renders the whole slide from the same scene, its right-panel rows arriving as each agent
starts work.

- **The alert (0.5 s):** the NDR headline drops in; its badge and the bell ping in red
  three times (the bell's ring sits round the bell, inside the window), the card's outline pulses red, the bell rings, and the sidebar's Risk count
  turns red. All of it settles by 3.8 s.
- **The finding (3.0 s):** the Risk agent's card, re-worded from the reroute card: "3 of 7
  bookings call at Hamburg. Up to 5 days late.", the seven bookings as pills, SHP-001,
  SHP-002 and SHP-005 in red, "4 stay on plan", a red "high" pill, and "23 h before the
  international wires" (the demo scenario's trail). Then Routing weighs slack, the reroute,
  Comms drafts, the mail, Routing finds no better route for SHP-002, the hold. "This run"
  and the Approvals count tick up as the agents produce them (18 = 6 drafts + 12 changes).
- **The preview (10 s):** the thread scrolls down past the cost line to PREPARED FOR YOU:
  the carrier amendment to Hapag-Lloyd (the run's draft), a Slack heads-up for the ops
  channel, and the TMS link's record for SHP-001 (the run's five field changes and the two
  drafts on the communication log, old values struck through, "Queued, not written" +
  Approve); then it scrolls home and rests on the still.
- **The Slack heads-up is the one thing the build does not draft.** Its words are the
  run's (2 reroutes, 1 hold, 6 drafts and 12 TMS changes), it carries the same Draft
  ready + Approve gate, and it is there because slide 09 names chat as where the Comms
  agent's work goes next. Say so if asked. Mail stays on the Outlook mark the slide uses.
- The Risk agent's ring and shine are timed to rest exactly on the still at the last
  frame (`window.LAST_T`, which `animate.py` now passes, with `window.MARKS` from
  `channel_marks.json` for the Slack mark).

**Slide 07 right panel, one rhythm** (owner: fill the white space, uniform and aligned):
every row 46 px, every arrow gap 18 px, stage cards 95 px, so the panel fills to its foot
(an assert in `build_07.py` stops the build if it overruns). Assistant and TMS link start
on the desk's third column, Inbox and You approve end at the same edge; the two narrow
boxes carry their description on a second line.

## The 40%: replaced by Asana's 58% (2026-09-30, on the owner's instruction)

Where it came from: the old web deck says "60% goes to coordination, only 40% goes to the
skilled work (Asana 2022)". The v2 deck took the 40% skilled-work share and labelled it
"admin", which is the wrong way round. On top of that, 60% is Asana's 2021 figure; the
2022 index says **58%** of the day goes to coordination, 33% to skilled work and under 10%
to strategy (10,624 knowledge workers, Germany included, not forwarders specifically).
`docs/problem-brief.md` now says so, so the error cannot creep back.

- **Slide 02:** the bar reads "58% coordination" against "the actual job", with Asana's
  own definition under it (chasing status, searching for information, switching apps)
  and the source. The closing line changed from "is stuck doing data entry." to "is stuck
  chasing status." so the claim matches its source.
- **Slide 03:** "58% of the day on coordination" and "€19,700 per desk, per year"
  (€34k x 58% = €19,720).
- **Slide 04:** 320,000 desks x €19,700 = **€6.30bn** (was €4.36bn); headline "€6bn a year
  of desk work"; the x €19,700 line carries an "assumed" chip, because applying an
  office-worker average to forwarding desks is an assumption.
- Not changed: `static/deck.html`, `static/what.html` and `docs/replit-deck-prompt.md`
  still say 60% under the 2022 label. Out of this deck's scope; flagged to the owner.

Agent copy (accepted by the owner):
- Inbox: Reads every mail, links it to the booking, and passes it to the right agent.
- Playbook: Checks every output against the customer's rules. Sends back what breaks them.
- Rate: Prices a lane across the carriers that serve it.
- RFQ: Turns a rate request into a drafted quote.
- Booking: Opens the booking from the mail and its documents. Holds what it cannot verify.
- Docs: Reads bills of lading, packing lists and invoices, and checks them against the booking.
- Milestones: Puts carrier updates on the booking and answers "where is my box?"
- Exception: Flags rolled boxes and mismatched documents. Escalates what the desk cannot absorb.
- Invoice: Checks the carrier invoice against the agreed rate and drafts the dispute.
- Customs: Prepares the entry for the arrival country. Escalates, never files.
- Assistant: Sends your question to the agent who owns it, or says nobody does.
- Risk: Reads 60 sources and flags what touches your bookings.
- Routing: Weighs slack against delay. Reroute, hold or no change.
- Comms: Drafts the carrier and customer mail. Sends nothing.
- Planner (scripted): Checks bookings before departure, while changes are still cheap.
- TMS Link (demo): Reads bookings in. Queues every change for your approval.

## Accepted copy changes for the remaining slides

- **08 The How 2/2 (done, kept for the record):** headline "Know early, while you still have options."; "42 live.
  Rest is phase two." becomes "60 live sources. AIS, freight indices and prediction
  markets come next."; drop the "triggered · 92%" number from the mock (reads as a real
  confidence score); the drafted mail's revised ETA must fit slide 02 (due 14 Oct, ETA
  10 Oct, +2 days reroute, so about 12 Oct); closing "The earlier the call, the more
  options you have and the less it costs." Answers slide 03's second problem.
- **10 Who am I:** point 2 named Zeit AI; use "Risk tools stop at the alert. Execution
  tools start after the decision. Nobody owns the step between. That is my bet."
  Point 3: "The groundwork is done: a forwarder ICP list, enriched in Apollo, and events
  lined up for outreach." (owner to confirm it is SQRlane's work). Experience lines:
  "Advised Fortune 500 CEOs on restructuring liabilities above $100M." and "Shaped the
  investment thesis of a $170M VC fund." Logos (UN Foundation, Manage and More, European
  Commission, IC, the tool stack) and the LinkedIn QR code: never redraw; ask for files
  or use name badges.

## Design system (all in `kit.py`)

- **Background** `#FAFAFA` on content slides (owner's choice), cards `#FFFFFF` with a
  12% ink border, 14px radius. The cover keeps its sage `#DBDBCD`.
- **One typeface: Geist** everywhere (the owner rejected monospace). Font named `Geist`
  alone, no fallback stack (Figma reads a stack as one missing font).
- **Ink** `#0A0A0A`, **muted** `#6B6B6B`, **amber** `#96580A` spent only on "where the
  pressure lands", green `#0F7B3F` only for ticks. Chart polarity pair validated with
  the dataviz skill: positive `#3D72A8`, negative amber.
- Header: eyebrow `NN · SECTION` with an amber square, 66px headline, 24px subline, and
  a **hairline rule at y 282** (owner asked for it; mirrors the footer rule at 978).
- Footer: mark + `sqrlane` + tagline "Automates the desk. Acts before the route breaks."
  + `SLIDE NN`.
- Section numbering so far: 01 Introduction, 02 The What, 03 The Why, 04 The Job 1/2,
  05 The Job 2/2, 06 The How 1/2.
- Figma-safe SVG: inline attributes, **no `<style>`**, named `<g id>` layers,
  `kit.write()` fails on an em dash. Escape `&` as `&amp;` in text (a bare `&` blanked
  slide 07 once). Superscripts via `<tspan dy>` shift the rest of the line; put them last.
- Build and check: `cd deck/v2 && python3 build_NN.py && cd .. && python3 render.py
  v2/slide-NN-*.svg`, then **look at the preview** (text overflow never raises). Headless
  Chrome needs Geist installed locally: convert `static/fonts/*.woff2` to TTF into
  `~/.fonts` with fontTools and run `fc-cache` (pip: fonttools brotli pillow pymupdf).
- Vendor logos: only official marks, inlined byte-for-byte (`channel_marks.json`, from
  Iconify's npm sets, CC0/MIT). No mark available means a grey name badge. Never redraw.

## House rules the owner holds to

- Minimal, simple, plain words a lay reader gets. No em dashes. No jargon without a gloss.
- **Never invent a figure.** Every number needs a source; derived ones show their
  arithmetic; assumptions carry an "assumed" chip. No traction or performance claim
  about SQRlane (why "40% of the day, back" became "Built for the 40%").
- Tags stay honest: 14 live, Planner scripted, TMS link demo. Nothing is sent or written.
- When the owner asks "is this the best you can do", critique the slide honestly, propose
  a stronger concept, and wait for a go before building.

## Facts checked this session (slide 06)

- Sea-Intelligence: 49.9% on time in Aug 2026 (lowest since Sep 2022); 2018 to 2019
  average 74%. The old deck's "47 of 100" had no source.
- Hapag-Lloyd Germany import tariff, 40ft: EUR 115 a day after 3 free days, EUR 180
  later (the old deck's EUR 185 was unsourced). So a box is a loss from day two.
- Red Sea detour absorbs 6 to 9% of global capacity (ING, Freightos). Rolled cargo goes
  to the next sailing, about a week later.
- Nemox funding: no reliable figure found (slide 04 leaves it off).
- Open with the owner: EUR 1,913 billed on slide 05 equals Drewry's $1,913 on slide 02
  in a different currency; which is right is unanswered.
