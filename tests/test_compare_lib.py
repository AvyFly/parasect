"""Test cases for the private build_lib module."""
from typing import Optional, List, Tuple

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
from parasect._helpers import Parameter, ParameterList
from parasect import build_lib
from parasect import compare_lib


class TestGetVehiclesComparison:
    """Testing the Dish class."""

    def test_nocal(self, setup_px4):
        """Test if calibration is correctly removed."""
        list_1 = _helpers.read_params(utils.PX4_JMAVSIM_PARAMS)
        list_2 = _helpers.read_params(utils.PX4_ULOG_PARAMS_FILE)
        comparison = compare_lib.get_vehicles_comparison(
            list_1, list_2, nocal=True, noop=False
        )
        param_names = [
            param_pair[0].name for param_pair in comparison[0] if param_pair[0]
        ]
        calibration = build_lib.Calibration()
        cal_names = [name for name in param_names if name in calibration]
        assert len(cal_names) == 0

    def test_noop(self, setup_px4):
        """Test if calibration is correctly removed."""
        list_1 = _helpers.read_params(utils.PX4_JMAVSIM_PARAMS)
        list_2 = _helpers.read_params(utils.PX4_ULOG_PARAMS_FILE)
        comparison = compare_lib.get_vehicles_comparison(
            list_1, list_2, nocal=False, noop=True
        )
        param_names = [
            param_pair[0].name for param_pair in comparison[0] if param_pair[0]
        ]
        operator = build_lib.Operator()
        cal_names = [name for name in param_names if name in operator]
        assert len(cal_names) == 0

    def test_component(self):
        """Test the correctness of component filtering."""
        param_1 = Parameter("P1", 0)
        list_1 = ParameterList()
        list_1.add_param(param_1)
        param_2 = Parameter("P1", 1)
        list_2 = ParameterList()
        list_2.add_param(param_2)

        comparison = compare_lib.get_vehicles_comparison(
            list_1, list_2, nocal=False, noop=False, component=1
        )
        assert len(comparison[0]) == 1

        comparison = compare_lib.get_vehicles_comparison(
            list_1, list_2, nocal=False, noop=False, component=2
        )
        assert len(comparison) == 0


class TestCompareParameterLists:
    """Test the compare_parameter_lists function."""

    def test_id_test_1(self):
        """Test parameter only in first list but undesirable vid/cid."""
        param_1 = Parameter("P1", 0)
        list_1 = ParameterList()
        list_1.add_param(param_1)
        list_2 = ParameterList()

        comparison = compare_lib.compare_parameter_lists(list_1, list_2, vid=1, cid=2)
        assert len(comparison) == 0

    def test_id_test_2(self):
        """Test parameter only in second list but undesirable vid/cid."""
        list_1 = ParameterList()
        param_2 = Parameter("P1", 0)
        list_2 = ParameterList()
        list_2.add_param(param_2)

        comparison = compare_lib.compare_parameter_lists(list_1, list_2, vid=1, cid=2)
        assert len(comparison) == 0

    def test_id_test_3(self):
        """Test parameter in both lists but undesirable vid/cid."""
        param_1 = Parameter("P1", 0)
        list_1 = ParameterList()
        list_1.add_param(param_1)
        param_2 = Parameter("P1", 1)
        list_2 = ParameterList()
        list_2.add_param(param_2)

        comparison = compare_lib.compare_parameter_lists(list_1, list_2, vid=1, cid=2)
        assert len(comparison) == 0


@pytest.mark.parametrize("vid, cid, expected", [(None, None, True), (1, 1, False)])
def test_comparison_spec_1(vid, cid, expected):
    """Test the function comparison_spec_1."""
    assert compare_lib.comparison_spec_1(vid, cid) == expected


