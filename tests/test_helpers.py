"""Test cases for the private _helpers module."""
import os
import pathlib

import pydantic
import pytest

from .utils import (  # noqa: F401 # setup_generic is used by pytest as string
    fixture_setup_generic,
)
from .utils import setup_logger  # noqa: F401 # setup_logger is an autouse fixture
from .utils import setup_px4  # noqa: F401 # setup_px4 is used by pytest as string
from parasect import _helpers


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
        log_file = pathlib.Path("./parasect.log")
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
        custom_path = "."
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
        _helpers.ConfigPaths().CUSTOM_PATH = (
            "~/idontexist"  # Unset custom paths to activate environment variable
        )
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
        custom_path = "."
        _helpers.ConfigPaths().DEFAULT_PARAMS_PATH = custom_path
        assert _helpers.ConfigPaths().default_parameters == custom_path

    def test_no_parameters(self):
        """Ensure it is possbile not to have set any default parameters path."""
        del os.environ["PARASECT_DEFAULTS"]
        _helpers.ConfigPaths().DEFAULT_PARAMS_PATH = None
        assert _helpers.ConfigPaths().default_parameters is None


@pytest.mark.usefixtures("setup_generic")
class TestMealMenuModel:
    """Testing the MealMenuModel class."""

    def test_bad_dish(self):
        """Test if a MealMenu asks for a non-existing dish."""
        bad_dish = {"meal_1": {"dish_1": None, "non_existing_dish": None}}
        with pytest.raises(pydantic.ValidationError):
            _helpers.MealMenuModel.parse_obj(bad_dish)


@pytest.mark.usefixtures("setup_generic")
class TestParameterGeneric:
    """Test Parameter-related functionality."""

    def test_wrong_type(self):
        """Verify the correct error is raised when a wrong parameter type is requested."""
        with pytest.raises(ValueError):
            _helpers.get_param_from_str("1", "0")

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
