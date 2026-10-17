"""Simple reproducibility checks, using Python's built-in unittest runner."""
import unittest
import pandas as pd
from analysis import analyse, DATA

class AnalysisChecks(unittest.TestCase):
    def test_source_and_missingness(self):
        raw = pd.read_csv(DATA)
        original = raw.copy(deep=True)
        mass, pairs, summary, metrics = analyse(raw)
        pd.testing.assert_frame_equal(raw, original)
        self.assertEqual(len(raw), 344)
        self.assertEqual(len(mass), 342)
        self.assertEqual(len(pairs), 342)
        self.assertEqual(metrics['excluded_missing_mass'], 2)
        self.assertEqual(int(summary['count'].sum()), len(mass))
        self.assertEqual(summary.loc['Gentoo','median_g'], 5000)
        self.assertEqual(summary.loc['Adelie','median_g'], 3700)
        self.assertEqual(summary.loc['Chinstrap','median_g'], 3700)
        self.assertTrue(all(0 < r <= 1 for r in metrics['within_species_pearson_r'].values()))

if __name__ == '__main__':
    unittest.main()
