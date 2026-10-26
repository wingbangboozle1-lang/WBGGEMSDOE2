import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from scripts.legacy_format_validator import validate


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.reference = self.root / "reference.tif"
        self.candidate = self.root / "candidate.tif"
        self.transform = Affine(100, 0, 500000, 0, -100, 4500000)
        self.crs = "EPSG:32611"
        self._write(self.reference, np.ones((3, 4), dtype=np.float32))

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, path, values, *, crs=None, transform=None, count=None, nodata=None):
        values = np.asarray(values)
        if values.ndim == 2:
            values = values[np.newaxis, ...]
        count = count if count is not None else values.shape[0]
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=values.shape[1],
            width=values.shape[2],
            count=count,
            dtype=values.dtype,
            crs=crs or self.crs,
            transform=transform or self.transform,
            nodata=nodata,
        ) as dst:
            dst.write(values)

    def test_valid_float32_grid_passes_but_does_not_authorize(self):
        self._write(self.candidate, np.full((3, 4), 0.25, dtype=np.float32))
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["checks"]["finite_inside_footprint"])
        self.assertTrue(receipt["checks"]["range_0_1_all_pixels"])
        self.assertFalse(receipt["submission_authorized"])

    def test_out_of_range_value_fails(self):
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[1, 1] = 1.01
        self._write(self.candidate, values)
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["range_0_1_all_pixels"])

    def test_nan_outside_reference_footprint_still_fails_portal_range_gate(self):
        reference_values = np.ones((3, 4), dtype=np.float32)
        reference_values[2, 3] = -9999.0
        self._write(self.reference, reference_values, nodata=-9999.0)
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[2, 3] = np.nan
        self._write(self.candidate, values)
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertTrue(receipt["checks"]["finite_inside_footprint"])
        self.assertFalse(receipt["checks"]["finite_all_pixels"])

    def test_grid_mismatch_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), transform=Affine(100, 0, 500100, 0, -100, 4500000))
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["transform_match"])

    def test_wrong_dtype_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float64))
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["float32"])

    def test_crs_mismatch_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), crs="EPSG:4326")
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["crs_match"])

    def test_shape_mismatch_fails(self):
        self._write(self.candidate, np.full((2, 4), 0.5, dtype=np.float32))
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["shape_match"])

    def test_multiple_bands_fail(self):
        values = np.full((2, 3, 4), 0.5, dtype=np.float32)
        self._write(self.candidate, values)
        receipt = validate(self.candidate, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["single_band"])

    def test_non_tif_extension_fails(self):
        non_tif = self.root / "candidate.bin"
        self._write(non_tif, np.full((3, 4), 0.5, dtype=np.float32))
        receipt = validate(non_tif, self.reference)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["geotiff"])


if __name__ == "__main__":
    unittest.main()
