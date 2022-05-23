"""Command-line interface."""
import cProfile
from pstats import Stats
from typing import Optional

import click

from ._helpers import Formats
from ._helpers import Logger
from .build import build_helper
from .compare import compare_helper

##############
# UI functions
##############


@click.group()
@click.option("--debug", is_flag=True, help="Generate log file.")
def cli(debug: bool) -> None:
    """Main CLI entry point."""
    Logger().debug = debug


@click.command()
@click.argument("file_1", type=click.Path(exists=True))
@click.argument("file_2", type=click.Path(exists=True))
@click.option(
    "-i",
    "--input_folder",
    default=None,
    type=click.Path(exists=True),
    help="Specify the folder from which to read configurations and parameters.",
)
@click.option(
    "-s",
    "--supress-calibration",
    "nocal",
    is_flag=True,
    default=False,
    help="Dont compare calibration parameters.",
)
@click.option(
    "-u",
    "--supress-user-defined",
    "nouser",
    is_flag=True,
    default=False,
    help="Dont compare user-selectable parameters.",
)
@click.option(
    "-c",
    "--component",
    default=None,
    type=int,
    help="Pass a specific component to compare",
)
def compare(file_1, file_2, input_folder, nocal, nouser, component):
    """Compare command."""
    s = compare_helper(file_1, file_2, input_folder, nocal, nouser, component)
    print(s)


@click.command()
@click.option(
    "-o",
    "--output_folder",
    default=None,
    type=click.Path(exists=False),
    help="Specify the output folder.",
)
@click.option(
    "-c",
    "--configuration",
    "config",
    default=None,
    type=str,
    help="Specify a single configuration to build.",
)
@click.option(
    "-f",
    "--format",
    default=Formats.px4.value,
    type=click.Choice([format.value for format in Formats], case_sensitive=False),
    help="Select autopilot format. PX4 parameters | PX4 airframe file | Ardupilot parameters",
)
@click.option(
    "-i",
    "--input_folder",
    default=None,
    type=click.Path(exists=True),
    help="Specify the folder from which to read configurations and parameters.",
)
@click.option(
    "-d",
    "--default_parameters",
    default=None,
    type=click.Path(exists=True),
    help="Specify the default parameters file to apply to all recipes.",
)
def build(
    config: str,
    format: str,
    input_folder: Optional[str],
    default_parameters: str,
    output_folder: str,
) -> None:
    """Build command."""
    build_helper(
        config, Formats[format], input_folder, default_parameters, output_folder
    )


cli.add_command(compare)
cli.add_command(build)


if __name__ == "__main__":
    profile = False
    if profile:
        with cProfile.Profile() as pr:
            cli(prog_name="parsect")

        with open("profiling_stats.txt", "w+") as stream:
            stats = Stats(pr, stream=stream)
            stats.strip_dirs()
            stats.sort_stats("time")
            stats.dump_stats(".prof_stats")
            stats.print_stats()
    else:
        cli(prog_name="parasect")