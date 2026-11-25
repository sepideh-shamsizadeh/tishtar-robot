"""TISHTAR - TFmini 9-byte serial frame parser.

Hardware-independent: this module never opens a serial port, so it can be
unit-tested without the sensor.

Frame layout (little-endian), as observed on the TISHTAR Raspberry Pi:

    byte  0-1  header        0x59 0x59
    byte  2-3  distance      uint16, centimetres
    byte  4-5  strength      uint16, signal strength (unitless)
    byte  6-7  extra         sensor/version specific, NOT interpreted here
    byte  8    checksum      sum(bytes 0..7) & 0xFF

Bytes 6-7 are kept raw on purpose: their meaning (mode, temperature, ...)
depends on the exact TFmini variant and firmware, which is not yet confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HEADER = b"\x59\x59"
FRAME_SIZE = 9


def compute_checksum(data: bytes) -> int:
    """Return the TFmini checksum of the first eight frame bytes."""
    return sum(data[:8]) & 0xFF


@dataclass(frozen=True)
class TFminiFrame:
    """One 9-byte frame aligned on a 0x59 0x59 header.

    ``checksum_ok`` distinguishes a correctly received frame from a corrupted
    or falsely aligned one. A checksum-valid frame is still only a *raw
    reading*: whether it is a physically valid measurement is a separate
    question answered by characterization (TF-03).
    """

    raw: bytes
    checksum_ok: bool

    @property
    def distance_cm(self) -> int:
        return int.from_bytes(self.raw[2:4], "little")

    @property
    def strength(self) -> int:
        return int.from_bytes(self.raw[4:6], "little")

    @property
    def extra(self) -> bytes:
        """Uninterpreted bytes 6-7."""
        return self.raw[6:8]

    @property
    def hex(self) -> str:
        return self.raw.hex(" ")


def decode_frame(raw: bytes) -> TFminiFrame:
    """Decode exactly one 9-byte frame that starts with the header."""
    if len(raw) != FRAME_SIZE:
        raise ValueError(f"expected {FRAME_SIZE} bytes, got {len(raw)}")
    if raw[:2] != HEADER:
        raise ValueError("frame does not start with 0x59 0x59")
    return TFminiFrame(raw=bytes(raw), checksum_ok=compute_checksum(raw) == raw[8])


@dataclass
class ParserStats:
    """Counters for diagnosing link quality."""

    valid_frames: int = 0
    checksum_errors: int = 0
    discarded_bytes: int = 0


@dataclass
class TFminiStreamParser:
    """Incremental parser for an arbitrary chunked byte stream.

    Feed it whatever ``serial.read()`` returns. Partial frames are buffered
    until complete. After a checksum failure the parser advances by one byte
    rather than a whole frame, so it re-synchronises even if the false header
    was inside a real frame (e.g. a distance of 89 cm = 0x59).
    """

    stats: ParserStats = field(default_factory=ParserStats)
    _buffer: bytearray = field(default_factory=bytearray, repr=False)

    def feed(self, data: bytes) -> list[TFminiFrame]:
        """Consume ``data`` and return every complete frame found.

        Frames with a bad checksum are returned too (``checksum_ok=False``)
        so callers can count invalid readings; filter them if not needed.
        """
        self._buffer.extend(data)
        frames: list[TFminiFrame] = []

        while True:
            start = self._buffer.find(HEADER)
            if start < 0:
                # Keep a trailing 0x59: it may be the first half of a header.
                keep = 1 if self._buffer.endswith(HEADER[:1]) else 0
                self._discard(len(self._buffer) - keep)
                break
            if start:
                self._discard(start)
            if len(self._buffer) < FRAME_SIZE:
                break  # incomplete frame, wait for more bytes

            frame = decode_frame(bytes(self._buffer[:FRAME_SIZE]))
            frames.append(frame)
            if frame.checksum_ok:
                self.stats.valid_frames += 1
                del self._buffer[:FRAME_SIZE]
            else:
                self.stats.checksum_errors += 1
                self._discard(1)

        return frames

    def reset(self) -> None:
        """Drop buffered bytes, e.g. after flushing the serial input."""
        self._buffer.clear()

    def _discard(self, count: int) -> None:
        if count > 0:
            del self._buffer[:count]
            self.stats.discarded_bytes += count
