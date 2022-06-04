"""Test cases for the private build_lib module."""

import pydantic
import pytest

from . import utils
from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from .utils import setup_px4  # noqa: F401 # setup_px4 is used by pytest as string
from parasect import _helpers
from parasect import build_lib


@pytest.fixture
def generic_meals():
    """Build the all generic meals."""
    return build_lib.build_meals()


@pytest.mark.usefixtures("setup_generic")
class TestDish:
    """Testing the Dish class."""

    def test_str_(self):
        """Test the __str__ dunder method."""
        dish_model = build_lib.get_dish(_helpers.ConfigPaths().custom_dishes, "fruit")
        dish = build_lib.Dish(dish_model, "single")
        dish_str = str(dish)
        apple_str = str(dish.param_list["APPLE"])
        assert dish_str == apple_str
