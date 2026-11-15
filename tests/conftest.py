import random

import pytest

from arcade.player import new_player


@pytest.fixture
def rng():
    return random.Random(42)


@pytest.fixture
def player():
    return new_player("TESTER")
