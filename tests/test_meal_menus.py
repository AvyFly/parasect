"""Functional testing of the various Menus."""
import pytest

from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from .utils import setup_px4  # noqa: F401 # setup_px4 is used by pytest as string
from parasect import build_lib


@pytest.fixture
def generic_meals():
    """Build the all generic meals."""
    return build_lib.build_meals()


@pytest.mark.usefixtures("setup_generic")
class TestGenericLightMeals:
    """Test that all Generic meals have generated correctly."""

    def test_light_meal(self, generic_meals):
        """Test if the light_meal has correctly generated."""
        light_meal = generic_meals["light_meal"]
        assert "BEEF" in light_meal.param_list.keys()
        assert "CUCUMBER" in light_meal.param_list.keys()
        assert "MUSHROOMS" not in light_meal.param_list.keys()
        assert "VINEGAR" not in light_meal.param_list.keys()
        assert "EGG" not in light_meal.param_list.keys()

    def test_spicy_meal(self, generic_meals):
        """Test if the spicy_meal has correctly generated."""
        spicy_meal = generic_meals["spicy_meal"]
        assert "BEEF" in spicy_meal.param_list.keys()
        assert "CHILLI" in spicy_meal.param_list.keys()
        assert "EGG" not in spicy_meal.param_list.keys()

    def test_full_meal(self, generic_meals):
        """Test if the full_meal has correctly generated."""
        full_meal = generic_meals["full_meal"]
        assert "BEEF" in full_meal.param_list.keys()
        assert "CHILLI" not in full_meal.param_list.keys()
        assert "EGG" in full_meal.param_list.keys()
        assert "PISTACHIO" not in full_meal.param_list.keys()

    def test_christmass_meal(self, generic_meals):
        """Test if the christmass_meal has correctly generated."""
        christmass_meal = generic_meals["christmass_at_grandmas"]
        assert christmass_meal.param_list["BEEF"].value == 5
