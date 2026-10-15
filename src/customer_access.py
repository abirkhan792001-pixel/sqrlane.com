"""customer_access.py - who may send a quote request: the forwarder's own customers.

One job: turn a key into the customer it belongs to, or into nobody.

Each customer gets a personal key, and with it a personal connector link,
https://www.sqrlane.com/mcp/c/<key>, which they add to Claude (or send as
`Authorization: Bearer <key>` from their own agent). A request that arrives with
a key the forwarder issued is that customer's; anything else is nobody's, and
request_quote refuses it.

No database and no accounts. The keys live in one environment variable,
CUSTOMER_KEYS, as JSON mapping the SHA-256 of each key to the customer's name:

    {"3f1c...e9": "Bavaria Drivetrain GmbH", "a07b...12": "Wonen Direct B.V."}

Only the hash is stored, so the variable leaking does not leak a working key. The
key itself is shown once, when it is made, and handed to the customer. Removing a
line revokes that customer (after a redeploy, like any Vercel variable). With the
variable unset, nobody is let in - the tool fails closed, never open.

Make a key:   python -m src.customer_access new "Bavaria Drivetrain GmbH"
See who has one:  python -m src.customer_access list
"""

import hashlib
import hmac
import json
import os
import secrets
import sys

ENV = "CUSTOMER_KEYS"
PREFIX = "sqr_"
CONNECTOR_BASE = "https://www.sqrlane.com/mcp/c/"


def hash_key(key: str) -> str:
    return hashlib.sha256((key or "").encode("utf-8")).hexdigest()


def load(raw: str | None = None) -> dict[str, str]:
    """{key hash: customer name}. Unset, unreadable or malformed means nobody."""
    raw = os.getenv(ENV, "") if raw is None else raw
    try:
        table = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return {}
    if not isinstance(table, dict):
        return {}
    return {str(h).lower(): str(name).strip() for h, name in table.items()
            if isinstance(name, str) and name.strip() and len(str(h)) == 64}


def customer_for(key: str | None, table: dict[str, str] | None = None) -> str | None:
    """The customer a key was issued to, or None."""
    if not key or not key.startswith(PREFIX):
        return None
    table = load() if table is None else table
    digest = hash_key(key)
    found = None
    for stored, name in table.items():
        # Compare every entry, so the time taken does not say how close a guess was.
        if hmac.compare_digest(stored, digest):
            found = name
    return found


def new_key(customer: str) -> tuple[str, str]:
    """(the key to hand the customer, its hash for CUSTOMER_KEYS)."""
    key = PREFIX + secrets.token_urlsafe(32)
    return key, hash_key(key)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    table = load()
    if argv[:1] == ["list"]:
        names = sorted(table.values())
        print("\n".join(names) if names else f"No customer has a key ({ENV} is empty).")
        return
    if argv[:1] != ["new"] or len(argv) < 2:
        print(__doc__)
        return
    customer = " ".join(argv[1:]).strip()
    key, digest = new_key(customer)
    table[digest] = customer
    print(f"Customer:        {customer}")
    print(f"Connector link:  {CONNECTOR_BASE}{key}")
    print(f"Or as a header:  Authorization: Bearer {key}")
    print()
    print("Give the link to the customer - it is shown only now, and only its hash is kept.")
    print(f"Set {ENV} in Vercel to the line below (it keeps every existing key), then redeploy:")
    print()
    print(json.dumps(table, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
