"""Hardware-independent tests for the characterization statistics.

The rows below are SYNTHETIC test inputs chosen for easy hand calculation;
they are not experimental measurements.
"""

import math
import unittest

from tfmini_analyze import analyze


def row(distance, strength=1000, valid=True, t=0.0, ref=50, material="cardboard", exp="synthetic"):
    return {
        "experiment_id": exp,
        "timestamp_utc": "",
        "elapsed_s": str(t),
        "reference_distance_cm": str(ref),
        "target_material": material,
        "frame_valid": "1" if valid else "0",
        "distance_cm": str(distance) if valid else "",
        "strength": str(strength) if valid else "",
        "raw_frame_hex": "",
    }


class AnalysisTest(unittest.TestCase):
    def test_basic_statistics(self):
        # Distances 48, 50, 52, 54 at reference 50, 10 ms apart.
        rows = [row(d, t=i * 0.01) for i, d in enumerate([48, 50, 52, 54])]
        (s,) = analyze(rows)
        self.assertEqual(s.valid_measurements, 4)
        self.assertAlmostEqual(s.mean_cm, 51.0)
        self.assertAlmostEqual(s.median_cm, 51.0)
        self.assertAlmostEqual(s.std_cm, math.sqrt(20 / 3))  # sample std
        self.assertAlmostEqual(s.bias_cm, 1.0)
        self.assertAlmostEqual(s.mae_cm, (2 + 0 + 2 + 4) / 4)
        self.assertAlmostEqual(s.rmse_cm, math.sqrt((4 + 0 + 4 + 16) / 4))
        self.assertEqual((s.min_cm, s.max_cm), (48, 54))
        self.assertAlmostEqual(s.rate_hz, 100.0)
        self.assertEqual(s.invalid_rate, 0.0)

    def test_checksum_invalid_frames_are_not_measurements(self):
        rows = [row(50), row(0, valid=False), row(50, t=0.01), row(0, valid=False)]
        (s,) = analyze(rows)
        self.assertEqual(s.frames, 4)
        self.assertEqual(s.checksum_invalid, 2)
        self.assertEqual(s.valid_measurements, 2)
        self.assertAlmostEqual(s.invalid_rate, 0.5)
        self.assertAlmostEqual(s.mean_cm, 50.0)

    def test_sentinels_flagged_but_only_excluded_on_request(self):
        rows = [row(50), row(0, t=0.01), row(65535, t=0.02)]
        (kept,) = analyze(rows)
        self.assertEqual(kept.valid_measurements, 3)
        self.assertEqual((kept.suspect_zero, kept.suspect_65535), (1, 1))

        (excluded,) = analyze(rows, exclude_distances=[0, 65535])
        self.assertEqual(excluded.valid_measurements, 1)
        self.assertEqual(excluded.excluded, 2)
        self.assertAlmostEqual(excluded.invalid_rate, 2 / 3)

    def test_min_strength_filter(self):
        rows = [row(50, strength=10), row(50, strength=500, t=0.01)]
        (s,) = analyze(rows, min_strength=100)
        self.assertEqual((s.valid_measurements, s.excluded), (1, 1))

    def test_groups_by_reference_and_material(self):
        rows = [row(10, ref=10), row(50, ref=50), row(51, ref=50, material="black foam")]
        summaries = analyze(rows)
        keys = [(s.reference_distance_cm, s.target_material) for s in summaries]
        self.assertEqual(keys, [(10.0, "cardboard"), (50.0, "black foam"), (50.0, "cardboard")])

    def test_no_valid_measurements(self):
        (s,) = analyze([row(0, valid=False)])
        self.assertEqual(s.valid_measurements, 0)
        self.assertIsNone(s.mean_cm)
        self.assertEqual(s.invalid_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
