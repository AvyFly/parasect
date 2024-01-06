"""Test cases for the private _helpers module."""
import os
from pathlib import Path

import pydantic
import pytest

from . import utils
from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import (  # noqa: F401 # setup_px4 is used by pytest as string
    fixture_setup_px4,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from parasect import _helpers
from parasect import build_lib


@pytest.fixture
def generic_meals():
    """Build the all generic meals."""
    return build_lib.build_meals()


class TestLogger:
    """Testing of the Logger class."""

    def test_constructor(self):
        """Test the class constructor."""
        _helpers.Logger().clear()
        assert _helpers.Logger() is not None

    def test_debug(self):
        """Test that the debug level is correctly stored."""
        _helpers.Logger().clear()
        tests = []
        logger_singleton = _helpers.Logger()
        tests.append(logger_singleton._debug is False)
        logger_singleton._debug = True
        logger_singleton = _helpers.Logger()
        tests.append(logger_singleton._debug is True)
        assert all(tests)

    def test_new_log_file(self):
        """Test if a new log file is indeed crated at the start of the program."""
        _helpers.Logger().clear()
        log_file = Path("./parasect.log")
        log_file.write_text("old line")
        _helpers.Logger(debug=True)
        logger = _helpers.get_logger()
        logger.debug("new line")
        assert log_file.read_text() == "parasect - DEBUG - new line\n"

    def test_clear(self, setup_generic):
        """Test the clear() method."""
        _ = _helpers.get_logger()
        assert not _helpers.Logger()._debug
        _helpers.Logger().clear()
        _helpers.Logger(debug=True)
        _ = _helpers.get_logger()
        assert _helpers.Logger()._debug
        _helpers.Logger().clear()
        assert not _helpers.Logger()._debug


@pytest.mark.usefixtures("setup_px4")
class TestConfigPathsPX4:
    """Testing of the ConfigPaths class."""

    def test_no_env_path(self):
        """Catch the correct fallback if PARASECT_PATH is unset."""
        del os.environ["PARASECT_PATH"]
        custom_path = Path(".")
        _helpers.ConfigPaths().CUSTOM_PATH = custom_path
        assert _helpers.ConfigPaths().path == custom_path

    def test_bad_env_path(self):
        """Raise the correct error if PARASECT_PATH is bad."""
        _helpers.ConfigPaths().CUSTOM_PATH = (
            None  # Unset custom paths to activate environment variable
        )
        os.environ["PARASECT_PATH"] = "~/idontexist"
        with pytest.raises(NotADirectoryError):
            _helpers.ConfigPaths().path

    def test_bad_custom_path(self):
        """Raise the correct error if CUSTOM_PATH is bad."""
        _helpers.ConfigPaths().CUSTOM_PATH = Path(
            "~/idontexist"
        )  # Unset custom paths to activate environment variable
        with pytest.raises(NotADirectoryError):
            _helpers.ConfigPaths().path

    def test_no_path(self):
        """Raise the correct error if no path is set."""
        del os.environ["PARASECT_PATH"]
        _helpers.ConfigPaths().CUSTOM_PATH = None  # Unset custom paths
        with pytest.raises(RuntimeError):
            _helpers.ConfigPaths().path

    def test_no_env_parameters(self):
        """Catch the correct fallback if PARASECT_DEFAULTS is unset."""
        del os.environ["PARASECT_DEFAULTS"]
        custom_path = Path(".")
        _helpers.ConfigPaths().DEFAULT_PARAMS_PATH = custom_path
        assert _helpers.ConfigPaths().default_parameters == custom_path

    def test_no_parameters(self):
        """Ensure it is possbile not to have set any default parameters path."""
        del os.environ["PARASECT_DEFAULTS"]
        _helpers.ConfigPaths().DEFAULT_PARAMS_PATH = None
        assert _helpers.ConfigPaths().default_parameters is None


def test_check_type():
    """Verify that check_type raises an error."""
    with pytest.raises(TypeError, match="Value of var=1 should be <class 'str'>."):
        _helpers.check_type("var", 1, str)


@pytest.mark.usefixtures("setup_generic")
class TestMealMenuModel:
    """Testing the MealMenuModel class."""

    def test_bad_dish(self):
        """Test if a MealMenu asks for a non-existing dish."""
        bad_dish = {"meal_1": {"dish_1": None, "non_existing_dish": None}}
        with pytest.raises(pydantic.ValidationError):
            _helpers.MealMenuModel.model_validate(bad_dish)

    def test_bad_parent(self):
        """Verify that a non-string parent raises an error."""
        bad_dish = {"bad_parent": {"parent": 1, "dish_1": None}}
        with pytest.raises(pydantic.ValidationError):
            _helpers.MealMenuModel.model_validate(bad_dish)

    def test_bad_header(self):
        """Verify that a non-string parent raises an error."""
        bad_dish = {"bad_header": {"header": 1, "dish_1": None}}
        with pytest.raises(pydantic.ValidationError):
            _helpers.MealMenuModel.model_validate(bad_dish)

    def test_bad_footer(self):
        """Verify that a non-string footer raises an error."""
        bad_dish = {"bad_footer": {"footer": 1, "dish_1": None}}
        with pytest.raises(pydantic.ValidationError):
            _helpers.MealMenuModel.model_validate(bad_dish)


@pytest.mark.usefixtures("setup_generic")
class TestParameterGeneric:
    """Test Parameter-related functionality."""

    def test_wrong_type(self):
        """Verify the correct error is raised when a wrong parameter type is requested."""
        with pytest.raises(TypeError):
            _helpers.cast_param_value("1", "0")

    def test_wrong_type_2(self):
        """Verify the correct error is raised when a None parameter type."""
        with pytest.raises(TypeError):
            _helpers.cast_param_value("1", None)

    def test_get_pretty_value_int_notype(self):
        """Verify that integer values are correctly deduced."""
        param = _helpers.Parameter("TEMP", 1)
        assert param.get_pretty_value() == "1"

    def test_get_pretty_value_float_float(self):
        """Verify that float values typed as float have their trailling zeros deleted."""
        param = _helpers.Parameter("TEMP", 1.10)
        param.param_type = "FLOAT"
        assert param.get_pretty_value() == "1.1"

    def test_get_pretty_value_float_float_2(self):
        """Verify that float values typed as float at least one decimal."""
        param = _helpers.Parameter("TEMP", 1)
        param.param_type = "FLOAT"
        assert param.get_pretty_value() == "1.0"

    def test_int_type(self):
        """Test that in an INT32 parameter a float is cast into an int."""
        param = _helpers.Parameter("TEMP", 1, "INT32")
        param.value = 2.2
        assert param.get_pretty_value() == "2"

    def test_int_type_2(self):
        """Test that in a FLOAT parameter an int is cast into an float."""
        param = _helpers.Parameter("TEMP", 1, "FLOAT")
        param.value = 2
        assert param.get_pretty_value() == "2.0"


class TestParameterBuilders:
    """Test the parameter builders."""

    def test_from_iter(self):
        """Test building parameter from iterator."""
        iterator = ("NAME", 42, "Because I'm Batman!")
        param = _helpers.build_param_from_iter(iterator)
        assert param.name == "NAME"
        assert param.value == pytest.approx(42)
        assert (
            "Batman" in param.reasoning  # type: ignore # reasoning is definitely not None
        )
        assert param.readonly is False

        iterator = ("NAME", 42, "Because I'm Batman! @READONLY")
        param = _helpers.build_param_from_iter(iterator)
        assert param.readonly is True


@pytest.mark.usefixtures("setup_generic")
class TestParameterList:
    """Test the ParameterList class."""

    def test_copy_constructor(self, generic_meals):
        """Test the copy constructor."""
        light_meal = generic_meals["light_meal"]
        new_parameter_list = _helpers.ParameterList(light_meal.param_list)
        assert light_meal.param_list.keys() == new_parameter_list.keys()
        assert not (light_meal.param_list.params is new_parameter_list.params)

    def test_subtract(self, generic_meals):
        """Test the __sub__ operation."""
        spicy_meal = generic_meals["spicy_meal"]
        light_meal = generic_meals["light_meal"]
        params_diff = spicy_meal.param_list - light_meal.param_list
        assert len(params_diff) == 2
        assert "CHILLI" in params_diff
        assert "JALLAPENOS" in params_diff

    def test_str(self, generic_meals):
        """Test the __str__ operation."""
        light_meal = generic_meals["light_meal"]
        s = light_meal.__str__()
        assert s.count("\n") == 4
        assert s[0:4] == "BEEF"

    def test_add_illegal(self, generic_meals):
        """Test the add_param operation when doing illegal edits."""
        light_meal = generic_meals["light_meal"]
        param = _helpers.Parameter("UNOBTAINIUM", -1)
        with pytest.raises(KeyError):
            light_meal.param_list.add_param(param, safe=True)
        param = _helpers.Parameter("BEEF", 100)
        with pytest.raises(KeyError):
            light_meal.param_list.add_param(param, overwrite=False)

    def test_remove_illegal(self, generic_meals):
        """Test the remove_param operation when doing illegal edits."""
        light_meal = generic_meals["light_meal"]
        with pytest.raises(KeyError):
            param = _helpers.Parameter("UNOBTAINIUM", 0)
            light_meal.param_list.remove_param(param)

    def test_contains(self, generic_meals):
        """Test the __contains__ dunder method."""
        light_meal = generic_meals["light_meal"]
        assert "BEEF" in light_meal.param_list
        param = _helpers.Parameter("BEEF", 100)
        assert param in light_meal.param_list
        assert "UNOBTAINIUM" not in light_meal.param_list

    def test_param_cid(self):
        """Test the correct accessing with cid."""
        param_list = _helpers.ParameterList()
        p1 = _helpers.Parameter(name="P1", value=1, cid=10)
        p2 = _helpers.Parameter(name="P2", value=2, cid=20)
        param_list.add_param(p1, safe=False)
        param_list.add_param(p2, safe=False)
        p1_b = param_list["P1", 10]
        p2_b = param_list["P2", 20]
        assert p1_b.cid == 10
        assert p2_b.cid == 20


class TestPX4ParamReaders:
    """Test the various PX4 parameter file decoders."""

    def test_xml(self, setup_px4, tmp_path):  # noqa: F811 # setup_px4 is a fixture
        """Test reading from an XML parameters definition file."""
        # Add a parameter outside of a group
        new_entry = [
            '<parameter name="UNGROUPED_PARAM" default="-1" type="INT32">\n',
            "<short_desc>A parameter outside of a group</short_desc>\n",
            "<long_desc>Added for testing purposes.</long_desc>\n",
            "<min>-1</min>\n",
            "<max>1</max>\n",
            "</parameter>\n",
        ]
        path = tmp_path
        new_file = path / "edited.params"
        old_fp = open(utils.PX4_DEFAULT_PARAMS_XML)
        old_lines = old_fp.readlines()
        new_fp = open(new_file, "a")
        new_fp.writelines(old_lines[0:-1])  # Stop right before the </parameters> tag
        new_fp.writelines(new_entry)
        new_fp.writelines(["</parameters>"])
        new_fp.close()

        parameter_list = _helpers.read_params(new_file)
        # Test if the parameter exists, is in the correct group and has the correct type and value
        assert parameter_list["ASPD_BETA_NOISE"].value == pytest.approx(0.3)
        assert parameter_list["ASPD_BETA_NOISE"].group == "Airspeed Validator"
        assert parameter_list["ASPD_BETA_NOISE"].param_type == "FLOAT"
        assert "UNGROUPED_PARAM" in parameter_list

    def test_qgc(self, tmp_path):
        """Test reading from a parameter file extracted from a .ulg via ulog_params."""
        path = tmp_path
        new_file = path / "edited.params"
        old_fp = open(utils.PX4_GAZEBO_PARAMS)
        old_lines = old_fp.readlines()
        new_fp = open(new_file, "a")
        new_fp.writelines(old_lines[0:50])
        new_fp.writelines(["\n"])  # Insert a blank line
        new_fp.writelines(old_lines[50:-1])  # Write the rest of the lines
        new_fp.close()

        parameter_list = _helpers.read_params(new_file)
        assert parameter_list["BAT_CRIT_THR"].value == pytest.approx(0.07)

    def test_qgc_2(self, tmp_path):
        """Verify that a GQC file without a string in the 3rd place will raise an error."""
        path = tmp_path
        new_file = path / "edited.params"
        old_fp = open(utils.PX4_GAZEBO_PARAMS)
        old_lines = old_fp.readlines()
        new_fp = open(new_file, "w")
        new_fp.writelines(old_lines[0:50])
        new_fp.writelines(["1	1	42	1.000000000000000000	9\n"])  # Insert a wrong line
        new_fp.writelines(old_lines[50:-1])  # Write the rest of the lines
        new_fp.close()

        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params_qgc(new_file)
        assert (
            str(exc_info.value)
            == "File is not of QGC format:\nThird element must be a parameter name string"
        )

    def test_qgc_3(self, tmp_path):
        """Verify that a GQC file with an invalid parameter type enum raises an error."""
        path = tmp_path
        new_file = path / "edited.params"
        new_fp = open(new_file, "w")
        new_fp.writelines(["1	1	MY_PARAM	1.0	42\n"])  # Insert a wrong line
        new_fp.close()

        with pytest.raises(ValueError) as exc_info:
            _helpers.read_params_qgc(new_file)
        assert str(exc_info.value) == "Unknown parameter type: 42"

    def test_qgc_empty(self, tmp_path):
        """Verify that an exception is raised from empty input."""
        path = tmp_path
        new_file = path / "edited.params"
        with open(new_file, "w") as new_fp:
            new_fp.writelines(
                ["#1	1	ASPD_SCALE_1	1.000000000000000000	0\n"]
            )  # Insert a commented-out line
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params_qgc(new_file)
        assert (
            str(exc_info.value)
            == "File is not of QGC format:\nCould not extract any parameter from file."
        )

    def test_qgc_cid_shadowing(self, tmp_path):
        """Verify that the same parameter in a different component doesn't shadow the former."""
        new_entry = ["1	2	ASPD_SCALE_1	2.0	9"]
        path = tmp_path
        new_file = path / "edited.params"
        old_fp = open(utils.PX4_GAZEBO_PARAMS)
        old_lines = old_fp.readlines()
        new_fp = open(new_file, "a")
        new_fp.writelines(old_lines[0:-1])  # Stop right before the </parameters> tag
        new_fp.writelines(new_entry)
        new_fp.close()

        parameter_list = _helpers.read_params(new_file)
        # Test if the parameter exists, is in the correct group and has the correct type and value
        assert parameter_list["ASPD_SCALE_1"].value == pytest.approx(1)

    def test_ulog_param(self):
        """Test reading from a parameter file extracted from a .ulg via ulog_params."""
        parameter_list = _helpers.read_params(utils.PX4_ULOG_PARAMS_FILE)
        assert parameter_list["BAT1_A_PER_V"].value == pytest.approx(36.364)

    def test_ulog_param_2(self, tmp_path):
        """Verify that a ulog file with a number in the first position raises an exception."""
        path = tmp_path
        new_file = path / "edited.params"
        old_fp = open(utils.PX4_ULOG_PARAMS_FILE)
        old_lines = old_fp.readlines()
        new_fp = open(new_file, "w")
        new_fp.writelines(old_lines[0:50])
        new_fp.writelines(["42, 0\n"])  # Insert a wrong line
        new_fp.writelines(old_lines[50:-1])  # Write the rest of the lines
        new_fp.close()
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params_ulog_param(new_file)
        assert (
            str(exc_info.value)
            == "File is not of ulog format:\nFirst row element must be a parameter name string"
        )

    def test_ulog_param_empty(self, tmp_path):
        """Verify that an exception is raised from empty input."""
        path = tmp_path
        new_file = path / "edited.params"
        with open(new_file, "w") as new_fp:
            new_fp.writelines([])  # Insert empty file
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params_ulog_param(new_file)
        print(exc_info.value)
        assert (
            str(exc_info.value)
            == "File is not of ulog format:\nCould not extract any parameter from file."
        )

    def test_unknown_protocol(self, tmp_path):
        """Verify an exception is thrown if the file protocol is unknown."""
        path = tmp_path
        new_file = path / "wrong.params"
        content = ["Bad line1\n", "Plus some, numbers\n"]
        new_fp = open(new_file, "w")
        new_fp.writelines(content)
        new_fp.close()
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params(new_file)
        assert str(exc_info.value) == "Could not recognize log protocol."


class TestArdupilotParamReaders:
    """Test the various Ardupilot parameter file decoders."""

    def test_mavproxy(self):
        """Test reading from a parameter file saved by MAVProxy."""
        parameter_list = _helpers.read_params(utils.ARDUPILOT_DEFAULT_PARAMS)
        assert parameter_list["ARMING_ACCTHRESH"].value == pytest.approx(0.75)

    def test_split_row(self):
        """Test that a number as the first element throws an error."""
        row = "42\t42"
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.split_mavproxy_row(row)
        assert (
            str(exc_info.value) == "First row element must be a parameter name string."
        )

    def test_split_row_2(self):
        """Ensure all 3 elements are decoded."""
        row = "NAME 42 Batman"
        result = _helpers.split_mavproxy_row(row)
        expected = ("NAME", "42", "Batman")
        assert all([a == b for a, b in zip(result, expected)])  # noqa: B905
        # Disabling qa because 'strict' keyword not supported before 3.10

    def test_parse_failure(self):
        """Ensure an exception is thrown if parsing fails."""
        with pytest.raises(SyntaxError) as exc_info:
            _helpers.read_params_mavproxy(utils.PX4_GAZEBO_PARAMS)
        assert "File is not of mavproxy format" in str(exc_info.value)
