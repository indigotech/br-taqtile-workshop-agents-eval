from math import comb


def pass_at_k(n: int, c: int, k: int) -> float:
    """Chance that at least one of k runs drawn from n, c of which passed, passes.
    The unbiased estimator of Chen et al. 2021: 1 - C(n - c, k) / C(n, k)."""
    validate_samples(n, c, k)
    return 1 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """Chance that all k runs drawn from n, c of which passed, pass.
    The estimator of Yao et al. 2024 (tau-bench): C(c, k) / C(n, k)."""
    validate_samples(n, c, k)
    return comb(c, k) / comb(n, k)


def validate_samples(n: int, c: int, k: int) -> None:
    if not 0 <= c <= n:
        raise ValueError(f"c must be between 0 and n ({n}), got {c}")
    if not 1 <= k <= n:
        raise ValueError(f"k must be between 1 and n ({n}), got {k}")
