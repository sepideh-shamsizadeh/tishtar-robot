"""Hardware-independent tests for the TFmini frame parser.

Run with:  python -m pytest -q   (or: python -m unittest -v)
"""

import unittest

from tfmini_protocol import (
    FRAME_SIZE,
    TFminiStreamParser,
    compute_checksum,
    decode_frame,
)

# Frames actually received from the TISHTAR TFmini on /dev/ttyS0 (hexdump).
RECORDED_FRAMES = [
    bytes.fromhex("59 59 2f 00 41 0a 78 09 ad"),  # 47 cm, strength 2625
    bytes.fromhex("59 59 2f 00 44 0a 78 09 b0"),  # 47 cm, strength 2628
    bytes.fromhex("59 59 2f 00 3c 0a 78 09 a8"),  # 47 cm, strength 2620
]
FRAME = RECORDED_FRAMES[0]


def make_frame(distance: int, strength: int, extra: bytes = b"\x00\x00") -> bytes:
    """Build a synthetic frame with a correct checksum."""
    body = b"\x59\x59" + distance.to_bytes(2, "little") + strength.to_bytes(2, "little") + extra
    return body + bytes([compute_checksum(body)])


def corrupt_checksum(frame: bytes) -> bytes:
    return frame[:8] + bytes([(frame[8] + 1) & 0xFF])


class DecodeFrameTest(unittest.TestCase):
    def test_recorded_frame(self):
        frame = decode_frame(FRAME)
        self.assertTrue(frame.checksum_ok)
        self.assertEqual(frame.distance_cm, 47)
        self.assertEqual(frame.strength, 2625)
        self.assertEqual(frame.extra, b"\x78\x09")

    def test_all_recorded_frames_have_valid_checksums(self):
        for raw in RECORDED_FRAMES:
            with self.subTest(raw=raw.hex(" ")):
                self.assertTrue(decode_frame(raw).checksum_ok)

    def test_little_endian_decoding(self):
        frame = decode_frame(make_frame(distance=0x0102, strength=0xABCD))
        self.assertEqual(frame.distance_cm, 258)
        self.assertEqual(frame.strength, 43981)

    def test_incorrect_checksum(self):
        self.assertFalse(decode_frame(corrupt_checksum(FRAME)).checksum_ok)

    def test_rejects_wrong_length_or_header(self):
        with self.assertRaises(ValueError):
            decode_frame(FRAME[:8])
        with self.assertRaises(ValueError):
            decode_frame(b"\x00" + FRAME[1:])


class StreamParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = TFminiStreamParser()

    def valid(self, data: bytes):
        return [f for f in self.parser.feed(data) if f.checksum_ok]

    def test_single_valid_frame(self):
        frames = self.valid(FRAME)
        self.assertEqual([f.distance_cm for f in frames], [47])
        self.assertEqual(self.parser.stats.valid_frames, 1)

    def test_consecutive_frames(self):
        frames = self.valid(b"".join(RECORDED_FRAMES))
        self.assertEqual([f.strength for f in frames], [2625, 2628, 2620])
        self.assertEqual(self.parser.stats.discarded_bytes, 0)

    def test_incomplete_frame_is_buffered(self):
        self.assertEqual(self.parser.feed(FRAME[:5]), [])
        frames = self.valid(FRAME[5:])
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].raw, FRAME)

    def test_byte_by_byte_feed(self):
        frames = []
        for byte in b"".join(RECORDED_FRAMES):
            frames.extend(self.valid(bytes([byte])))
        self.assertEqual(len(frames), 3)

    def test_misaligned_start(self):
        # Stream joined mid-frame: tail of a previous frame, then a full frame.
        frames = self.valid(FRAME[3:] + RECORDED_FRAMES[1])
        self.assertEqual([f.raw for f in frames], [RECORDED_FRAMES[1]])

    def test_garbage_between_frames(self):
        frames = self.valid(FRAME + b"\x00\xff\x12\x59" + RECORDED_FRAMES[1])
        self.assertEqual(len(frames), 2)
        self.assertEqual(self.parser.stats.discarded_bytes, 4)

    def test_recovers_after_corrupted_checksum(self):
        frames = self.parser.feed(corrupt_checksum(FRAME) + RECORDED_FRAMES[1])
        self.assertFalse(frames[0].checksum_ok)
        self.assertEqual([f.raw for f in frames if f.checksum_ok], [RECORDED_FRAMES[1]])
        self.assertEqual(self.parser.stats.checksum_errors, 1)
        self.assertEqual(self.parser.stats.valid_frames, 1)

    def test_false_header_inside_frame(self):
        # Distance 89 cm = 0x59: misaligned by one byte, "59 59" appears at a
        # false position. The parser must slide forward one byte, not a frame.
        real = make_frame(distance=0x59, strength=100)
        frames = self.valid(b"\x59" + real + FRAME)
        self.assertEqual([f.distance_cm for f in frames], [89, 47])

    def test_lone_trailing_header_byte_is_kept(self):
        self.assertEqual(self.parser.feed(b"\x01\x02\x59"), [])
        frames = self.valid(FRAME[1:])
        self.assertEqual([f.raw for f in frames], [FRAME])

    def test_reset_clears_partial_frame(self):
        self.parser.feed(FRAME[:4])
        self.parser.reset()
        self.assertEqual(self.valid(FRAME[4:]), [])
        self.assertEqual(len(self.valid(FRAME)), 1)

    def test_frame_size_constant(self):
        self.assertEqual(FRAME_SIZE, len(FRAME))


if __name__ == "__main__":
    unittest.main()
