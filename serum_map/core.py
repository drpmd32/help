from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import msgpack
import zstandard as zstd

MAGIC = b"XferJson\x00"
COMPRESSION_ZSTD = 2


@dataclass(slots=True)
class SerumMap:
    header: dict[str, Any]
    payload: dict[str, Any]
    compression_type: int = COMPRESSION_ZSTD


def read_map(path: str | Path) -> SerumMap:
    raw = Path(path).read_bytes()
    if not raw.startswith(MAGIC):
        raise ValueError("Not an XferJson container")

    offset = len(MAGIC)
    header_length = struct.unpack_from("<Q", raw, offset)[0]
    offset += 8
    header = json.loads(raw[offset : offset + header_length])
    offset += header_length

    expected_size, compression_type = struct.unpack_from("<II", raw, offset)
    offset += 8
    if compression_type != COMPRESSION_ZSTD:
        raise ValueError(f"Unsupported compression type: {compression_type}")

    decoded = zstd.ZstdDecompressor().decompress(raw[offset:], max_output_size=expected_size)
    if len(decoded) != expected_size:
        raise ValueError(f"Payload length mismatch: expected {expected_size}, got {len(decoded)}")

    payload = msgpack.unpackb(decoded, raw=False, strict_map_key=False)
    return SerumMap(header=header, payload=payload, compression_type=compression_type)


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return msgpack.packb(payload, use_bin_type=True)


def candidate_hash(payload_bytes: bytes) -> str:
    """Experimental only; the actual Xfer hash algorithm is not confirmed."""
    return hashlib.md5(payload_bytes).hexdigest()


def write_map(
    serum_map: SerumMap,
    path: str | Path,
    *,
    preserve_header_hash: bool = True,
    explicit_hash: str | None = None,
) -> None:
    payload_bytes = canonical_payload_bytes(serum_map.payload)
    compressed = zstd.ZstdCompressor(level=3).compress(payload_bytes)

    header = dict(serum_map.header)
    if explicit_hash is not None:
        header["hash"] = explicit_hash
    elif not preserve_header_hash:
        header["hash"] = candidate_hash(payload_bytes)

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    output = bytearray(MAGIC)
    output += struct.pack("<Q", len(header_bytes))
    output += header_bytes
    output += struct.pack("<II", len(payload_bytes), serum_map.compression_type)
    output += compressed
    Path(path).write_bytes(output)


def midi_entries(serum_map: SerumMap) -> list[dict[str, Any]]:
    entries = serum_map.payload.get("midiMap")
    if not isinstance(entries, list):
        raise ValueError("Payload does not contain a midiMap list")
    return entries
