"""connect.py - plugging a real TMS into SQRlane.

The demo connector (src/tms.py) reads a synthetic book. This module is what lets a
forwarder put their own book behind the same door, today, without an integration
project:

    read_export()   a bookings export - CSV or JSON, the thing every TMS can
                    produce from a saved search - mapped onto SQRlane's fields.
    read_api()      the same records, fetched live from an HTTPS endpoint that
                    returns them as JSON (a TMS API, or a small bridge in front
                    of one), with the caller's own token.
    push()          an approved write-back, POSTed to the endpoint the person
                    configured. Only ever called for one operation a person has
                    just approved - never in bulk behind their back.

Three rules hold it:

  * **Mapping, not guessing.** A column is used only if its header is one a TMS
    export actually uses for that field (the aliases below). Everything else is
    reported as unmapped, so a person can see what was and was not read.
  * **Covered or not covered, said out loud.** The agents can only judge a
    booking on a lane the route catalogue models - Asia to North-West Europe and
    its inland legs. Anything else is read, listed and left alone with the
    reason, never forced onto the nearest route.
  * **Nothing is stored server-side.** A connection is the records the person
    uploaded or the endpoint they named; the dashboard holds it and sends it with
    each request. No token is written anywhere by this module.

Numbers never go to a model here either: dates, slack and costs are parsed and
computed, and a value that does not parse is reported as unread rather than
filled in.
"""

import csv
import io
import ipaddress
import json
import re
import socket
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from src import config, httpget

# ---------------------------------------------------------------------------
# The field map - what a TMS export calls each field
# ---------------------------------------------------------------------------

# Header aliases, compared after lower-casing and squashing everything that is
# not a letter or digit to "_". Drawn from the column names forwarding systems
# actually export (job / shipment / house-bill numbers, POL / POD, RDD ...).
ALIASES = {
    "id": ["shipment_id", "shipment", "shipment_no", "shipment_number", "job", "job_no",
           "job_number", "file", "file_no", "file_number", "reference", "ref", "our_ref",
           "house_bill", "hbl", "hawb", "hbl_no", "consol", "id", "booking_id"],
    "booking_ref": ["booking_ref", "booking_reference", "booking_no", "booking_number",
                    "carrier_booking", "carrier_booking_ref", "carrier_booking_no",
                    "carrier_ref", "mbl", "master_bill", "master_bl", "mbl_no"],
    "cargo": ["commodity", "goods", "goods_description", "description", "cargo",
              "cargo_description", "product"],
    "origin": ["origin", "origin_port", "pol", "port_of_loading", "load_port",
               "loading_port", "from", "origin_city", "pol_name"],
    "port_of_discharge": ["pod", "port_of_discharge", "discharge_port", "destination_port",
                          "discharge", "pod_name"],
    "final_destination": ["final_destination", "destination", "place_of_delivery",
                          "delivery_place", "to", "destination_city", "consignee_city",
                          "fpod", "final_place"],
    "etd": ["etd", "departure", "sailing_date", "etd_pol", "departure_date"],
    "eta": ["eta", "arrival", "eta_pod", "estimated_arrival", "arrival_date"],
    "required_by": ["required_by", "rdd", "required_delivery_date", "delivery_date",
                    "due_date", "must_arrive_by", "deadline", "latest_delivery",
                    "required_date"],
    "carrier": ["carrier", "shipping_line", "line", "ocean_carrier", "scac",
                "carrier_name"],
    "customer": ["customer", "client", "consignee", "account", "customer_name",
                 "shipper", "bill_to"],
    "customer_contact": ["contact", "customer_contact", "consignee_contact"],
    "container": ["container", "container_no", "container_number", "containers",
                  "equipment", "cntr"],
    "cold_chain": ["reefer", "cold_chain", "temperature_controlled", "temp_controlled",
                   "temperature", "temperature_regime", "is_reefer"],
    "special_requirements": ["remarks", "notes", "special_instructions",
                             "special_requirements", "handling"],
    "freight_eur": ["freight_eur", "freight", "freight_cost", "freight_value", "cost_eur",
                    "freight_amount"],
    "late_eur_per_day": ["late_eur_per_day", "late_penalty_per_day", "penalty_per_day",
                         "delay_cost_per_day"],
}
_BY_ALIAS = {alias: field for field, aliases in ALIASES.items() for alias in aliases}

