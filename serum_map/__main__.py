from __future__ import annotations

import argparse
import json

from .build import build_microfreak_macro_map
from .container import load


def main() -> None:
    parser = argparse.ArgumentParser(prog="serum_map")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("path")
    build_cmd = sub.add_parser("build-microfreak")
    build_cmd.add_argument("--controller", required=True)
    build_cmd.add_argument("--template", required=True)
    build_cmd.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "inspect":
        item = load(args.path)
        print(json.dumps({"header": item.header, "payload": item.payload}, indent=2))
    else:
        item = build_microfreak_macro_map(args.controller, args.template, args.output)
        print(json.dumps(item.payload["midiMap"], indent=2))


if __name__ == "__main__":
    main()
