import pandas as pd
from django.test import SimpleTestCase

from .trainer import train
from .validation import DatasetValidationError, build_metadata


class RegressionCsvTests(SimpleTestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            {
                "size": list(range(10, 30)),
                "Price": [100 + value * 5 for value in range(20)],
            }
        )

    def test_regression_metadata_exposes_numeric_price_target(self):
        metadata = build_metadata(self.dataframe, task="regression")
        self.assertIn("Price", metadata["target_candidates"])

    def test_regression_training_accepts_continuous_price_target(self):
        result = train(self.dataframe, "Price", algorithm="LINEAR_REGRESSION")
        self.assertEqual(result.metadata["task"], "regression")
        self.assertIn("rmse", result.metrics)

    def test_classification_rejects_continuous_price_target(self):
        with self.assertRaises(DatasetValidationError):
            train(self.dataframe, "Price", algorithm="RANDOM_FOREST_CLASSIFIER")
