"""Utilities to deal with data."""

import warnings
from collections.abc import Iterator

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from tqdm import trange

from src.utils.stochastic_processes import AR1, CycleRandomWalk, Renewal, TwoStateMarkovChain


class SequentialSplit:
    """Sequential data splitter."""

    def __init__(
        self,
        sizes: tuple[int, ...],
        show_progress: bool = True,

    ) -> None:
        """Initialize with tuple representing the size of each set in a split."""
        self.sizes = sizes
        self.show_progress = show_progress

    def split(
        self,
        X: ArrayLike,
    ) -> Iterator[list[list[int]]]:
        """Iterate sequentially over possible splits given set sizes."""
        indices = np.arange(X.shape[0]).tolist()
        n_splits = len(indices) - sum(self.sizes) + 1
        for t in trange(n_splits) if self.show_progress else range(n_splits):
            yield [
                indices[t + sum(self.sizes[:j]) : t + sum(self.sizes[:j+1])]
                for j in range(len(self.sizes))
            ]


def get_data(
    target: str,
    target_gap: int,
    maxlags: int,
    year: int,
) -> pd.DataFrame:
    """Get processed data with specified lagged features and set target variable."""
    if target and target_gap < 1:
        raise ValueError("A gap less than 1 would constitute data leakage and is not allowed.")
    if not target and target_gap:
        warnings.warn(
            "Warning: No target variable was passed, but a gap was given. Gap will be ignored.",
        )
    df = pd.read_csv(
        f"data/processed/df-{target}-{year}-maxlags_{maxlags}.csv",
        index_col="datetime",
        parse_dates=["datetime"],
    )
    if target:
        df["target"] = df[target].shift(-target_gap)
    return df.dropna(axis=0)


def get_synthetic(
    stochastic_process: str,
    N: int,
    lags: int,
    seed: int | None = None,
    **kwargs: int | float,
) -> pd.DataFrame:
    """Generate dataset from stochastic process."""
    # Initialize stochastic process class
    sp: AR1 | CycleRandomWalk | Renewal | TwoStateMarkovChain
    if stochastic_process == "ar1":
        sp = AR1(**kwargs)
    elif stochastic_process == "cycle_random_walk":
        sp = CycleRandomWalk(**kwargs)
    elif stochastic_process == "renewal":
        sp = Renewal(**kwargs)
    elif stochastic_process == "two_state_markov_chain":
        sp = TwoStateMarkovChain(**kwargs)
    else:
        raise ValueError(f"Stochastic process {stochastic_process} is not available.")

    # Generate sequence
    sequence = sp.generate(N=N+lags+1, seed=seed)

    # Add small gaussian noise to discrete sequences.
    # This is particularly important for binary sequences, otherwise
    # it would not be possible to compute meaningful quantiles.
    match stochastic_process:
        case "cycle_random_walk" | "renewal" | "two_state_markov_chain":
            rng = np.random.default_rng(seed)
            sequence = rng.normal(sequence, scale=1e-6)

    # Create dataframe with original sequence and lags
    df = pd.DataFrame(sequence, columns=["value"])
    for lag in range(1, lags + 1):
        df[f"value_lag_{lag}"] = df["value"].shift(lag)

    # Set target as next unseen observation
    df["target"] = df["value"].shift(-1)

    # Drop missing values introduced during lagged variables creation
    df = df.dropna().reset_index(drop=True)

    # Verify resulting dataframe is of expected length
    assert len(df) == N

    return df
