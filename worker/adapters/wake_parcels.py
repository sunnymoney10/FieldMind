#!/usr/bin/env python3
"""Wake County owner-of-record lookup (official property source) for the FieldMind worker.

STATUS: written, NOT RUN (the hosted workspace could not reach maps.wake.gov). Run locally:
    python3 adapters/wake_parcels.py runs/<ref>
Data: Wake County "Parcels" layer, open data, CC BY 4.0 (attribute "Wake County" when shown).
Service: https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0

The worker treats source_type "property_record" as official, so an owner name found here can be
"verified" as the PROPERTY owner of record for the parcel at this address. It still says nothing about
who controls tenant HVAC or the utility account. Field names are discovered from the layer's metadata
instead of being hard-coded; if no address or owner field is found the record is logged as failed.
"""
import json, os, sys, datetime as dt
from urllib.parse import urlencode
from urllib.request import urlopen, Request

LAYER = "https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def get(url):
    with urlopen(Request(url, headers={"User-Agent": "fieldmind-worker/0.1"}), timeout=30) as r:
        return json.load(r)


def main(run_dir):
    p = json.load(open(os.path.join(run_dir, "prospect.json")))
    a = p["address"]
    t0 = now()
    rec = {"id": "P1", "kind": "fetch", "title": "Wake County parcels (owner of record)", "source_type": "property_record", "started_at": t0}
    try:
        meta = get(LAYER + "?f=json")
        fields = [f["name"] for f in meta.get("fields", [])]
        addr_f = next((f for f in fields if "SITE" in f.upper() and "ADDR" in f.upper()), None) or next((f for f in fields if "ADDR" in f.upper()), None)
        owner_f = [f for f in fields if "OWNER" in f.upper()][:2]
        if not addr_f or not owner_f:
            raise RuntimeError(f"address/owner fields not found in layer: {fields[:40]}")
        street = f"{a['number']} {a['street']}".upper().replace("'", "")
        q = {"where": f"UPPER({addr_f}) LIKE '{street}%'", "outFields": ",".join([addr_f] + owner_f), "returnGeometry": "false", "f": "json"}
        url = LAYER + "/query?" + urlencode(q)
        data = get(url)
        feats = [f["attributes"] for f in data.get("features", [])]
        text = "\n".join("; ".join(f"{k}: {v}" for k, v in at.items()) for at in feats)
        rec.update(url=url, outcome="ok" if feats else "no_results", error=None if feats else "no parcel matched the street address",
                   captured_text=text, completed_at=now(), license="CC BY 4.0, Wake County")
    except Exception as e:
        rec.update(url=LAYER, outcome="failed", error=repr(e)[:300], captured_text="", completed_at=now())
    with open(os.path.join(run_dir, "retrieval.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(rec["outcome"], rec.get("error") or "")


if __name__ == "__main__":
    main(sys.argv[1])