# What each SQRlane field is for, in the words the mapping table shows.
USED_FOR = {
    "id": "the booking's id on the board",
    "booking_ref": "the carrier's booking reference",
    "cargo": "what is being moved",
    "origin": "the load port - picks the lane",
    "port_of_discharge": "the discharge port - picks the lane",
    "final_destination": "where it is delivered - picks the inland leg",
    "etd": "departure date",
    "eta": "arrival date - the delay is measured from it",
    "required_by": "the customer's date - slack is measured to it",
    "carrier": "who the carrier mail goes to",
    "customer": "who the customer mail goes to",
    "customer_contact": "the customer mail's addressee",
    "container": "the equipment on the booking",
    "cold_chain": "reefer - a port change is a cold-chain transfer",
    "special_requirements": "handling notes the drafts respect",
    "freight_eur": "freight value - prices a reroute's premium",
    "late_eur_per_day": "what a day late costs",
}


def _key(header) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(header).strip().lower()).strip("_")


# ---------------------------------------------------------------------------
# Lanes - which bookings the route catalogue can judge
# ---------------------------------------------------------------------------

# The catalogue (data/routes.json) models Asia to North-West Europe via Suez or
# the Cape, and three inland legs. A booking is covered when its load port is in
# Asia and its discharge port or final destination is one of these. The route and
# alternates are the ones the authored pool uses for the same lane, so an
# imported booking is judged exactly the way the demo's are.
PORTS = {
    "HAM": ["hamburg", "deham"],
    "RTM": ["rotterdam", "nlrtm"],
    "ANR": ["antwerp", "antwerpen", "anvers", "beanr", "antwerp_bruges"],
    "FOS": ["fos", "fos_sur_mer", "marseille", "frfos", "frmrs", "marseille_fos"],
}
INLAND = {
    "basel": ("R-RTM-RHINE", ["R-RTM-RAIL", "R-COGH-BSL"]),
    "chbsl": ("R-RTM-RHINE", ["R-RTM-RAIL", "R-COGH-BSL"]),
    "lyon": ("R-FOS-STD", ["R-ANR-LYON", "R-COGH-FOS"]),
    "frlys": ("R-FOS-STD", ["R-ANR-LYON", "R-COGH-FOS"]),
}
LANES = {
    "HAM": ("R-HAM-STD", ["R-RTM-ALT", "R-COGH-ALT"]),
    "RTM": ("R-RTM-STD", ["R-COGH-RTM"]),
    "ANR": ("R-ANR-STD", ["R-COGH-ANR"]),
    "FOS": ("R-FOS-STD", ["R-COGH-FOS"]),
}
# Load ports the Asia-Europe catalogue starts from: UN/LOCODE country prefixes,
# and the port names an export writes out in full.
ASIA_COUNTRIES = {"cn", "hk", "tw", "kr", "jp", "vn", "th", "my", "sg", "id", "ph", "in",
                  "lk", "bd", "pk", "kh", "mm"}
ASIA_PORTS = {"shanghai", "ningbo", "shenzhen", "yantian", "shekou", "qingdao", "tianjin",
              "xingang", "dalian", "xiamen", "guangzhou", "nansha", "hong_kong", "hongkong",
              "kaohsiung", "keelung", "busan", "pusan", "incheon", "tokyo", "yokohama",
              "kobe", "osaka", "nagoya", "singapore", "port_klang", "tanjung_pelepas",
              "laem_chabang", "bangkok", "ho_chi_minh", "ho_chi_minh_city", "cat_lai",
              "haiphong", "hai_phong", "da_nang", "jakarta", "surabaya", "manila",
              "nhava_sheva", "jawaharlal_nehru", "mundra", "chennai", "colombo",
              "chittagong", "karachi", "fuzhou", "lianyungang", "taicang"}


