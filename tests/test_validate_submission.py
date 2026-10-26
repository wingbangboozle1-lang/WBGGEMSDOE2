import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from scripts.validate_submission import validate


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.reference = self.root / "reference.tif"
        self.candidate = self.root / "candidate.tif"
        self.transform = Affine(100, 0, 500000, 0, -100, 4500000)
        self.crs = "EPSG:32611"
        self.expected_grid = {"crs": self.crs, "shape": (3, 4), "transform": tuple(self.transform)[:6]}
        self._write(self.reference, np.ones((3, 4), dtype=np.float32))

    def tearDown(self):
        self.tmp.cleanup()

    def _validate(self, candidate=None):
        return validate(candidate or self.candidate, self.reference, expected_grid=self.expected_grid)

    def _write(self, path, values, *, crs=None, transform=None, count=None, nodata=None, mask=None, internal_mask=True):
        values = np.asarray(values)
        if values.ndim == 2:
            values = values[np.newaxis, ...]
        count = count if count is not None else values.shape[0]
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=internal_mask):
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
                if mask is not None:
                    dst.write_mask(mask)

    def test_valid_float32_grid_passes_but_does_not_authorize(self):
        self._write(self.candidate, np.full((3, 4), 0.25, dtype=np.float32))
        receipt = self._validate()
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["checks"]["finite_inside_footprint"])
        self.assertTrue(receipt["checks"]["range_0_1_all_pixels"])
        self.assertFalse(receipt["submission_authorized"])

    def test_out_of_range_value_fails(self):
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[1, 1] = 1.01
        self._write(self.candidate, values)
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["range_0_1_all_pixels"])

    def test_nan_outside_reference_footprint_fails_conservative_range_gate(self):
        reference_values = np.ones((3, 4), dtype=np.float32)
        reference_values[2, 3] = -9999.0
        self._write(self.reference, reference_values, nodata=-9999.0)
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[2, 3] = np.nan
        self._write(self.candidate, values)
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertTrue(receipt["checks"]["finite_inside_footprint"])
        self.assertFalse(receipt["checks"]["finite_all_pixels"])

    def test_candidate_and_reference_both_on_wrong_grid_fail(self):
        wrong = Affine(100, 0, 500100, 0, -100, 4500000)
        self._write(self.reference, np.ones((3, 4), dtype=np.float32), transform=wrong)
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), transform=wrong)
        receipt = self._validate()
        self.assertTrue(receipt["checks"]["transform_match"])
        self.assertFalse(receipt["checks"]["reference_expected_transform"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_cli_default_uses_pinned_full_size_grid(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32))
        receipt = validate(self.candidate, self.reference)
        self.assertFalse(receipt["checks"]["reference_expected_shape"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_masked_exterior_and_finite_values_pass_local_checks_only(self):
        reference_values = np.ones((3, 4), dtype=np.float32)
        reference_values[2, 3] = -9999.0
        self._write(self.reference, reference_values, nodata=-9999.0)
        mask = np.full((3, 4), 255, dtype=np.uint8)
        mask[2, 3] = 0
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[2, 3] = 0.0
        self._write(self.candidate, values, mask=mask)
        receipt = self._validate()
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["checks"]["mask_valid_inside_footprint"])
        self.assertTrue(receipt["checks"]["mask_null_outside_footprint"])
        self.assertTrue(receipt["checks"]["standalone_file"])
        self.assertFalse(receipt["submission_authorized"])

    def test_unmasked_exterior_fails(self):
        reference_values = np.ones((3, 4), dtype=np.float32)
        reference_values[2, 3] = -9999.0
        self._write(self.reference, reference_values, nodata=-9999.0)
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32))
        receipt = self._validate()
        self.assertFalse(receipt["checks"]["mask_null_outside_footprint"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_masked_interior_fails(self):
        mask = np.full((3, 4), 255, dtype=np.uint8)
        mask[1, 1] = 0
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), mask=mask)
        receipt = self._validate()
        self.assertFalse(receipt["checks"]["mask_valid_inside_footprint"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_external_mask_sidecar_fails(self):
        mask = np.full((3, 4), 255, dtype=np.uint8)
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), mask=mask, internal_mask=False)
        receipt = self._validate()
        self.assertFalse(receipt["checks"]["standalone_file"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_nan_inside_footprint_fails(self):
        values = np.full((3, 4), 0.5, dtype=np.float32)
        values[1, 1] = np.nan
        self._write(self.candidate, values)
        receipt = self._validate()
        self.assertFalse(receipt["checks"]["finite_inside_footprint"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_grid_mismatch_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), transform=Affine(100, 0, 500100, 0, -100, 4500000))
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["transform_match"])

    def test_wrong_dtype_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float64))
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["float32"])

    def test_crs_mismatch_fails(self):
        self._write(self.candidate, np.full((3, 4), 0.5, dtype=np.float32), crs="EPSG:4326")
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["crs_match"])

    def test_shape_mismatch_fails(self):
        self._write(self.candidate, np.full((2, 4), 0.5, dtype=np.float32))
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["shape_match"])

    def test_multiple_bands_fail(self):
        values = np.full((2, 3, 4), 0.5, dtype=np.float32)
        self._write(self.candidate, values)
        receipt = self._validate()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["single_band"])

    def test_non_tif_extension_fails(self):
        non_tif = self.root / "candidate.bin"
        self._write(non_tif, np.full((3, 4), 0.5, dtype=np.float32))
        receipt = self._validate(non_tif)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertFalse(receipt["checks"]["geotiff"])


if __name__ == "__main__":
    unittest.main()
