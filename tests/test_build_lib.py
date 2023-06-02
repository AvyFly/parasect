"""Test cases for the private build_lib module."""
from pathlib import Path

import pytest

from .utils import (  # noqa: F401 # setup_ardupilot is used by pytest as string
    fixture_setup_ardupilot,
)
from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import (  # noqa: F401 # setup_px4 is used by pytest as string
    fixture_setup_px4,
)
from .utils import (  # noqa: F401 # setup_tests is used by pytest as string
    fixture_setup_tests,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from parasect import _helpers
from parasect import build_lib


@pytest.fixture
def build_meals():
    """Build the all generic meals."""
    return build_lib.build_meals()


@pytest.fixture
def build_dish_model():
    """Return a simple DishModel."""
    return _helpers.DishModel.parse_obj(
        {
            "common": None,
            "variants": {
                "var1": {
                    "variants": {"var2": {"common": {"ingredients": [["ING1", 1, ""]]}}}
                }
            },
        }
    )


class TestDish:
    """Testing the Dish class."""

    def test_empty_variant(self, build_dish_model):
        """Test that a variant with no common section is properly handled.

        Its sub-variants still exist in this test case.
        """
        model = build_dish_model
        dish = build_lib.Dish(model, "var1", "var2")
        assert "ING1" in dish

    def test_bad_variant(self, build_dish_model):
        """Verify that an exception is raised when asking for a non-existing variant."""
        model = build_dish_model
        with pytest.raises(
            KeyError,
            match="The variant var3 is not found in the parameter list of <class 'parasect.build_lib.Dish'>",
        ):
            build_lib.Dish(model, "var3")

    def test_bad_subvariant(self, build_dish_model):
        """Test that a non-existing subvariant raises a warning."""
        model = build_dish_model
        with pytest.raises(
            KeyError, match="The submodel var1/var3 is not found in the parameter list"
        ):
            build_lib.Dish(model, "var1", "var3")

    def test_empty_subvariant(self, build_dish_model):
        """Test that a recipe with empty subvariant returns empty."""
        model = _helpers.DishModel.parse_obj(
            {
                "common": None,
                "variants": {"var1": {"variants": {"var2": {"common": None}}}},
            }
        )
        dish = build_lib.Dish(model, "var1", "var2")
        assert len(dish.param_list) == 0
        assert len(dish.black_groups) == 0
        assert len(dish.black_params) == 0


@pytest.mark.usefixtures("setup_tests")
class TestDishTests:
    """Testing the Dish class with the Tests meal menu."""

    def test_sitl(self):
        """Test the sitl flag."""
        meal = build_lib.build_meals(["sitl_meal"])["sitl_meal"]
        assert meal.is_sitl

    def test_hitl(self):
        """Test the hitl flag."""
        meal = build_lib.build_meals(["hitl_meal"])["hitl_meal"]
        assert meal.is_hitl

    def test_no_subvariant(self):
        """Verify that requesting a subvariant with an empty subvariant list raises an error."""
        with pytest.raises(
            SyntaxError,
            match="Tried to request subvariant sar1 but no subvariants are specified.",
        ):
            build_lib.build_meals(["empty_subvariants"])["empty_subvariants"]


@pytest.mark.usefixtures("setup_generic")
class TestDishGeneric:
    """Testing the Dish class with the Generic meal menu."""

    def test_str_(self):
        """Test the __str__ dunder method."""
        dish_model = _helpers.get_dish(_helpers.ConfigPaths().custom_dishes, "fruit")
        dish = build_lib.Dish(dish_model, "single")
        dish_str = str(dish)
        apple_str = str(dish.param_list["APPLE"])
        assert dish_str == apple_str

    def test_len(self):
        """Test the __len__ dunder method."""
        dish_model = _helpers.get_dish(_helpers.ConfigPaths().custom_dishes, "fruit")
        dish = build_lib.Dish(dish_model, "single")
        assert len(dish) == 1

    def test_contains(self):
        """Test the __contains__ dunder method."""
        dish_model = _helpers.get_dish(
            _helpers.ConfigPaths().custom_dishes, "meat_and_potatoes"
        )
        dish = build_lib.Dish(dish_model)
        assert "BEEF" in dish.param_list
        param = _helpers.Parameter("BEEF", 100)
        assert param in dish.param_list
        assert "UNOBTAINIUM" not in dish.param_list

    def test_no_variant(self):
        """Test that a Dish without a variant can be parsed."""
        model = _helpers.DishModel.parse_obj(
            {"common": {"ingredients": [["ING1", 1, ""]]}, "variants": None}
        )
        dish = build_lib.Dish(
            model, "var1"
        )  # Ask for a varient even if it doesn't exist
        assert "ING1" in dish


class TestMeal:
    """Test the Meal class."""

    def test_contains(self, setup_generic, build_meals):
        """Test the __contains__ dunder method."""
        light_meal = build_meals["light_meal"]
        assert "BEEF" in light_meal.param_list
        param = _helpers.Parameter("BEEF", 100)
        assert param in light_meal.param_list
        assert "UNOBTAINIUM" not in light_meal

    def test_allergens(self, setup_px4, build_meals):
        """Make sure allergens defined in custom dishes are removed."""
        vtol_1 = build_meals["my_vtol_1"]
        assert "TC_A0_ID" not in vtol_1.param_list
        assert "ATT_ACC_COMP" not in vtol_1.param_list

    def test_floats(self, setup_generic, build_meals):
        """Make sure floats are correctly parsed from the recipe."""
        light_meal = build_meals["light_meal"]
        assert light_meal.param_list["OIL"].value == 0.5

    def test_floats_2(self, setup_px4, build_meals):
        """Make sure floats are correctly parsed from the recipe, when overwriting default values."""
        vtol_1 = build_meals["my_vtol_1"]
        assert (
            str(vtol_1.param_list["BAT1_V_EMPTY"]) == "BAT1_V_EMPTY     (F):\t3.300000"
        )
        assert vtol_1.param_list["BAT1_V_EMPTY"].value == 3.3

    def test_add_new(self, setup_px4, build_meals):
        """Make sure new parameters lookup the defaults for their type."""
        vtol_3 = build_meals["my_vtol_3"]
        assert vtol_3.param_list["SIH_IXX"].param_type == "FLOAT"

    def test_defaults_override(self, setup_ardupilot, build_meals):
        """Make sure that the defaults keyword can load a file.

        No defaults keyword will result in the PARASECT_DEFAULTS being used.
        """
        copter_1 = build_meals["my_copter_1"]
        assert copter_1.param_list["ARMING_CHECK"].value == 1

    def test_defaults_override_2(self, setup_ardupilot, build_meals):
        """Make sure that the defaults keyword can load a file.

        sitl_copter_defaults.parm in assets folder has ARMING_CHECK=1.
        """
        copter_1 = build_meals["my_copter_1"]
        assert copter_1.param_list["ARMING_CHECK"].value == 1

    def test_defaults_override_3(self, setup_ardupilot, build_meals):
        """Make sure that the defaults keyword can load a file.

        defaults.param in menu folder has ARMING_CHECK=0.
        """
        copter_2_apj = build_meals["my_copter_2_apj"]
        assert not ("ARMING_CHECK" in copter_2_apj)

    def test_defaults_override_4(self, setup_ardupilot, tmp_path):
        """Make sure that the defaults keyword can load a file.

        defaults overrides with absolute path get correctly resolved.
        """
        new_file = tmp_path / "my_defaults.param"
        new_fp = open(new_file, "w")
        new_fp.writelines(["ARMING_CHECK 2\n"])
        new_fp.close()

        meals_menu_dict = {
            "my_copter_2": {
                "defaults": f"{str(new_file)}",
                "battery": "my_copter_2",
                "tuning": None,
                "mission": None,
                "header": "my_copter_2",
                "remove_calibration": True,
                "remove_operator": True,
                "add_new": True,
            }
        }
        meals_menu = _helpers.MealMenuModel.parse_obj(meals_menu_dict)

        default_params_filepath = _helpers.ConfigPaths().default_parameters
        configs_path = _helpers.ConfigPaths().path
        my_copter_2 = build_lib.Meal(
            meals_menu, default_params_filepath, configs_path, "my_copter_2"
        )

        assert my_copter_2.param_list["ARMING_CHECK"].value == 2


class TestExport:
    """Testing the export functionalities."""

    def test_header(self, setup_generic, build_meals):
        """Test if the headers are generated correctly."""
        light_meal = build_meals["light_meal"]
        gen = light_meal.export_to_px4afv1()
        line1 = next(gen)
        assert line1.startswith("# Parameter file")

    def test_variant(self, setup_generic, build_meals):
        """Test if the variants are generated correctly."""
        full_meal = build_meals["full_meal"]
        gen = full_meal.export_to_px4afv1()
        lines = list(gen)
        assert lines[-1].startswith("Remember")

    def test_export_csv(self, setup_generic, build_meals):
        """Test if exports to CSV parameter format work."""
        meal = build_meals["light_meal"]
        gen = meal.export_to_csv()
        lines = list(gen)
        assert lines[1].startswith("# Parameter name, Parameter value")

    def test_export_px4(self, setup_px4, build_meals):
        """Test if exports to PX4 parameter format work."""
        vtol_1 = build_meals["my_vtol_1"]
        gen = vtol_1.export_to_px4()
        lines = list(gen)
        assert lines[0].startswith("# Onboard parameters")

    def test_export_px4afv1(self, setup_px4, build_meals):
        """Test if exports to legacy PX4 airframe format work as expected."""
        vtol_1 = build_meals["my_vtol_1"]
        gen = vtol_1.export_to_px4afv1()
        lines = list(gen)
        assert "param set " in lines[27]

    def test_export_px4afv2(self, setup_px4, build_meals):
        """Test if exports to new-style PX4 airframe file format work as expected."""
        vtol_1 = build_meals["my_vtol_1"]
        gen = vtol_1.export_to_px4afv2()
        lines = list(gen)
        assert "param set-default " in lines[27]

    def test_export_px4af_unsupported(self, setup_px4, build_meals):
        """Test exception when passing invalid PX4 airframe version."""
        vtol_1 = build_meals["my_vtol_1"]
        with pytest.raises(ValueError):
            gen = vtol_1.export_to_px4af(3)
            list(gen)

    def test_export_apm(self, setup_ardupilot, build_meals):
        """Test if exports to ardupilot parameter format work."""
        copter_1 = build_meals["my_copter_1"]
        gen = copter_1.export_to_apm()
        lines = list(gen)
        assert lines[0].startswith("# Ardupilot onboard parameters")

    def test_export(self, setup_px4, build_meals):
        """Test if the export method works as expected for the px4 format."""
        vtol_1 = build_meals["my_vtol_1"]
        vtol_1.apply_additions_px4()  # Invoke the aiframe file addition.
        gen = vtol_1.export_to_px4()
        lines1 = list(gen)
        lines2 = list(vtol_1.export(_helpers.Formats.px4))
        assert lines1 == lines2

    def test_export_2(self, setup_ardupilot, build_meals):
        """Test if the export method works as expected for the apm format."""
        my_copter_1 = build_meals["my_copter_1"]
        gen = my_copter_1.export_to_apm()
        lines1 = list(gen)
        lines2 = list(my_copter_1.export(_helpers.Formats.apm))
        assert lines1 == lines2


@pytest.mark.usefixtures("setup_generic")
class TestBuildFilename:
    """Test the build_filename function."""

    def test_csv(self, build_meals):
        """Test the csv format."""
        name = build_lib.build_filename(_helpers.Formats.csv, build_meals["light_meal"])
        assert Path(name).suffix == ".csv"

    def test_px4(self, build_meals):
        """Test the px4 format."""
        name = build_lib.build_filename(_helpers.Formats.px4, build_meals["light_meal"])
        assert Path(name).suffix == ".params"

    def test_px4_hitl(self, build_meals):
        """Test the px4afv2 hil format."""
        name = build_lib.build_filename(
            _helpers.Formats.px4afv2, build_meals["breakfast"]
        )
        assert Path(name).suffix == ".hil"

    def test_px4af(self, build_meals):
        """Test the px4 airframe format."""
        name = build_lib.build_filename(
            _helpers.Formats.px4afv1, build_meals["light_meal"]
        )
        assert name == "1_light_meal"


class TestConvertTtrToPath:
    """Test convert_str_to_path."""

    def test_none(self):
        """Test None input."""
        assert build_lib.convert_str_to_path(None) is None

    def test_str(self):
        """Test str input."""
        path = Path("my") / "home"
        result = build_lib.convert_str_to_path(str(path))
        assert isinstance(result, Path)
        assert result == path


class TestBuildHelper:
    """Test the build_helper function."""

    def test_single_meal(self, setup_px4, tmp_path):
        """Test if it is possible to generate only one meal."""
        path = tmp_path
        build_lib.build_helper(
            meal_ordered="my_vtol_1",
            format=_helpers.Formats.px4afv1,
            input_folder=str(_helpers.ConfigPaths().path),
            default_params=str(_helpers.ConfigPaths().default_parameters),
            output_folder=str(path),
        )
        assert (path / "1_my_vtol_1").is_file()
        assert len([file for file in path.iterdir()]) == 1

    def test_no_input(self, setup_px4, tmp_path):
        """Test if it is possible to not pass paths explicitly."""
        path = tmp_path
        build_lib.build_helper(
            meal_ordered="my_vtol_1",
            format=_helpers.Formats.px4afv1,
            input_folder=None,
            default_params=None,
            output_folder=str(path),
        )
        assert (path / "1_my_vtol_1").is_file()

    def test_csv(self, setup_generic, tmp_path):
        """Test exporting the Generic meals with the csv format.

        This invocation is also used by the documentation.
        """
        build_lib.build_helper(
            None,
            _helpers.Formats("csv"),
            str(_helpers.ConfigPaths().path),
            None,
            str(tmp_path),
        )
        meals_menu = _helpers.get_meals_menu(_helpers.ConfigPaths().meals)
        generated_meals = {gen_file.stem for gen_file in list(tmp_path.iterdir())}
        for meal in meals_menu.keys():
            assert meal in generated_meals
