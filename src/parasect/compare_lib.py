"""Module providing the comparison of parameter sets."""
import itertools as it
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from ._helpers import ConfigPaths
from ._helpers import get_logger
from ._helpers import read_params
from .build_lib import Calibration
from .build_lib import Operator
from .build_lib import Parameter
from .build_lib import ParameterList


PARAM_EPS_PCT = 0.006  # This value allow a displayed precision of 3 digits
EPS = 1e-6
PARAM_MAX_LEN = 15  # According to PX4 documentation


def get_vehicles_comparison(
    param_list_1: ParameterList,
    param_list_2: ParameterList,
    nocal: bool,
    noop: bool,
    component: Optional[int] = None,
) -> List:
    """Top-level comparison function.

    Returns a list of comparison results
    Each list item refers to a unique (vehicle-id, component-id) tuple
    """
    # Collect vehicle IDs and component IDs
    id_dict = collect_vid_cid(param_list_1, param_list_2)

    # Remove calibration parameters from both lists
    if nocal:
        param_list_1 -= Calibration().param_list
        param_list_2 -= Calibration().param_list

    # Remove user parameters from both lists
    if noop:
        param_list_1 -= Operator().param_list
        param_list_2 -= Operator().param_list

    # Generate comparison results
    comparison_results = list()

    # Iterate over all VIDs
    for vid, cids in id_dict.items():
        # Iterate over all CIDs:
        for cid in cids:
            # Filter for the desired component
            if component is not None and cid != component:
                continue
            result = compare_parameter_lists(param_list_1, param_list_2, vid, cid)
            comparison_results.append(result)

    return comparison_results


def collect_vid_cid(
    param_list_1: ParameterList, param_list_2: ParameterList
) -> Dict[int, Set[int]]:
    """Collect vehicle IDs and component IDs.

    Args:
        param_list_1: The first ParameterList to parse for VIDs and CIDs.
        param_list_2: The second ParameterList to parse for VIDs and CIDs.

    Returns:
        A Dict where the keys are the VIDs found. The value of each key is the
        CIDs found in every VID.
        The result will never be an empty Dict because the Parameter object is
        initialized with VID=1 and CID=1.
    """
    id_dict = dict()  # type: Dict[int, Set[int]]
    for param in it.chain(param_list_1, param_list_2):
        # If this VID is new, create it
        if param.vid not in id_dict.keys():
            id_dict[param.vid] = {param.cid}
        # Otherwise append to it
        else:
            id_dict[param.vid].add(param.cid)

    return id_dict


def compare_parameter_lists(
    param_list_1: ParameterList,
    param_list_2: ParameterList,
    vid: Optional[int],
    cid: Optional[int],
) -> List[Tuple[Optional[Parameter], Optional[Parameter]]]:
    """Compare two parameter lists, potentially filtering with vid and cid.

    Returns a list of tuples. Each tuple contains the old parameter and the new parameter.
    None is inserted if parameter does not exist
    """
    param_names_1 = param_list_1.keys()
    param_names_2 = param_list_2.keys()
    all_param_names = sorted(set(param_names_1) | set(param_names_2))

    comparison_list = list()

    # Parse contents
    for param_name in all_param_names:

        param_diff = False

        param_1: Optional[Parameter]
        param_2: Optional[Parameter]
        # Parameter only in first list
        if param_name in param_names_1 and param_name not in param_names_2:
            param_1 = param_list_1[param_name]
            param_2 = None
            # Test if we need to print this now
            if not param_id_test(param_1, None, vid, cid):
                continue
            param_diff = True
        # Parameter only in second list
        elif param_name in param_names_2 and param_name not in param_names_1:
            param_1 = None
            param_2 = param_list_2[param_name]
            # Test if we need to print this now
            if not param_id_test(None, param_2, vid, cid):
                continue
            param_diff = True
        # Parameter value changed
        else:
            param_1 = param_list_1[param_name]
            param_2 = param_list_2[param_name]
            # Test if we need to print this now
            if not param_id_test(param_1, param_2, vid, cid):
                continue
            v1 = param_1.value
            v2 = param_2.value
            if values_differ(v1, v2):
                param_diff = True

        if param_diff:
            comparison_list.append((param_1, param_2))

    return comparison_list


