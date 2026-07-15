from __future__ import annotations

import csv
from pathlib import Path

from .container import SerumMap, dump, load

PRIMARY_PARAMETERS = ["Cutoff", "Resonance", "Timbre", "Shape", "Wave", "Filter amount", "Envelope attack", "Envelope decay"]


def read_microfreak_ccs(path: str | Path) -> dict[str, int]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        result: dict[str, int] = {}
        for row in csv.DictReader(handle):
            name = (row.get("parameter_name") or "").strip()
            cc = (row.get("cc_msb") or "").strip()
            if name and cc:
                result[name.casefold()] = int(cc)
    return result


def build_microfreak_macro_map(controller_csv: str | Path, template_path: str | Path, output_path: str | Path) -> SerumMap:
    template = load(template_path)
    entries = template.payload.get("midiMap")
    if not isinstance(entries, list) or len(entries) < 8:
        raise ValueError("Template must contain at least eight MIDI map entries")
    ccs = read_microfreak_ccs(controller_csv)
    selected = [ccs[name.casefold()] for name in PRIMARY_PARAMETERS]
    payload = dict(template.payload)
    payload["midiMap"] = [
        {"ccNum": cc, "paramIDs": list(source["paramIDs"])}
        for cc, source in zip(selected, entries[:8])
    ]
    result = SerumMap(header=dict(template.header), payload=payload)
    dump(result, output_path)
    return result