@pytest.mark.parametrize(
    "p1, p2, vid, cid, expected",
    [
        (Parameter(name="P1", value=0, vid=1, cid=2), None, 1, 1, False),
        (None, Parameter(name="P2", value=0, vid=1, cid=2), 1, 1, False),
        (
            Parameter(name="P1", value=0, vid=1, cid=1),
            Parameter(name="P2", value=0, vid=1, cid=1),
            1,
            1,
            False,
        ),
        (Parameter(name="P1", value=0, vid=1, cid=1), None, 1, 1, True),
        (None, Parameter(name="P2", value=0, vid=1, cid=1), 1, 1, True),
    ],
)
def test_comparison_spec_2(p1, p2, vid, cid, expected):
    """Test the function comparison_spec_1."""
    assert compare_lib.comparison_spec_2(p1, p2, vid, cid) == expected


class TestGetColumnLegnths:
    """Test the get_column_lengths function."""

    def test_1(self):
        """Test the case where param_1 == None."""
        param_list = [
            (None, Parameter("P", 0)),
            (None, Parameter("P1", 10)),
            (None, Parameter("Q", 1)),
        ]  # type: List[Tuple[Optional[Parameter], Optional[Parameter]]]
        c1, c2, c3 = compare_lib.get_column_lengths(param_list)
        assert c1 == 2
        assert c2 == 1
        assert c3 == 2

    def test_2(self):
        """Test the case where param_1 != None."""
        param_list = [
            (Parameter("P", 0), None),
            (Parameter("P1", 10), None),
            (Parameter("Q", 1), None),
        ]  # type: List[Tuple[Optional[Parameter], Optional[Parameter]]]
        c1, c2, c3 = compare_lib.get_column_lengths(param_list)
        assert c1 == 2
        assert c2 == 2
        assert c3 == 1


class TestGenerateComparisonStrings:
    """Test the generate_comparison_strings function."""

    def test_empty(self):
        """Test that an empty comparison list returns an empty string."""
        assert compare_lib.generate_comparison_strings([], [1, 2, 3]) == ""

    def test_ids_1(self):
        """Test that that the vids are picked from the first parameter of the first pair."""
        output = compare_lib.generate_comparison_strings(
            [(Parameter("P", 0), None)],
            [1, 2, 3],
        )

        lines = output.split("\n")
        assert lines[1] == "Component 1-1:"

    def test_ids_2(self):
        """Test that that the vids are picked from the second parameter of the first pair."""
        output = compare_lib.generate_comparison_strings(
            [(None, Parameter("P", 0))],
            [1, 2, 3],
        )

        lines = output.split("\n")
        assert lines[1] == "Component 1-1:"


class TestBuildComparisonString:
    """Test the build_comparison_string function."""

    def test_default_source_files(self):
        """Test that that None source files can be handled."""
        output = compare_lib.build_comparison_string(
            [[(None, Parameter("P", 0))]], None, None
        )
        lines = output.split("\n")
        assert lines[0] == "File comparison : List 1 | List 2"

    def test_names_length(self):
        """Test the case where the column lengths are bigger than the new contents.

        Test used for coverage reasons.
        """
        output = compare_lib.build_comparison_string(
            [
                [
                    (Parameter("P10", 20), Parameter("P10", 10)),
                    (Parameter("P", 2), Parameter("P", 1)),
                ]
            ],
            None,
            None,
        )
        lines = output.split("\n")
        assert lines[0] == "File comparison : List 1 | List 2"

    def test_values_length(self):
        """Test the case where the value column lengths are bigger than the file names.

        Test used for coverage reasons.
        """
        output = compare_lib.build_comparison_string(
            [
                [
                    (Parameter("P10", 20), Parameter("P10", 10)),
                    (Parameter("P", 2), Parameter("P", 1)),
                ]
            ],
            "1",
            "2",
        )
        lines = output.split("\n")
        assert lines[0] == "File comparison : 1  | 2 "


class TestCompareHelper:
    """Tests for the compare_helper function."""

    def test_input_folder(self, setup_generic):
        """Make sure the compare_helper API correctly overwrites the input folder path."""
        _ = compare_lib.compare_helper(
            file_1=str(utils.PX4_JMAVSIM_PARAMS),
            file_2=str(utils.PX4_GAZEBO_PARAMS),
            input_folder=str(utils.PX4_ASSETS_PATH),
            nocal=False,
            noop=False,
            component=None,
        )
        assert _helpers.ConfigPaths().path == utils.PX4_ASSETS_PATH
