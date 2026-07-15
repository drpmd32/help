# Serum MIDI Map Generator

Tools for inspecting and generating Xfer Serum 2 `.SerumMIDIMap` files.

## What works

- Parses the `XferJson` container
- Decompresses and compresses Zstandard payloads
- Decodes and encodes the Xfer compact binary value format
- Round-trips the supplied Serum 2 maps
- Generates an experimental MicroFreak map using the eight target parameter IDs from Serum's default map

## MicroFreak mapping

The generated map assigns these MicroFreak CCs to the eight targets from Serum's default map:

| MicroFreak control | CC |
|---|---:|
| Cutoff | 23 |
| Resonance | 83 |
| Timbre | 12 |
| Shape | 13 |
| Wave | 10 |
| Filter amount | 26 |
| Envelope attack | 105 |
| Envelope decay | 106 |

Because Xfer's internal parameter IDs are not publicly named in the file, the generator preserves the eight target IDs from the default Serum map rather than guessing IDs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Inspect a map

```bash
python -m serum_map inspect "samples/default.SerumMIDIMap"
```

## Generate the MicroFreak map

```bash
python -m serum_map build-microfreak \
  --controller data/MicroFreak.csv \
  --template samples/default.SerumMIDIMap \
  --output MicroFreak.SerumMIDIMap
```

## Validation status

The generated file is structurally valid and can be parsed back losslessly by this project. It still requires a real Serum 2 import test. The header hash is preserved from the template because its algorithm or semantics have not yet been confirmed.
