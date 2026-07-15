# Serum MIDI Map Generator

Reverse-engineering and generation tools for Xfer Serum 2 `.SerumMIDIMap` files.

This repository starts from three user-supplied reference files:

- a Serum 2 Novation MIDI map
- Serum 2's default MIDI map
- a Novation `.mmp` map

The goal is to generate a valid Serum 2 MIDI map from a controller CSV, beginning with the Arturia MicroFreak.

## Current confirmed format

A `.SerumMIDIMap` file contains:

1. `XferJson\0` magic bytes
2. an unsigned 64-bit little-endian JSON-header length
3. a JSON metadata header
4. an unsigned 32-bit little-endian uncompressed payload length
5. an unsigned 32-bit little-endian compression type (`2` in the samples)
6. a Zstandard-compressed MessagePack payload

The decoded payload contains a `midiMap` array. Each entry contains a MIDI CC number and one or more internal Serum parameter IDs.

## Status

- [x] Container parser
- [x] Zstandard payload extraction
- [x] MessagePack decoding
- [x] Round-trip writer scaffold
- [x] MicroFreak controller CSV
- [ ] Identify stable Serum parameter names for each internal parameter ID
- [ ] Confirm header hash algorithm
- [ ] Validate a generated map inside Serum 2

## Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Inspect a map

```bash
python -m serum_map inspect "samples/default.SerumMIDIMap"
```

## Export decoded JSON

```bash
python -m serum_map decode "samples/default.SerumMIDIMap" --output decoded.json
```

## Build from a mapping CSV

```bash
python -m serum_map build \
  --controller data/MicroFreak.csv \
  --assignments data/microfreak_serum_assignments.csv \
  --template "samples/Novation Serum 2 Map.SerumMIDIMap" \
  --output MicroFreak.SerumMIDIMap
```

Generation is intentionally blocked unless all target Serum parameter IDs are explicit. The tool does not guess plugin parameters.

## Important limitation

The container structure and payload encoding are confirmed. The metadata `hash` field has not yet been proven. The writer currently supports preserving the template hash for controlled experiments, or accepting an explicitly supplied hash. A generated file should be treated as experimental until Serum 2 successfully imports it.