def param_id_test(
    param_1: Optional[Parameter],
    param_2: Optional[Parameter],
    vid: Optional[int],
    cid: Optional[int],
) -> bool:
    """Decide if the two parameters should be compared with each other given the demanded vehicle id and component id.

    # 1. If vid and cid are None, then compare them.
    # If only one of vid and cid is None, this is undefined.
    # 2. If p1 is None, then test only for p2. And vice versa.
    # 3. If both parameters' ids match the requested, do compare them.
    # 4. If a parameter is None it is missing and only the other will be checked
    # TODO: Double-check
    """
    try:
        get_logger().debug(
            f"Checking if {param_1}:{param_1.vid}-{param_1.cid} "  # type: ignore[union-attr]
            + f"and {param_2}:{param_2.vid}-{param_2.cid} need to be compared for {vid}-{cid}"  # type: ignore[union-attr]
        )
    except AttributeError:
        get_logger().debug(
            f"Checking if {param_1} and {param_2} need to be compared for {vid}-{cid}"
        )

    # Catch undefined input combinations
    if param_1 is None and param_2 is None:
        raise ValueError("Unhandled input values")

    spec_1 = comparison_spec_1(vid, cid)
    spec_2 = comparison_spec_2(param_1, param_2, vid, cid)
    spec_3 = comparison_spec_3(param_1, param_2, vid, cid)

    if spec_1 or spec_2 or spec_3:
        get_logger().debug("Yes, they should.")
        return True
    else:
        get_logger().debug("No, they should not.")
        return False


def comparison_spec_1(vid: Optional[int], cid: Optional[int]) -> bool:
    """Decide if two parameters should be compared in the context of the provided vid and cid."""
    if (vid is None) ^ (cid is None):
        raise ValueError("Unhandled input values")

    # Spec 1
    if vid is None:
        # No need to check for cid, it is undefined input if it's not None
        return True
    else:
        return False


def comparison_spec_2(
    param_1: Optional[Parameter],
    param_2: Optional[Parameter],
    vid: Optional[int],
    cid: Optional[int],
) -> bool:
    """If p1 is None, then test only for p2. And vice versa.

    Assumes vid, cid are not None.
    """
    if vid is None:
        raise ValueError("vid must not be None")
    if cid is None:
        raise ValueError("cid must not be None")

    if param_1 is None and param_2 is not None:
        if param_2.vid == vid and param_2.cid == cid:
            return True
        else:
            return False
    if param_2 is None and param_1 is not None:
        if param_1.vid == vid and param_1.cid == cid:
            return True
        else:
            return False
    else:
        return False


def comparison_spec_3(
    param_1: Optional[Parameter],
    param_2: Optional[Parameter],
    vid: Optional[int],
    cid: Optional[int],
) -> bool:
    """If both parameters' ids match the requested, do compare them.

    Assumes vid, cid are not None.
    """
    # Guard for input validity
    if vid is None:
        raise ValueError("vid must not be None")
    if cid is None:
        raise ValueError("cid must not be None")
    if param_1 is None or param_2 is None:
        return False

    if (param_1.vid == param_2.vid == vid) and (param_1.cid == param_2.cid == cid):
        return True
    else:
        return False


# TODO: I think this is redundant to comparison_spec_3
# def comparison_spec_4(param_1, param_2, vid, cid):
#     """If a parameter is None it means is missing and only the other will be checked."""

#     if param_1.vid != vid or param_1.cid != cid:
#         return False
#     if param_2.vid != vid or param_2.cid != cid:
#         return False
#     return True


def values_differ(v1: Union[int, float], v2: Union[int, float]) -> bool:
    """Compare if two values differ up to the level of precision."""
    return abs(v1 - v2) / (max(abs(v1), abs(v2)) + EPS) > PARAM_EPS_PCT


def get_column_lengths(
    comparison_list: List[Tuple[Optional[Parameter], Optional[Parameter]]]
) -> List[int]:
    """Find max param column lengths."""
    max_param_length = 1
    max_value_1_length = 1
    max_value_2_length = 1
    for param_tuple in comparison_list:
        if param_tuple[0] is None and param_tuple[1] is None:
            raise RuntimeError("At least one parameter must not be None")

        if param_tuple[0] is not None:
            if max_param_length < len(param_tuple[0].name):
                max_param_length = len(param_tuple[0].name)
            if max_value_1_length < len(param_tuple[0].get_pretty_value()):
                max_value_1_length = len(param_tuple[0].get_pretty_value())
        else:
            if max_param_length < len(param_tuple[1].name):  # type: ignore[union-attr] # Caught at the start of the for-loop
                max_param_length = len(param_tuple[1].name)  # type: ignore[union-attr] # Caught at the start of the for-loop

        if param_tuple[1] is not None:
            if max_value_2_length < len(param_tuple[1].get_pretty_value()):
                max_value_2_length = len(param_tuple[1].get_pretty_value())

    return [max_param_length, max_value_1_length, max_value_2_length]


