"""Seeded RNG wrapper for reproducible V0 sampling."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class SeededRNG:
    """Wraps ``random.Random`` with an explicit seed and typed sampling helpers."""

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self._random = random.Random(seed)

    def random(self) -> float:
        return self._random.random()

    def choice(self, seq: Sequence[T]) -> T:
        return self._random.choice(seq)

    def weighted_choice(self, pairs: Sequence[tuple[T, float]]) -> T:
        if not pairs:
            raise ValueError(
                "weighted_choice requires at least one (item, weight) pair"
            )
        items = [item for item, _weight in pairs]
        weights = [weight for _item, weight in pairs]
        return self._random.choices(items, weights=weights, k=1)[0]

    def normal(self, median: float, std: float) -> int:
        return int(round(self._random.gauss(median, std)))

    def uniform_int(self, min: int, max: int) -> int:
        return self._random.randint(min, max)
