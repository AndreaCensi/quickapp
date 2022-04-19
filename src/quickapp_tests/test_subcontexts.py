import unittest

from quickapp.app_utils.minimal_name import minimal_names, minimal_names_at_boundaries


class TestMinimal(unittest.TestCase):
    def test_minimal_names_at_boundaries(self):
        objects = ["test_random_dpx1_64_10", "test_random_drob1_64_10"]

        prefix, minimal, postfix = minimal_names_at_boundaries(objects)

        self.assertEqual(prefix, "test_random_")
        self.assertEqual(postfix, "_64_10")

        self.assertEqual(minimal, ["dpx1", "drob1"])

    def test_minimal_names(self):
        objects = ["test_random_dpx1_64_10", "test_random_drob1_64_10"]

        prefix, minimal, postfix = minimal_names(objects)

        self.assertEqual(prefix, "test_random_d")
        self.assertEqual(postfix, "1_64_10")

        self.assertEqual(minimal, ["px", "rob"])
