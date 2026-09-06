from __future__ import annotations

import unittest

from tools import validate_localizations


class LocalizationNumericTokenTests(unittest.TestCase):
    def test_editorial_punctuation_is_not_part_of_numeric_identity(self) -> None:
        # Footnote: language-local prose may move commas naturally. The strict
        # airlock protects the numeric value, including grouped numbers, decimals,
        # percentages and multipliers, rather than English sentence punctuation.
        text = "September 1, 2026; context 1,050,000; score 99.9%; speed 3.66x."
        self.assertEqual(
            validate_localizations.NUM.findall(text),
            ["1", "2026", "1,050,000", "99.9%", "3.66x"],
        )

    def test_decimal_and_grouped_values_still_differ_when_value_changes(self) -> None:
        source = "1,050,000 tokens at 62.7% and 3.66x speed."
        changed = "1,500,000 tokens at 62.7% and 3.66x speed."
        self.assertNotEqual(
            sorted(validate_localizations.NUM.findall(source)),
            sorted(validate_localizations.NUM.findall(changed)),
        )


if __name__ == "__main__":
    unittest.main()
