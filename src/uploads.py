"""uploads.py - what a file dropped into the Ask box is, and who it goes to.

One job: look at an uploaded file and say which of three things it is, so the
right Worker gets it.

    export      a bookings export (CSV / TSV / JSON with booking columns) - the
                TMS Link reads it, exactly as the TMS link page's upload does
    mail        an email (.eml) or a text document - the desk works it the way
                it works every inbound mail: Inbox Worker, then the owner
    unreadable  a PDF, an image, an Office file. The Docs Worker reads text; a
                scanned page needs a vision model, which this build does not
                have. Said, never guessed at.

The file arrives as text the browser read; a binary file arrives with no
content at all, which is how "unreadable" is known without sniffing bytes.
"""

import base64
import quopri
import re

from src import connect

TEXT_EXTENSIONS = (".txt", ".eml", ".md", ".csv", ".tsv", ".json", ".xml", ".edi", ".log")
SPREADSHEETS = (".xlsx", ".xls", ".ods", ".numbers")
MAX_CHARS = 200_000


def _ext(name: str) -> str:
    match = re.search(r"\.[A-Za-z0-9]+$", name or "")
    return match.group(0).lower() if match else ""


def _looks_like_export(name: str, text: str) -> bool:
    if _ext(name) in (".csv", ".tsv", ".json"):
        try:
            conn = connect.read_export(text, name)
        except (ValueError, UnicodeError):
            return False
        return bool(conn["mapping"]) and any(m["field"] in ("eta", "origin", "port_of_discharge")
                                             for m in conn["mapping"])
    return False


def _headers_and_body(raw: str) -> tuple[dict, str]:
    """RFC 822 headers (folded lines joined, names lower-cased) and the rest."""
    head, _, body = raw.replace("\r\n", "\n").partition("\n\n")
    headers, last = {}, None
    for line in head.split("\n"):
        if line[:1] in (" ", "\t") and last:
            headers[last] += " " + line.strip()
        elif ":" in line:
            last, value = line.split(":", 1)
            last = last.strip().lower()
            headers[last] = value.strip()
    return headers, body


def _decoded(headers: dict, body: str) -> str:
    encoding = headers.get("content-transfer-encoding", "").lower()
    charset = (re.search(r'charset="?([\w-]+)', headers.get("content-type", "")) or [None, "utf-8"])[1]
    try:
        if encoding == "base64":
            return base64.b64decode(body).decode(charset, "replace")
        if encoding == "quoted-printable":
            return quopri.decodestring(body.encode()).decode(charset, "replace")
    except (ValueError, LookupError):
        return body
    return body


def _from_eml(name: str, text: str) -> dict:
    """A mail file read by hand - headers, the plain-text body, text attachments.

    Deliberately not the standard library's email package: that package builds
    messages too, and src/ imports nothing that could put a mail in front of
    anyone (tests/test_comms_agent_sends_nothing.py). Reading one is plain text.
    """
    headers, body = _headers_and_body(text)
    plain, attachments = "", []
    boundary = re.search(r'boundary="?([^";]+)"?', headers.get("content-type", ""))
    if boundary:
        for part in body.split("--" + boundary.group(1))[1:]:
            part_headers, part_body = _headers_and_body(part.lstrip("\n"))
            kind = part_headers.get("content-type", "text/plain").lower()
            filename = re.search(r'filename="?([^";]+)"?',
                                 part_headers.get("content-disposition", "") + " "
                                 + part_headers.get("content-type", ""))
            if not kind.startswith("text/"):
                continue
            content = _decoded(part_headers, part_body).strip()
            if filename:
                attachments.append({"name": filename.group(1), "text": content[:20_000]})
            elif kind.startswith("text/plain") and not plain:
                plain = content
    else:
        plain = _decoded(headers, body).strip()
    sender = headers.get("from") or "Uploaded mail"
    org = re.sub(r"\s*<.*?>\s*", "", sender).strip().strip('"') or "Unknown sender"
    return {"from": sender, "sender_org": org, "subject": headers.get("subject") or name,
            "body": plain[:20_000], "attachments": attachments}


def read(name: str, content: str | None, index: int = 1) -> dict:
    """Classify one upload. Returns {kind, name, ...} with what that kind needs."""
    name = (name or "upload").strip()[:120]
    if _ext(name) in SPREADSHEETS:
        return {"kind": "unreadable", "name": name,
                "reason": ("A spreadsheet file is not read directly. Save it as CSV (File > "
                           "Save as > CSV) and drop that in - the TMS Link reads a CSV export.")}
    if content is None or _ext(name) not in TEXT_EXTENSIONS + ("",) or "\x00" in content:
        return {"kind": "unreadable", "name": name,
                "reason": ("The Docs Worker reads text documents. A PDF, an image or an Office "
                           "file needs a vision model to read, and this build does not have one "
                           "- nothing is guessed from it. Paste the text, or upload the mail "
                           "as .eml.")}
    text = content[:MAX_CHARS]
    if _looks_like_export(name, text):
        return {"kind": "export", "name": name, "connection": connect.read_export(text, name)}
    if _ext(name) == ".eml" or re.match(r"(?im)^(from|subject):", text[:500]):
        mail = _from_eml(name, text)
    else:
        # A plain document: worked as a mail from you with the document attached,
        # so the Docs Worker reads it the way it reads any attachment.
        mail = {"from": "You (uploaded in Ask)", "sender_org": "Uploaded by you",
                "subject": f"Document: {name}", "body": text[:4000],
                "attachments": [{"name": name, "text": text[:20_000]}]}
    return {"kind": "mail", "name": name, "message": dict(mail, id=f"UP-{index:03d}")}
