"""Command-line interface."""
import cProfile
from importlib.metadata import version
from pstats import Stats
from typing import Optional

import click

from parasect._helpers import Formats
from parasect._helpers import Logger
from parasect.build_lib import build_helper
from parasect.compare_lib import compare_helper

##############
# UI functions
##############


@click.group()
@click.option("--debug", is_flag=True, help="Generate log file.")
@click.version_option(version("parasect"))
def cli(debug: bool) -> None:
    """Main CLI entry point."""
    Logger(debug=debug)


@click.command()
@click.argument("file_1", type=click.Path(exists=True))
@click.argument("file_2", type=click.Path(exists=True))
@click.option(
    "-i",
    "--input_folder",
    default=None,
    type=click.Path(exists=True),
    help="The directory where the Meals Menu is created, containing at least the"
    + " *calibration* and *operator* staple dishes. Necessary when the *nocal* and *noop* options are set.",
)
@click.option(
    "-s",
    "--supress-calibration",
    "nocal",
    is_flag=True,
    default=False,
    help="Don't compare calibration parameters.",
)
@click.option(
    "-u",
    "--supress-operator-defined",
    "noop",
    is_flag=True,
    default=False,
    help="Don't compare operator-selectable parameters.",
)
@click.option(
    "-c",
    "--component",
    default=None,
    type=int,
    help="Compare the parameters of a specific component. Refers to MAVLink-type Component IDs.",
)
def compare(
    file_1: str,
    file_2: str,
    input_folder: Optional[str],
    nocal: bool,
    noop: bool,
    component: int,
) -> None:
    """Compare command."""
    s = compare_helper(file_1, file_2, input_folder, nocal, noop, component)
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
    help="Specify a single Meal to build.",
)
@click.option(
    "-f",
    "--format",
    default=Formats.px4.value,
    type=click.Choice([format.value for format in Formats], case_sensitive=False),
    help="Select autopilot format. Read the documentation of :class:`~parasect.Formats` for more information.",
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
    help="Specify the default parameters file to apply to all Meals.",
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
        config,
        Formats[format],
        input_folder,
        default_parameters,
        output_folder,
    )


cli.add_command(compare)
cli.add_command(build)


if __name__ == "__main__":  # pragma: no cover
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
