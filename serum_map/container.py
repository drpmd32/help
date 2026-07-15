from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import zstandard as zstd

from .codec import decode, encode

MAGIC = b"XferJson\x00"
COMPRESSION_ZSTD = 2


@dataclass
class SerumMap:
    header: dict[str, Any]
    payload: dict[str, Any]


def load(path: str | Path) -> SerumMap:
    data = Path(path).read_bytes()
    if not data.startswith(MAGIC):
        raise ValueError("Not an XferJson file")
    header_len = struct.unpack_from("<Q", data, len(MAGIC))[0]
    header_start = len(MAGIC) + 8
    header_end = header_start + header_len
    header = json.loads(data[header_start:header_end].decode("utf-8"))
    raw_len, compression = struct.unpack_from("<II", data, header_end)
    if compression != COMPRESSION_ZSTD:
        raise ValueError(f"Unsupported compression type: {compression}")
    raw = zstd.ZstdDecompressor().decompress(data[header_end + 8:], max_output_size=raw_len)
    if len(raw) != raw_len:
        raise ValueError(f"Payload length mismatch: expected {raw_len}, got {len(raw)}")
    payload = decode(raw)
    if not isinstance(payload, dict):
        raise ValueError("Decoded payload is not a map")
    return SerumMap(header=header, payload=payload)


def dump(map_file: SerumMap, path: str | Path, *, compression_level: int = 9) -> None:
    raw = encode(map_file.payload)
    compressed = zstd.ZstdCompressor(level=compression_level).compress(raw)
    header_bytes = json.dumps(map_file.header, separators=(",", ":")).encode("utf-8")
    output = MAGIC + struct.pack("<Q", len(header_bytes)) + header_bytes + struct.pack("<II", len(raw), COMPRESSION_ZSTD) + compressed
    Path(path).write_bytes(output)
