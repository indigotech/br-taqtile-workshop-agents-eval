from collections.abc import Callable

import pytest

from app.evals.pass_metrics import pass_at_k, pass_hat_k


class TestPassAtK:
    @pytest.mark.parametrize(
        ("k", "expected"),
        [(1, 0.7), (3, 1 - 1 / 120), (4, 1.0), (10, 1.0)],
    )
    def test_seven_passes_out_of_ten_runs(self, k: int, expected: float) -> None:
        assert pass_at_k(10, 7, k) == pytest.approx(expected)

    def test_three_of_ten_failing_runs_is_about_99_percent_for_k_3(self) -> None:
        assert round(pass_at_k(10, 7, 3), 4) == 0.9917

    def test_no_passing_run_never_passes(self) -> None:
        assert pass_at_k(5, 0, 5) == 0.0

    def test_every_run_passing_always_passes(self) -> None:
        assert pass_at_k(5, 5, 1) == 1.0


class TestPassHatK:
    @pytest.mark.parametrize(
        ("k", "expected"),
        [(1, 0.7), (3, 35 / 120), (5, 21 / 252), (7, 1 / 120), (8, 0.0)],
    )
    def test_seven_passes_out_of_ten_runs(self, k: int, expected: float) -> None:
        assert pass_hat_k(10, 7, k) == pytest.approx(expected)

    def test_five_in_a_row_is_about_8_percent(self) -> None:
        assert round(pass_hat_k(10, 7, 5), 4) == 0.0833

    def test_k_equal_to_n_passes_only_when_every_run_passed(self) -> None:
        assert (pass_hat_k(3, 3, 3), pass_hat_k(3, 2, 3)) == (1.0, 0.0)

    def test_no_passing_run_never_passes(self) -> None:
        assert pass_hat_k(5, 0, 1) == 0.0


class TestPassMetricsInputs:
    @pytest.mark.parametrize("metric", [pass_at_k, pass_hat_k])
    @pytest.mark.parametrize(
        ("n", "c", "k"),
        [(10, 11, 1), (10, -1, 1), (10, 7, 0), (10, 7, 11), (0, 0, 1)],
    )
    def test_impossible_counts_are_rejected(
        self, metric: Callable[[int, int, int], float], n: int, c: int, k: int
    ) -> None:
        with pytest.raises(ValueError):
            metric(n, c, k)