def _lane(origin, pod, destination):
    """(primary, alternates, None) for a covered booking, or (None, None, why)."""
    o = _key(origin)
    if not o:
        return None, None, "no load port on the record"
    asia = (o in ASIA_PORTS or any(o.startswith(p) for p in ASIA_PORTS)
            or (len(o) == 5 and o[:2] in ASIA_COUNTRIES))
    if not asia:
        return None, None, (f"load port '{origin}' is outside the catalogue - it models "
                            f"Asia to North-West Europe")
    dest = _key(destination)
    for name, lane in INLAND.items():
        if dest == name or dest.startswith(name):
            return lane[0], list(lane[1]), None
    for candidate in (pod, destination):
        c = _key(candidate)
        for port, names in PORTS.items():
            if c in names or any(c.startswith(n) for n in names):
                return LANES[port][0], list(LANES[port][1]), None
    where = pod or destination or "none given"
    return None, None, (f"discharge '{where}' is not a port the catalogue models "
                        f"(Hamburg, Rotterdam, Antwerp, Fos) or an inland leg it covers")


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%d %b %Y",
                "%d %B %Y", "%b %d %Y", "%Y%m%d")


def parse_date(raw) -> str | None:
    """An ISO date, or None. Never a guess: an unreadable date stays unread."""
    if raw in (None, ""):
        return None
    text = str(raw).strip()
    text = text.split("T", 1)[0] if re.match(r"\d{4}-\d{2}-\d{2}T", text) else text
    text = text.replace(",", "")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _truthy(raw) -> bool:
    text = str(raw or "").strip().lower()
    if text in ("", "0", "no", "n", "false", "dry", "ambient", "none", "-"):
        return False
    # "+2 to +8 C", "yes", "reefer", "frozen" - any stated regime is a cold chain.
    return True


def _money(raw) -> int | None:
    digits = re.sub(r"[^\d.,-]", "", str(raw or ""))
    if not digits:
        return None
    # 28,800 / 28.800 / 28800.00 - thousands separators in either convention.
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", digits):
        digits = re.sub(r"[.,]", "", digits)
    try:
        return int(round(float(digits.replace(",", "."))))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def _rows_from_text(text: str, filename: str = "") -> list[dict]:
    """CSV (comma, semicolon or tab) or JSON, decided by the content."""
    stripped = text.lstrip("﻿").strip()
    if not stripped:
        raise ValueError("the file is empty")
    if stripped[0] in "[{":
        return _rows_from_json(json.loads(stripped))
    sample = stripped[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(stripped), dialect=dialect)
    return [dict(row) for row in reader]


def _rows_from_json(data, records_path: str = "") -> list[dict]:
    if records_path:
        for part in records_path.split("."):
            data = data.get(part) if isinstance(data, dict) else None
    if isinstance(data, dict):
        for key in ("bookings", "shipments", "data", "items", "results", "records", "rows"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("no list of bookings found - point 'records path' at the list")
    return [row for row in data if isinstance(row, dict)]


def _flatten(row: dict, prefix="") -> dict:
    """Nested JSON (pol: {name: ...}) read as pol_name, the way a mapping names it."""
    out = {}
    for key, value in row.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, f"{name}_"))
        elif isinstance(value, list):
            out[name] = ", ".join(str(v) for v in value if not isinstance(v, (dict, list)))
        else:
            out[name] = value
    return out


