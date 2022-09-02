"""Pytest functions for the tests collection."""
import os
from os import path
from pathlib import Path

import pytest

import parasect

GENERIC_ASSETS_PATH = Path(path.dirname(path.abspath(__file__))) / "assets" / "generic"
GENERIC_INPUT_FOLDER = Path(GENERIC_ASSETS_PATH) / "menu"

TESTS_ASSETS_PATH = Path(path.dirname(path.abspath(__file__))) / "assets" / "testing"
TESTS_INPUT_FOLDER = Path(TESTS_ASSETS_PATH) / "menu"

PX4_ASSETS_PATH = Path(path.dirname(path.abspath(__file__))) / "assets" / "px4"
PX4_DEFAULT_PARAMS_XML = Path(PX4_ASSETS_PATH) / "parameters_3fe4c6e.xml"
PX4_JMAVSIM_PARAMS = Path(PX4_ASSETS_PATH) / "default_jmavsim_3fe4c6e.params"
PX4_GAZEBO_PARAMS = Path(PX4_ASSETS_PATH) / "default_gazebo_3fe4c6e.params"
PX4_INPUT_FOLDER = Path(PX4_ASSETS_PATH) / "menu"
PX4_ULOG_PARAMS_FILE = PX4_ASSETS_PATH / "6fcfa754-186b-41ae-90a4-8de386f712c3.params"


@pytest.fixture(name="setup_generic")
def fixture_setup_generic():
    """Set up the parasect paths for generic testing and demonstration."""
    os.environ["PARASECT_PATH"] = str(GENERIC_INPUT_FOLDER)
    if "PARASECT_DEFAULTS" in os.environ.keys():
        del os.environ["PARASECT_DEFAULTS"]

    parasect._helpers.ConfigPaths().clear()


@pytest.fixture(name="setup_tests")
def fixture_setup_tests():
    """Set up the parasect paths for corner-case testing."""
    os.environ["PARASECT_PATH"] = str(TESTS_INPUT_FOLDER)
    if "PARASECT_DEFAULTS" in os.environ.keys():
        del os.environ["PARASECT_DEFAULTS"]

    parasect._helpers.ConfigPaths().clear()


@pytest.fixture(name="setup_px4")
def fixture_setup_px4():
    """Set up the parasect paths for PX4 testing."""
    os.environ["PARASECT_PATH"] = str(PX4_INPUT_FOLDER)
    os.environ["PARASECT_DEFAULTS"] = str(PX4_DEFAULT_PARAMS_XML)

    parasect._helpers.ConfigPaths().clear()


@pytest.fixture(scope="function", autouse=True)
def setup_logger():
    """Set up the logger object."""
    parasect._helpers.Logger().clear()
