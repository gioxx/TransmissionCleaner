import unittest

from app.presentation import format_size


class DisplayTests(unittest.TestCase):
    def test_formats_aggregated_sizes_for_dashboard(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(23 * 1_000_000_000), "23.00 GB")
        self.assertEqual(format_size(1_500_000_000), "1.50 GB")


if __name__ == "__main__":
    unittest.main()
