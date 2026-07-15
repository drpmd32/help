from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any


class DecodeError(ValueError):
    pass


@dataclass
class Reader:
    data: bytes
    pos: int = 0

    def read(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise DecodeError(f"Unexpected EOF at {self.pos}, need {n} bytes")
        out = self.data[self.pos:self.pos+n]
        self.pos += n
        return out

    def value(self) -> Any:
        marker = self.read(1)[0]
        if marker <= 0x17:
            return marker
        if marker == 0x18:
            return struct.unpack(">B", self.read(1))[0]
        if marker == 0x19:
            return struct.unpack(">H", self.read(2))[0]
        if marker == 0x1A:
            return struct.unpack(">I", self.read(4))[0]
        if 0x60 <= marker <= 0x77:
            return self.read(marker - 0x60).decode("utf-8")
        if marker == 0x78:
            return self.read(struct.unpack(">B", self.read(1))[0]).decode("utf-8")
        if marker == 0x79:
            return self.read(struct.unpack(">H", self.read(2))[0]).decode("utf-8")
        if 0x80 <= marker <= 0x9F:
            return [self.value() for _ in range(marker - 0x80)]
        if 0xA0 <= marker <= 0xBF:
            return {self.value(): self.value() for _ in range(marker - 0xA0)}
        if marker == 0xFA:
            return struct.unpack(">f", self.read(4))[0]
        if marker == 0xFB:
            return struct.unpack(">d", self.read(8))[0]
        if marker == 0xC0:
            return None
        if marker == 0xC2:
            return False
        if marker == 0xC3:
            return True
        raise DecodeError(f"Unsupported marker 0x{marker:02x} at offset {self.pos - 1}")


def decode(data: bytes) -> Any:
    reader = Reader(data)
    value = reader.value()
    if reader.pos != len(data):
        raise DecodeError(f"Trailing bytes: {len(data) - reader.pos} at offset {reader.pos}")
    return value


def encode(value: Any) -> bytes:
    if value is None:
        return b"\xC0"
    if value is False:
        return b"\xC2"
    if value is True:
        return b"\xC3"
    if isinstance(value, int):
        if 0 <= value <= 0x17:
            return bytes([value])
        if 0 <= value <= 0xFF:
            return b"\x18" + struct.pack(">B", value)
        if 0 <= value <= 0xFFFF:
            return b"\x19" + struct.pack(">H", value)
        if 0 <= value <= 0xFFFFFFFF:
            return b"\x1A" + struct.pack(">I", value)
        raise ValueError(f"Integer out of supported range: {value}")
    if isinstance(value, float):
        return b"\xFA" + struct.pack(">f", value)
    if isinstance(value, str):
        raw = value.encode("utf-8")
        if len(raw) <= 23:
            return bytes([0x60 + len(raw)]) + raw
        if len(raw) <= 0xFF:
            return b"\x78" + struct.pack(">B", len(raw)) + raw
        if len(raw) <= 0xFFFF:
            return b"\x79" + struct.pack(">H", len(raw)) + raw
        raise ValueError("String is too long")
    if isinstance(value, list):
        if len(value) > 31:
            raise ValueError("Only short arrays are currently supported")
        return bytes([0x80 + len(value)]) + b"".join(encode(v) for v in value)
    if isinstance(value, dict):
        if len(value) > 31:
            raise ValueError("Only short maps are currently supported")
        chunks = [bytes([0xA0 + len(value)])]
        for key, item in value.items():
            chunks.extend((encode(key), encode(item)))
        return b"".join(chunks)
    raise TypeError(f"Unsupported type: {type(value).__name__}")