def generate_comparison_strings(
    comparison_list: List[Tuple[Optional[Parameter], Optional[Parameter]]],
    column_lengths: List[int],
) -> str:
    """Generate the comparison string output, given a comparison list.

    Assumes that the comparison list contains the same VID-CID pair across all parameters.
    """
    # Check if there's anything to check at all
    if len(comparison_list) == 0:
        return ""

    # Extract the relevant vid and cid
    if comparison_list[0][0] is not None:
        vid = comparison_list[0][0].vid
        cid = comparison_list[0][0].cid
    elif comparison_list[0][1] is not None:
        vid = comparison_list[0][1].vid
        cid = comparison_list[0][1].cid
    else:
        raise ValueError("At least one of the two parameters must be non-None.")

    # Extract the column lengths
    name_len = column_lengths[0]
    value_1_len = column_lengths[1]
    value_2_len = column_lengths[2]

    # Generate header
    output_str = ""
    output_str += "-" * 80 + "\n"
    output_str += f"Component {vid}-{cid}:\n"
    output_str += "-" * 80 + "\n"

    # Parse contents
    for param_1, param_2 in comparison_list:
        output_str += build_comparison_row(
            param_1, param_2, name_len, value_1_len, value_2_len
        )
    return output_str


def build_comparison_row(
    param_1: Optional[Parameter],
    param_2: Optional[Parameter],
    name_len: int,
    value_1_len: int,
    value_2_len: int,
) -> str:
    """Generate the comparison row for a parameter pair."""
    if param_1 is None and param_2 is None:
        raise RuntimeError("at least one parameter must be non-None.")

    # Get parameter name
    if param_1 is not None:
        param_name = param_1.name
    else:
        # param_2 will never be None, thanks to the check at the start of the function.
        param_name = param_2.name  # type: ignore[union-attr]
    # Get parameter values
    if param_1 is not None:
        value_1 = param_1.get_pretty_value()
    else:
        value_1 = "X"
    if param_2 is not None:
        value_2 = param_2.get_pretty_value()
    else:
        value_2 = "X"
    # Get divider
    if param_1 is None:
        divider = "<"
    elif param_2 is None:
        divider = ">"
    else:
        divider = "|"

    return f"{param_name:{name_len}} : {value_1:{value_1_len}} {divider} {value_2:{value_2_len}}\n"


def build_comparison_string(
    comparison_lists: List[List[Tuple[Optional[Parameter], Optional[Parameter]]]],
    file1: Optional[str],
    file2: Optional[str],
) -> str:
    """Generate the comparison program textual output."""
    # Find column lengths and number of changed parameters
    if not file1:
        file1 = "List 1"
    if not file2:
        file2 = "List 2"

    names_length = 1
    value_1_length = len(file1)
    value_2_length = len(file2)
    compared_params = 0
    for comparison_list in comparison_lists:
        temp_lengths = get_column_lengths(list(comparison_list))
        if names_length < temp_lengths[0]:
            names_length = temp_lengths[0]
        if value_1_length < temp_lengths[1]:
            value_1_length = temp_lengths[1]
        if value_2_length < temp_lengths[2]:
            value_2_length = temp_lengths[2]

        compared_params += len(comparison_list)

    # Generate header
    head_1 = "File comparison"
    head_2 = file1
    head_3 = file2
    output_str = f"{head_1:{names_length}} : {head_2:{value_1_length}} | {head_3:{value_2_length}}\n"
    output_str += "=" * 80 + "\n"

    for comparison_list in comparison_lists:
        output_str += generate_comparison_strings(
            list(comparison_list), [names_length, value_1_length, value_2_length]
        )

    output_str += "=" * 80 + "\n"
    output_str += f"{compared_params} parameters differ\n"
    return output_str


def compare_helper(
    file_1: str,
    file_2: str,
    input_folder: Optional[str],
    nocal: bool,
    noop: bool,
    component: Optional[int],
) -> str:
    """Compare two parameter files.

    Args:
        file_1: The path to the first parameter file to compare.
        file_2: The path to the second parameter file to compare.
        input_folder: Necessary when the *nocal* and *noop* options are set.
            The directory where the Meals Menu is created, containing at least the *calibration* and *operator* staple dishes.
        nocal: Don't compare the calibration parameters.
        noop: Don't compare the operator parameters.
        component: Compare the parameters of a specific component. Refers to MAVLink-type Component IDs.

    Returns:
        A string with the comparison table contents.
    """
    get_logger().debug(f"Comparing {file_1} and {file_2} for component {component}")

    if input_folder:
        ConfigPaths().CUSTOM_PATH = Path(input_folder)
        get_logger().debug(f"Setting CUSTOM_PATH to {ConfigPaths().path}")

    param_list_1 = read_params(Path(file_1))
    param_list_2 = read_params(Path(file_2))
    comparison_lists = get_vehicles_comparison(
        param_list_1, param_list_2, nocal, noop, component
    )
    return build_comparison_string(
        comparison_lists, param_list_1.source_file, param_list_2.source_file
    )
