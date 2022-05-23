"""Test cases for the __main__ module."""
import os
from os import path

import pytest
from click.testing import CliRunner

import parasect
from parasect import __main__


PX4_ASSETS_PATH = path.join(path.dirname(path.abspath(__file__)), "assets", "px4")
PX4_DEFAULT_PARAMS_XML = path.join(PX4_ASSETS_PATH, "parameters_3fe4c6e.xml")
PX4_JMAVSIM_PARAMS = path.join(PX4_ASSETS_PATH, "default_jmavsim_3fe4c6e.params")
PX4_GAZEBO_PARAMS = path.join(PX4_ASSETS_PATH, "default_gazebo_3fe4c6e.params")
PX4_INPUT_FOLDER = path.join(PX4_ASSETS_PATH, "menu")


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.cli)
    assert result.exit_code == 0


class TestLogging:
    """Test logging functionality."""

    def test_debug_file(self, runner: CliRunner) -> None:
        """Ensure a log file is generated upon demand."""
        with runner.isolated_filesystem():
            _ = runner.invoke(
                __main__.cli,
                ["--debug", "compare", PX4_JMAVSIM_PARAMS, PX4_GAZEBO_PARAMS],
            )
            log_path = path.join(os.getcwd(), "parasect.log")
            assert os.path.isfile(log_path)

    def test_no_debug(self, runner: CliRunner) -> None:
        """Ensure a log file is not generated in non-debug mode."""
        with runner.isolated_filesystem():
            _ = runner.invoke(
                __main__.cli,
                ["compare", PX4_JMAVSIM_PARAMS, PX4_GAZEBO_PARAMS],
            )
            log_path = path.join(os.getcwd(), "parasect.log")
            assert not os.path.isfile(log_path)


class TestCompare:
    """Test the compare command."""

    def test_compare_helper(self) -> None:
        """Make sure the compare_helper API generates the correct number of lines."""
        num_exp_lines = 5 + 1 + 3 - 1
        output_str = parasect.compare(
            file_1=PX4_JMAVSIM_PARAMS,
            file_2=PX4_GAZEBO_PARAMS,
            input_folder=None,
            nocal=False,
            nouser=False,
            component=None,
        )
        assert output_str.count("\n") == num_exp_lines

    def test_compare_cli(self, runner: CliRunner) -> None:
        """Make sure only one parameter differs."""
        num_exp_lines = 5 + 1 + 3
        result = runner.invoke(
            __main__.cli, ["compare", PX4_JMAVSIM_PARAMS, PX4_GAZEBO_PARAMS]
        )
        assert len(result.output.splitlines()) == num_exp_lines


class TestBuild:
    """Test the build command."""

    def test_build_helper(self, runner: CliRunner) -> None:
        """Make sure the build_helper API generates the output folder."""
        with runner.isolated_filesystem():
            parasect.build(
                meal_ordered=None,
                format=parasect._helpers.Formats.px4af,
                input_folder=PX4_INPUT_FOLDER,
                default_params=PX4_DEFAULT_PARAMS_XML,
                output_folder="output_folder",
            )
            log_path = path.join(os.getcwd(), "output_folder", "1_light_meal")
            print(os.listdir(path.join(os.getcwd())))
            # assert False
            assert os.path.isfile(log_path)

    def test_build(self, runner: CliRunner) -> None:
        """Make sure the full command works."""
        with runner.isolated_filesystem():
            _ = runner.invoke(
                __main__.cli,
                [
                    "build",
                    "-o",
                    "output_folder",
                    "-f",
                    "px4af",
                    "-i",
                    PX4_INPUT_FOLDER,
                    "-d",
                    PX4_DEFAULT_PARAMS_XML,
                ],
            )
            log_path = path.join(os.getcwd(), "output_folder", "1_light_meal")
            assert os.path.isfile(log_path)
