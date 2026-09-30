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
| 08 | The How 2 of 2: the risk layer (know early, while options exist) | to do |
| 09 | Who am I (founder) | to do |
| A | Appendix: sources for slide 06 (`SOURCES` list in `build_06.py`) | later, not now |

Slide 06 version B (callout map + takeaway strip) was deleted from the repo; it lives
in git at `d4af2cc:deck/v2/slide-06-the-job-2-b.svg` if the owner asks again.

## Slide 07, rebuilt twice (2026-09-30)

The first rebuild (dashboard with inbox rows and approvals, plus IN/OUT integration rows
with Today/Next brackets) was sent back as too much content. On the owner's instruction:
a very clean dashboard overview with infographics, no integrations, and the focus on how
the 16 agents work together and how the work is structured. Current version:

- **Left, the Overview:** sidebar, four stat cards (13 mails worked, 8 of 13 handled end
  to end, 5 held for a person, 24 awaiting approval = 10 drafts and 14 TMS changes) and
  two infographics: "How the 13 mails ended" (one square per mail, ids 101-113, blue
  handled / amber held) and "What came in" (13 mails by the job they start: Quote 1,
  Book 4, Documents 2, In transit 3, Arrival 2, Billing 1). All counted from
  `src/workflow.run(use_llm=False)`; the window bar says "Demo run · synthetic inbox".
  Chart pair validated with the dataviz script (#3D72A8, #96580A).
- **Right, how the work is structured:** Risk layer band (4 agents, slide 08) → Inbox
  and Assistant → the desk as six stages in shipment order (Quote: Rate, RFQ · Book:
  Booking · Documents: Docs · In transit: Milestones, Exception · Arrival: Customs ·
  Billing: Invoice) → Playbook → You approve → TMS link (demo) → "one mail, together":
  IN-108's real path. Tags in the panel header: 14 live, Planner scripted, TMS link demo.
- The closing line is now "Every step recorded, checked against the customer's rules,
  and approved by you." **"Built for the 40%" was removed** (see below).

## The 40% does not hold (checked 2026-09-30)

Slide 03 says "40% of the day on admin, upper estimate, logistics industry surveys" and
slides 02, 03 (EUR 13,600 = 34k x 40%) and 04 build on it. No named source says that.
The nearest Grade A figure, Asana's Anatomy of Work 2022, says the opposite shape: 58% of
a knowledge worker's day goes to coordination, 33% to skilled work, under 10% to strategy
(10,624 knowledge workers, not forwarders). nShift, a vendor, reports about a third of
logistics workers spend over half their time on manual tasks (Grade B at best). The rest
is vendor blogs (Grade C). The owner has not yet decided how to fix slides 02-04.

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

- **09 The How 2/2:** headline "Know early, while you still have options."; "42 live.
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
