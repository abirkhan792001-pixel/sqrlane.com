"""learning.py - what the desk has been taught. Corrections in, lessons out.

Every time a person corrects a Worker - "that is a rate request, not a
booking", "that line is the gross weight" - the correction is kept as a
**lesson**. On every later run the Workers read their lessons before they work:

    Inbox Worker   a lesson is a cue phrase and the intent it means. It is put in
                   front of the model as a correction to follow, and it is also
                   applied after the model answers, so a correction a person made
                   can never be quietly un-made by the model disagreeing.
    Docs Worker    a lesson is a document label and the field it fills. The
                   extractor reads it exactly like one of its own labels.

So "learning" here means one precise thing: **a correction becomes a rule and a
piece of context that every later run applies.** No model is retrained and no
weights change. That is deliberate. A lesson you can read, date, attribute to the
item it came from and delete is a lesson an operations lead can trust; a
fine-tune that shifted somewhere nobody can point at is not.

The loop that makes this safe lives in workflow.correct(): a new lesson is only
kept if it actually fixes the item it came from AND every earlier lesson still
holds afterwards. A lesson that would undo an earlier correction is refused.

Lessons are one JSON file (config.LESSONS_FILE) - no database, as everywhere
else. On a serverless host that file sits in the temp directory and lasts as
long as the instance does; the dashboard says so rather than implying memory it
does not have.
"""

import json
import re
from datetime import datetime, timezone

from src import config

# Which Worker each kind of lesson teaches. A lesson is always addressed to the
# Worker that made the mistake, because that is the Worker that has to read it.
KINDS = {"intent": "Inbox Worker", "field": "Docs Worker"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalise(text: str) -> str:
    """Lower-case and single-spaced, so a cue matches however it was typed."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def cue_pattern(cue: str) -> re.Pattern:
    """Match a cue as a whole phrase. Hyphens count as part of a word, so a lesson
    about "re-quote" is not triggered by "quote", and the other way round."""
    return re.compile(r"(?<![\w-])" + re.escape(normalise(cue)) + r"(?![\w-])")


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


def load() -> list[dict]:
    try:
        with open(config.LESSONS_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def save(lessons: list[dict]) -> None:
    config.LESSONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.LESSONS_FILE, "w", encoding="utf-8") as handle:
        json.dump(lessons, handle, indent=2, ensure_ascii=False)


def reset() -> int:
    """Forget everything. Returns how many lessons were dropped."""
    count = len(load())
    save([])
    return count


def active(lessons: list[dict] | None = None, kind: str | None = None) -> list[dict]:
    lessons = load() if lessons is None else lessons
    return [l for l in lessons if l.get("status") == "active"
            and (kind is None or l.get("kind") == kind)]


# ---------------------------------------------------------------------------
# Making a lesson out of a correction
# ---------------------------------------------------------------------------


def _next_id(lessons: list[dict]) -> str:
    numbers = [int(l["id"].split("-")[1]) for l in lessons
               if re.fullmatch(r"L-\d+", l.get("id", ""))]
    return f"L-{(max(numbers) + 1) if numbers else 1:03d}"


def intent_lesson(lessons, *, item_id, wrong, right, cue, right_label) -> dict:
    return {
        "id": _next_id(lessons), "kind": "intent", "worker": KINDS["intent"],
        "from_item": item_id, "wrong": wrong, "right": right,
        "cue": normalise(cue),
        "learned": (f"A message that says “{normalise(cue)}” is a "
                    f"{right_label.lower()}, whatever else it mentions."),
        "created_at": _now(), "status": "active", "superseded_by": None,
    }


def field_lesson(lessons, *, item_id, field, field_label, label, wrong, right) -> dict:
    return {
        "id": _next_id(lessons), "kind": "field", "worker": KINDS["field"],
        "from_item": item_id, "field": field, "wrong": wrong, "right": right,
        "label": normalise(label),
        "learned": (f"A document line labelled “{label.strip()}” is the "
                    f"{field_label.lower()}."),
        "created_at": _now(), "status": "active", "superseded_by": None,
    }


def conflicts(lessons: list[dict], new: dict) -> list[dict]:
    """Active lessons the new one replaces: the same cue, or the same label,
    taught to mean something else. The newer correction is the one a person made
    most recently, so it wins - but the old one is kept, marked superseded, so
    the history of what the desk was taught is never rewritten."""
    out = []
    for old in active(lessons, new["kind"]):
        if new["kind"] == "intent" and old["cue"] == new["cue"]:
            out.append(old)
        if new["kind"] == "field" and old["label"] == new["label"]:
            out.append(old)
    return out


def with_lesson(lessons: list[dict], new: dict) -> list[dict]:
    """The lesson list as it would be with `new` added. Nothing is saved."""
    replaced = {l["id"] for l in conflicts(lessons, new)}
    out = [dict(l, status="superseded", superseded_by=new["id"]) if l["id"] in replaced else l
           for l in lessons]
    return out + [new]


# ---------------------------------------------------------------------------
# What the Workers read
# ---------------------------------------------------------------------------


def intent_overrides(lessons: list[dict]) -> list[dict]:
    """Newest first, so if two cues both match, the later correction decides."""
    return sorted(active(lessons, "intent"), key=lambda l: l["created_at"] + l["id"],
                  reverse=True)


def field_aliases(lessons: list[dict]) -> dict[str, tuple[str, str]]:
    """label -> (field, lesson id)."""
    return {l["label"]: (l["field"], l["id"]) for l in active(lessons, "field")}


def context_for(worker_name: str, lessons: list[dict]) -> list[str]:
    """The lessons one Worker reads before it works, in plain words. This is the
    'context' a correction updates - shown on screen, and put in front of the
    model for the one Worker that uses one."""
    return [l["learned"] for l in active(lessons) if l["worker"] == worker_name]