def normalise(rows: list[dict], *, name: str, kind: str, source: str) -> dict:
    """Map a TMS's rows onto SQRlane's booking fields. The connection, described."""
    rows = [_flatten(r) for r in rows]
    headers = []
    for row in rows:
        for header in row:
            if header not in headers:
                headers.append(header)
    mapping, unmapped, column_for = [], [], {}
    for header in headers:
        field = _BY_ALIAS.get(_key(header))
        if field and field not in column_for:
            column_for[field] = header
            mapping.append({"column": header, "field": field, "used_for": USED_FOR[field]})
        else:
            unmapped.append(header)

    def value(row, field):
        column = column_for.get(field)
        raw = row.get(column) if column else None
        return raw.strip() if isinstance(raw, str) else raw

    bookings, not_covered, warnings = [], [], []
    seen = set()
    limit = config.TMS_MAX_BOOKINGS
    for index, row in enumerate(rows, start=1):
        ref = value(row, "id") or value(row, "booking_ref")
        if not ref:
            not_covered.append({"row": index, "ref": None,
                                "reason": "no shipment or booking reference on the row"})
            continue
        ref = str(ref)
        primary, alternates, why = _lane(value(row, "origin"), value(row, "port_of_discharge"),
                                         value(row, "final_destination"))
        eta = parse_date(value(row, "eta"))
        if primary and not eta:
            primary, why = None, "no readable ETA - the delay is measured from it"
        if not primary:
            not_covered.append({"row": index, "ref": ref, "reason": why})
            continue
        if len(bookings) >= limit:
            not_covered.append({"row": index, "ref": ref,
                                "reason": f"over the {limit}-booking limit for one run"})
            continue
        bid = ref if ref not in seen else f"{ref}-{index}"
        seen.add(bid)
        required_by = parse_date(value(row, "required_by"))
        notes = []
        if required_by:
            slack = (date.fromisoformat(required_by) - date.fromisoformat(eta)).days
        else:
            slack = 0
            notes.append("no required-by date on the record - slack taken as 0 days")
        freight = _money(value(row, "freight_eur"))
        late = _money(value(row, "late_eur_per_day"))
        if freight is None:
            notes.append("no freight value - a reroute's premium is not priced")
        booking = {
            "id": bid,
            "cargo": value(row, "cargo") or "Cargo (not stated on the record)",
            "cargo_detail": None,
            "origin": value(row, "origin"),
            "final_destination": (value(row, "final_destination")
                                  or value(row, "port_of_discharge")),
            "primary_route": primary,
            "alternates": alternates,
            "deadline_slack_days": slack,
            "notes": "; ".join(notes) or "Read from your TMS.",
            "customer": value(row, "customer") or "the customer",
            "customer_contact": value(row, "customer_contact"),
            "carrier": value(row, "carrier") or "the carrier",
            "booking_ref": str(value(row, "booking_ref") or ref),
            "container": value(row, "container"),
            "etd": parse_date(value(row, "etd")),
            "eta": eta,
            "required_by": required_by,
            "cold_chain": _truthy(value(row, "cold_chain")),
            "special_requirements": value(row, "special_requirements") or None,
            "commercial": {"freight_eur": freight or 0, "late_eur_per_day": late or 0,
                           "breach_eur": 0, "transfer_risk_eur": 0,
                           "basis": "Read from your TMS export."},
            "tms_row": index,
        }
        if notes:
            booking["read_notes"] = notes
        bookings.append(booking)

    for field in ("id", "origin", "eta"):
        if field not in column_for and not (field == "id" and "booking_ref" in column_for):
            warnings.append(f"No column for {USED_FOR[field]} ({field}). Rename the column "
                            f"to one of: {', '.join(ALIASES[field][:5])}.")
    if "port_of_discharge" not in column_for and "final_destination" not in column_for:
        warnings.append("No discharge port or destination column - no lane can be matched.")
    if "required_by" not in column_for:
        warnings.append("No required-by date column - every booking's slack is taken as 0 "
                        "days, so any delay reads as late.")

    return {
        "kind": kind,
        "name": name,
        "source": source,
        "read_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "rows_read": len(rows),
        "bookings": bookings,
        "not_covered": not_covered,
        "mapping": mapping,
        "unmapped_columns": unmapped,
        "warnings": warnings,
    }


def read_export(content: str, filename: str = "export") -> dict:
    """A bookings export, as uploaded. CSV or JSON."""
    if len(content.encode("utf-8")) > config.HTTP_MAX_BYTES:
        raise ValueError("the file is larger than this prototype reads in one go")
    rows = _rows_from_text(content, filename)
    return normalise(rows, name=f"Your TMS (export: {filename})", kind="file",
                     source=filename)


