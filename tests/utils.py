"""Pytest functions for the tests collection."""
import os
from os import path

import pytest

import parasect

PX4_ASSETS_PATH = path.join(path.dirname(path.abspath(__file__)), "assets", "px4")
PX4_DEFAULT_PARAMS_XML = path.join(PX4_ASSETS_PATH, "parameters_3fe4c6e.xml")
PX4_JMAVSIM_PARAMS = path.join(PX4_ASSETS_PATH, "default_jmavsim_3fe4c6e.params")
PX4_GAZEBO_PARAMS = path.join(PX4_ASSETS_PATH, "default_gazebo_3fe4c6e.params")
PX4_INPUT_FOLDER = path.join(PX4_ASSETS_PATH, "menu")


@pytest.fixture(scope="function", autouse=True)
def setup_paths():
    """Set up the parasect paths and logger object."""
    os.environ["PARASECT_PATH"] = PX4_INPUT_FOLDER
    os.environ["PARASECT_DEFAULTS"] = PX4_DEFAULT_PARAMS_XML

    parasect._helpers.ConfigPaths().clear()
    parasect._helpers.Logger().clear()
