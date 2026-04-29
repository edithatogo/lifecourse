from __future__ import annotations

import os
import tempfile
import unittest
from collections.abc import Iterable
from unittest.mock import patch

import pandas as pd
import pytest
from lifecourse.backend_evaluation import BackendUnavailableError
from lifecourse.data_loader import (
    apply_scenario_overrides,
    load_nz_life_table_hazards,
    load_nz_population_distribution,
    load_scenarios_from_yaml,
)


class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary YAML file for testing
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            self.temp_file = temp_file
            self.temp_file.write("""
scenarios:
  base:
    param1: null
    param2: 10
  scenario_a:
    param1: 5
    param2: null
  scenario_b:
    param1: null
    param2: 20

scenario_grid:
  param1: [1, 2]
  param2: [100, 200]
""")

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)

    def test_load_scenarios_from_yaml(self):
        """Test loading scenarios from YAML file."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Check that all scenarios are loaded
        self.assertIn("base", scenarios)
        self.assertIn("scenario_a", scenarios)
        self.assertIn("scenario_b", scenarios)

        # Check specific values
        self.assertEqual(scenarios["base"]["param2"], 10)
        self.assertEqual(scenarios["scenario_a"]["param1"], 5)
        self.assertIsNone(scenarios["scenario_a"]["param2"])

    def test_scenario_grid_generation(self):
        """Test that scenario grid definitions are properly expanded."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Check that grid scenarios are generated
        self.assertIn("param1_1_param2_100", scenarios)
        self.assertIn("param1_1_param2_200", scenarios)
        self.assertIn("param1_2_param2_100", scenarios)
        self.assertIn("param1_2_param2_200", scenarios)

        # Check specific values in grid scenarios
        self.assertEqual(scenarios["param1_1_param2_100"]["param1"], 1)
        self.assertEqual(scenarios["param1_1_param2_100"]["param2"], 100)
        self.assertEqual(scenarios["param1_2_param2_200"]["param1"], 2)
        self.assertEqual(scenarios["param1_2_param2_200"]["param2"], 200)

    def test_scenario_grid_combinatorial_expansion(self):
        """Test that all combinations in scenario grid are generated."""
        scenarios = load_scenarios_from_yaml(self.temp_file.name)

        # Count grid scenarios by checking if they contain both parameter names
        grid_scenarios = [
            name for name in scenarios if "param1_" in name and "param2_" in name
        ]

        # Should have 2 * 2 = 4 combinations
        self.assertEqual(len(grid_scenarios), 4)

        # Check that all expected combinations exist
        expected_names = [
            "param1_1_param2_100",
            "param1_1_param2_200",
            "param1_2_param2_100",
            "param1_2_param2_200",
        ]

        for name in expected_names:
            self.assertIn(name, scenarios)

    def test_scenario_grid_polars_backend_matches_default(self):
        """Test opt-in Polars grid expansion preserves scenario output."""
        default_scenarios = load_scenarios_from_yaml(self.temp_file.name)

        class FakePolarsDataFrame:
            def __init__(self, rows: list[dict[str, object]]) -> None:
                self._rows = rows

            def iter_rows(self, named: bool = False):
                if not named:
                    raise AssertionError("Polars grid expansion should request names")
                return iter(self._rows)

        class FakePolars:
            @staticmethod
            def DataFrame(rows: list[dict[str, object]]) -> FakePolarsDataFrame:
                return FakePolarsDataFrame(rows)

        with (
            patch("lifecourse.data_loader.find_spec", lambda name: object()),
            patch("lifecourse.data_loader.import_module", lambda name: FakePolars()),
        ):
            polars_scenarios = load_scenarios_from_yaml(
                self.temp_file.name, scenario_backend="polars"
            )

        self.assertEqual(polars_scenarios, default_scenarios)

    def test_scenario_grid_polars_backend_missing(self):
        """Test scenario Polars backend fails clearly when optional extra is absent."""
        with (
            patch("lifecourse.data_loader.find_spec", lambda name: None),
            pytest.raises(BackendUnavailableError, match="Polars backend requested"),
        ):
            load_scenarios_from_yaml(self.temp_file.name, scenario_backend="polars")

    def test_scenario_grid_rejects_unknown_backend(self):
        """Test invalid scenario backend names fail before expansion."""
        with pytest.raises(ValueError, match="Unsupported scenario backend"):
            load_scenarios_from_yaml(
                self.temp_file.name,
                scenario_backend="duckdb",  # type: ignore[arg-type]
            )

    def test_apply_scenario_overrides(self):
        """Test applying scenario overrides to base parameters."""
        base_params = {"param1": 100, "param2": 200, "param3": 300}

        overrides = {
            "param1": 150,  # Absolute value
            "param2": 0.1,  # Relative adjustment (small value)
            "param3": None,  # No change
        }

        result = apply_scenario_overrides(base_params, overrides)

        # Check absolute value override
        self.assertEqual(result["param1"], 150)

        # Check relative adjustment
        self.assertEqual(result["param2"], 200.1)  # 200 + 0.1

        # Check no change when None
        self.assertEqual(result["param3"], 300)

    def test_apply_scenario_overrides_with_severity_prop(self):
        """Test that severity proportions are correctly handled."""
        base_params = {"severity_mild_prop": 0.7, "severity_severe_prop": 0.3}

        overrides = {"severity_mild_prop": 0.8}

        result = apply_scenario_overrides(base_params, overrides)

        # Check that mild prop is updated
        self.assertEqual(result["severity_mild_prop"], 0.8)

        # Check that severe prop is automatically updated to maintain sum = 1
        # Using almost equal for floating point comparison
        self.assertAlmostEqual(result["severity_severe_prop"], 0.2, places=10)

    def test_scenario_name_sanitization(self):
        """Test that scenario names are properly sanitized."""
        # Create a temporary YAML file with decimal values
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            temp_file.write("""
scenario_grid:
  param_with_decimal: [0.1, 0.2]
  another_param: [1.5, 2.5]
""")

        try:
            scenarios = load_scenarios_from_yaml(temp_file.name)

            # Check that decimal points are replaced with underscores in names
            self.assertIn("param_with_decimal_0_1_another_param_1_5", scenarios)
            self.assertIn("param_with_decimal_0_1_another_param_2_5", scenarios)
            self.assertIn("param_with_decimal_0_2_another_param_1_5", scenarios)
            self.assertIn("param_with_decimal_0_2_another_param_2_5", scenarios)
        finally:
            os.unlink(temp_file.name)

    @patch("pandas.read_csv")
    def test_load_nz_population_distribution(self, mock_read_csv):
        """Test loading NZ population distribution data."""
        # Mock the CSV data
        mock_data = {
            "Geography": ["New Zealand", "Auckland", "New Zealand"],
            "Age": ["0-4", "5-9", "10-14"],
            "Sex": ["Male", "Female", "Male"],
            "Population": [100, 200, 150],
        }

        mock_df = pd.DataFrame(mock_data)
        mock_read_csv.return_value = mock_df

        result = load_nz_population_distribution()

        # Check that pandas.read_csv was called
        mock_read_csv.assert_called_once()

        # Check the result structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(list(result.columns), ["age", "sex", "count"])

        # Check data transformation
        self.assertEqual(result.iloc[0]["age"], 0)  # '0-4' -> 0
        self.assertEqual(result.iloc[0]["sex"], "Male")
        self.assertEqual(result.iloc[0]["count"], 100)

    @patch("pandas.read_csv")
    def test_load_nz_population_distribution_explicit_pandas(self, mock_read_csv):
        """Test explicit pandas backend remains equivalent to the default."""
        mock_read_csv.return_value = pd.DataFrame(
            {
                "Geography": ["New Zealand"],
                "Age": ["0-4"],
                "Sex": ["Female"],
                "Population": [120],
            }
        )

        result = load_nz_population_distribution(backend="pandas")

        self.assertListEqual(list(result.columns), ["age", "sex", "count"])
        self.assertEqual(result.iloc[0]["age"], 0)
        self.assertEqual(result.iloc[0]["sex"], "Female")
        self.assertEqual(result.iloc[0]["count"], 120)

    def test_load_nz_population_distribution_rejects_unknown_backend(self):
        """Test invalid backend names fail before attempting network access."""
        with pytest.raises(ValueError, match="Unsupported population backend"):
            load_nz_population_distribution(backend="duckdb")  # type: ignore[arg-type]

    def test_load_nz_population_distribution_polars_missing(self):
        """Test requesting Polars fails clearly when the optional extra is absent."""
        with (
            patch("lifecourse.data_loader.find_spec", lambda name: None),
            pytest.raises(BackendUnavailableError, match="Polars backend requested"),
        ):
            load_nz_population_distribution(backend="polars")

    def test_load_nz_population_distribution_polars_backend(self):
        """Test the opt-in Polars path can normalize data and return pandas output."""
        calls: list[str] = []

        class FakeStringNamespace:
            def __init__(self, expression: FakeExpression) -> None:
                self._expression = expression

            def extract(self, _pattern: str) -> FakeExpression:
                calls.append("extract")
                return self._expression

        class FakeExpression:
            str: FakeStringNamespace

            def __init__(self, column: str) -> None:
                self.column = column
                self.str = FakeStringNamespace(self)

            def __eq__(self, other: object) -> tuple[str, str, object]:  # type: ignore[override]
                return ("eq", self.column, other)

            def cast(self, _dtype: object) -> FakeExpression:
                calls.append("cast")
                return self

        class FakePolarsFrame:
            def __init__(self, frame: pd.DataFrame) -> None:
                self._frame = frame
                self.columns = list(frame.columns)

            def filter(self, expression: tuple[str, str, object]) -> FakePolarsFrame:
                calls.append("filter")
                _op, column, value = expression
                return FakePolarsFrame(self._frame[self._frame[column] == value])

            def rename(self, columns: dict[str, str]) -> FakePolarsFrame:
                calls.append("rename")
                return FakePolarsFrame(self._frame.rename(columns=columns))

            def with_columns(self, _expression: FakeExpression) -> FakePolarsFrame:
                calls.append("with_columns")
                updated = self._frame.copy()
                updated["age"] = (
                    updated["age"].astype(str).str.extract(r"(\d+)")[0].astype(int)
                )
                return FakePolarsFrame(updated)

            def select(self, columns: Iterable[str]) -> FakePolarsFrame:
                calls.append("select")
                return FakePolarsFrame(self._frame[list(columns)])

            def to_pandas(self) -> pd.DataFrame:
                calls.append("to_pandas")
                return self._frame.copy()

        class FakePolars:
            Utf8 = object()
            Int64 = object()

            @staticmethod
            def col(column: str) -> FakeExpression:
                return FakeExpression(column)

            @staticmethod
            def read_csv(_url: str) -> FakePolarsFrame:
                calls.append("read_csv")
                return FakePolarsFrame(
                    pd.DataFrame(
                        {
                            "Geography": ["New Zealand", "Auckland"],
                            "Age": ["0-4", "5-9"],
                            "Sex": ["Male", "Female"],
                            "Population": [100, 200],
                        }
                    )
                )

        with (
            patch("lifecourse.data_loader.find_spec", lambda name: object()),
            patch("lifecourse.data_loader.import_module", lambda name: FakePolars()),
        ):
            result = load_nz_population_distribution(backend="polars")

        self.assertListEqual(list(result.columns), ["age", "sex", "count"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["age"], 0)
        self.assertEqual(result.iloc[0]["sex"], "Male")
        self.assertEqual(result.iloc[0]["count"], 100)
        self.assertIn("read_csv", calls)
        self.assertIn("to_pandas", calls)

    @patch("pandas.read_csv")
    def test_load_nz_life_table_hazards(self, mock_read_csv):
        """Test loading NZ life table hazards data."""
        # Mock the CSV data
        mock_data = {
            "Sex": ["Male", "Male", "Female", "Female"],
            "Age": [0, 1, 0, 1],
            "nMx": [0.01, 0.02, 0.005, 0.015],
        }

        mock_df = pd.DataFrame(mock_data)
        mock_read_csv.return_value = mock_df

        result = load_nz_life_table_hazards()

        # Check that pandas.read_csv was called
        mock_read_csv.assert_called_once()

        # Check the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("Male", result)
        self.assertIn("Female", result)

        # Check data transformation
        self.assertEqual(len(result["Male"]), 2)
        self.assertEqual(len(result["Female"]), 2)
        self.assertEqual(result["Male"][0], 0.01)  # Age 0 for Male
        self.assertEqual(result["Male"][1], 0.02)  # Age 1 for Male

    @patch("pandas.read_csv")
    def test_load_nz_life_table_hazards_explicit_pandas(self, mock_read_csv):
        """Test explicit pandas backend remains equivalent to the default."""
        mock_read_csv.return_value = pd.DataFrame(
            {
                "Sex": ["Female", "Female"],
                "Age": [1, 0],
                "nMx": [0.015, 0.005],
            }
        )

        result = load_nz_life_table_hazards(backend="pandas")

        self.assertEqual(list(result.keys()), ["Female"])
        self.assertListEqual(result["Female"].tolist(), [0.005, 0.015])

    def test_load_nz_life_table_hazards_rejects_unknown_backend(self):
        """Test invalid life-table backend names fail before network access."""
        with pytest.raises(ValueError, match="Unsupported life-table backend"):
            load_nz_life_table_hazards(backend="duckdb")  # type: ignore[arg-type]

    def test_load_nz_life_table_hazards_polars_missing(self):
        """Test requesting Polars life-table loading fails clearly if absent."""
        with (
            patch("lifecourse.data_loader.find_spec", lambda name: None),
            pytest.raises(BackendUnavailableError, match="Polars backend requested"),
        ):
            load_nz_life_table_hazards(backend="polars")

    def test_load_nz_life_table_hazards_polars_backend(self):
        """Test the opt-in Polars life-table path returns numpy hazard arrays."""
        calls: list[str] = []

        class FakePolarsFrame:
            def __init__(self, frame: pd.DataFrame) -> None:
                self._frame = frame

            def rename(self, columns: dict[str, str]) -> FakePolarsFrame:
                calls.append("rename")
                return FakePolarsFrame(self._frame.rename(columns=columns))

            def select(self, columns: Iterable[str]) -> FakePolarsFrame:
                calls.append("select")
                return FakePolarsFrame(self._frame[list(columns)])

            def to_pandas(self) -> pd.DataFrame:
                calls.append("to_pandas")
                return self._frame.copy()

        class FakePolars:
            @staticmethod
            def read_csv(_url: str) -> FakePolarsFrame:
                calls.append("read_csv")
                return FakePolarsFrame(
                    pd.DataFrame(
                        {
                            "Sex": ["Male", "Female", "Male", "Female"],
                            "Age": [1, 1, 0, 0],
                            "nMx": [0.02, 0.015, 0.01, 0.005],
                        }
                    )
                )

        with (
            patch("lifecourse.data_loader.find_spec", lambda name: object()),
            patch("lifecourse.data_loader.import_module", lambda name: FakePolars()),
        ):
            result = load_nz_life_table_hazards(backend="polars")

        self.assertListEqual(result["Male"].tolist(), [0.01, 0.02])
        self.assertListEqual(result["Female"].tolist(), [0.005, 0.015])
        self.assertIn("read_csv", calls)
        self.assertIn("to_pandas", calls)


if __name__ == "__main__":
    unittest.main()