# ---------------------------------------------------------------------------
# The live link - an HTTPS endpoint, and the write-back
# ---------------------------------------------------------------------------


def host(url: str) -> str:
    """The hostname alone, for saying where something goes. No lookup."""
    return urlparse(url or "").hostname or "(no host)"


def check_url(url: str) -> str:
    """Refuse anything but a public HTTPS host.

    The fetch runs on this server, so an address it would be wrong to reach from
    here - loopback, a private network, a cloud metadata address - is refused
    before any request is made. Redirects are not followed either, so a public
    host cannot bounce the request somewhere private.
    """
    parsed = urlparse(url or "")
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("the endpoint must be an https:// address")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve {parsed.hostname}") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if (address.is_private or address.is_loopback or address.is_link_local
                or address.is_reserved or address.is_multicast or address.is_unspecified):
            raise ValueError(f"{parsed.hostname} resolves to a private address - refused")
    return parsed.hostname


def _auth_headers(token: str | None, header: str | None) -> dict:
    if not token:
        return {}
    header = (header or "Authorization").strip()
    if header.lower() == "authorization" and " " not in token.strip():
        token = f"Bearer {token.strip()}"
    return {header: token.strip(), "Accept": "application/json"}


def read_api(url: str, *, token: str | None = None, auth_header: str | None = None,
             records_path: str = "") -> dict:
    """The book, fetched live from the TMS's endpoint on every call."""
    host = check_url(url)
    response = httpget.get_capped(url, timeout=config.TMS_TIMEOUT_SECONDS,
                                  headers=_auth_headers(token, auth_header),
                                  allow_redirects=False)
    if 300 <= response.status_code < 400:
        raise ValueError(f"{host} answered with a redirect - point at the final address")
    rows = _rows_from_json(response.json(), records_path)
    return normalise(rows, name=f"Your TMS (API: {host})", kind="api", source=host)


def resolve(spec: dict | None) -> dict | None:
    """What the dashboard sent, turned into a connection with bookings in it.

    A file connection arrives already read (the dashboard keeps what /connect
    returned). An API connection is read again, live, every time - that is what
    makes it a link rather than a snapshot.
    """
    if not spec or spec.get("kind") in (None, "", "demo"):
        return None
    if spec.get("kind") == "api":
        live = read_api(spec.get("url", ""), token=spec.get("token"),
                        auth_header=spec.get("auth_header"),
                        records_path=spec.get("records_path") or "")
        live["writeback_url"] = spec.get("writeback_url") or None
        return live
    if spec.get("kind") == "file":
        bookings = spec.get("bookings")
        if not isinstance(bookings, list) or not bookings:
            raise ValueError("the connection carries no bookings - upload the export again")
        return {"kind": "file", "name": spec.get("name") or "Your TMS (export)",
                "source": spec.get("source") or "export",
                "read_at": spec.get("read_at"), "bookings": bookings[:config.TMS_MAX_BOOKINGS],
                "writeback_url": spec.get("writeback_url") or None}
    raise ValueError(f"unknown connection kind '{spec.get('kind')}'")


def push(operation: dict, *, url: str, token: str | None = None,
         auth_header: str | None = None) -> dict:
    """One approved write-back, sent to the TMS endpoint the person configured.

    The body is the operation exactly as the approval queue showed it - the
    booking, the Worker, every field's from and to - plus who approved it. What
    the TMS does with it is the TMS's business; what comes back is reported as is.
    """
    host = check_url(url)
    body = {"source": "SQRlane", "approved_at": datetime.now(timezone.utc)
            .replace(microsecond=0).isoformat(), "operation": operation}
    response = httpget.post_capped(url, timeout=config.TMS_TIMEOUT_SECONDS, json=body,
                                   headers=_auth_headers(token, auth_header))
    return {"ok": 200 <= response.status_code < 300, "status": response.status_code,
            "host": host, "response": response.text[:500]}
