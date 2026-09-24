import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class StreamlitAppSmokeTests(unittest.TestCase):
    def test_app_loads_without_exceptions(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path))
        app.run(timeout=15)
        self.assertEqual([], list(app.exception))


if __name__ == "__main__":
    unittest.main()
