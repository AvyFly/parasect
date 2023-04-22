"""Functional testing of the various Menus."""
import pytest

from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import (  # noqa: F401 # setup_px4 is used by pytest as string
    fixture_setup_px4,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from parasect import build_lib


@pytest.fixture
def generic_meals():
    """Build the all generic meals."""
    return build_lib.build_meals()


@pytest.mark.usefixtures("setup_generic")
class TestGenericMeals:
    """Test that all Generic meals have generated correctly."""

    def test_snack(self, generic_meals):
        """Test if the snack has correctly generated."""
        snack = generic_meals["snack"]
        assert "APPLE" in snack.param_list

    def test_breakfast(self, generic_meals):
        """Test if the breakfast has correctly generated."""
        breakfast = generic_meals["breakfast"]
        assert "MILK" in breakfast.param_list

    def test_light_meal(self, generic_meals):
        """Test if the light_meal has correctly generated."""
        light_meal = generic_meals["light_meal"]
        assert "BEEF" in light_meal.param_list
        assert "CUCUMBER" in light_meal.param_list
        assert "MUSHROOMS" not in light_meal.param_list
        assert "VINEGAR" not in light_meal.param_list
        assert "EGG" not in light_meal.param_list
        assert "SALT" not in light_meal.param_list
        assert "GRAVY" not in light_meal.param_list

    def test_spicy_meal(self, generic_meals):
        """Test if the spicy_meal has correctly generated."""
        spicy_meal = generic_meals["spicy_meal"]
        assert "BEEF" in spicy_meal.param_list
        assert "CHILLI" in spicy_meal.param_list
        assert "EGG" not in spicy_meal.param_list

    def test_full_meal(self, generic_meals):
        """Test if the full_meal has correctly generated."""
        full_meal = generic_meals["full_meal"]
        assert "BEEF" in full_meal.param_list
        assert "CHILLI" not in full_meal.param_list
        assert "EGG" in full_meal.param_list
        assert "PISTACHIO" not in full_meal.param_list

    def test_christmass_meal(self, generic_meals):
        """Test if the christmass_meal has correctly generated."""
        christmass_meal = generic_meals["christmass_at_grandmas"]
        assert christmass_meal.param_list["BEEF"].value == 5

    def test_dangerous_combinations(self, generic_meals):
        """Test if the dangerous_combinations has correctly generated."""
        dangerous_combinations = generic_meals["dangerous_combinations"]
        assert "MILK" in dangerous_combinations.param_list
        assert "COFFEE" in dangerous_combinations.param_list
