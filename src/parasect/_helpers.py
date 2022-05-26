# noqa: D101, D102, D103
"""Module with helper functions for the whole package."""
import csv
import logging
import math
import os
import pathlib
import typing
from enum import Enum
from typing import Any
from typing import Dict
from typing import Generator
from typing import KeysView
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from xml.etree.ElementTree import Element as XmlElement  # noqa: S405

import yaml  # type: ignore
from defusedxml import ElementTree as eTree  # type: ignore
from pydantic import BaseModel
from pydantic import root_validator


class Borg:
    """Borg helper class."""

    _shared_state: Any = {}

    def __init__(self) -> None:
        """Class constructor."""
        self.__dict__ = self._shared_state

    def clear(self) -> None:
        """Clear the instance dictionary and start afresh."""
        self._shared_state = {}
        self._first_call = True


class Logger(Borg):
    """Singleton to carry package-level settings."""

    _debug: bool = False
    _first_call: bool = True
    logger: logging.Logger

    def __init__(self, debug: bool = False) -> None:
        """Class constructor."""
        Borg.__init__(self)

        if self._first_call:
            self.logger = setup_logger(debug)
            self._first_call = False


def setup_logger(debug: bool) -> logging.Logger:
    """Build and return a logger for the parasect package."""
    # Get the logger
    logger = logging.getLogger("parasect")
    # Purge previous handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Construct a new handler
    log_format = "%(name)s - %(levelname)s - %(message)s"
    if debug:
        file_handler = logging.FileHandler("parasect.log", "w")
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
    else:
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(log_format)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)

    return logger


def get_logger() -> logging.Logger:
    """Access the logger singleton."""
    return Logger().logger


class ConfigPaths(Borg):
    """Helper class to construct the configurations and parameter filepaths."""

    CUSTOM_PATH: Optional[str] = None
    DEFAULT_PARAMS_PATH: Optional[str] = None

    def __init__(self) -> None:
        """Class constructor."""
        Borg.__init__(self)

    @property
    def path(self) -> str:
        """Get the path of the menu folder."""
        return self._get_path()

    @property
    def meals(self) -> str:
        """Return the meals file path."""
        return self._get_meals_path()

    @property
    def custom_dishes(self) -> str:
        """Get the path of the custom, user-defined dishes folder."""
        return self._get_custom_dishes_path()

    @property
    def staple_dishes(self) -> str:
        """Return the path of the staple dishes folder."""
        return self._get_staple_dishes_path()

    @property
    def default_parameters(self) -> str:
        """Return the path of the default parameters file."""
        return self._get_default_parameters_file()

    def _get_path(self) -> str:
        configs_path = None
        # First check if a specific CUSTOM_PATH has been defined.
        if self.CUSTOM_PATH:
            if not os.path.isdir(self.CUSTOM_PATH):
                raise NotADirectoryError(
                    "Given configuration path {self.CUSTOM_PATH} doesn't exist"
                )
            configs_path = self.CUSTOM_PATH

        if not configs_path:
            # If not, check if the environmental variable is set
            try:
                configs_path = os.environ["PARASECT_PATH"]
                if not pathlib.Path(configs_path).expanduser().is_dir():
                    raise NotADirectoryError(
                        f"PARASECT_PATH points to invalid directory {configs_path}"
                    )
            except KeyError:
                get_logger().debug("Environment variable for parasect path not set")

        if configs_path is None:
            raise RuntimeError("Configurations path not specified.")
        get_logger().debug(f"Pointing configurations to {configs_path}")
        return configs_path

    def _get_meals_path(self) -> str:
        return os.path.join(self.path, "meals.yaml")

    def _get_custom_dishes_path(self) -> str:
        return os.path.join(self.path, "custom_dishes")

    def _get_staple_dishes_path(self) -> str:
        return os.path.join(self.path, "staple_dishes")

    def _get_default_parameters_file(self) -> str:
        filepath = None
        try:
            filepath = os.path.expanduser(os.environ["PARASECT_DEFAULTS"])
        except KeyError:
            get_logger().debug("Environment variable for parasect path not set")
        if self.DEFAULT_PARAMS_PATH:
            filepath = self.DEFAULT_PARAMS_PATH
        if filepath is None:
            raise RuntimeError("Default parameters path not specified.")
        get_logger().debug(f"Using {filepath} as global default parameter file")
        return filepath


###############################################################################
# Input files definitions in Pydantic
###############################################################################


class Formats(Enum):
    """Supported output formats."""

    px4 = "px4"
    px4af = "px4af"


ReservedOptions = Literal["frame_id", "sitl", "parent"]
ReservedOptionsSequence = typing.get_args(ReservedOptions)

StapleDishesNames = Literal["calibration", "user_defined", "header", "footer"]
StapleDishesNamesSequence = typing.get_args(StapleDishesNames)


class Substances(BaseModel):
    """A general list of substances.

    Each is made up by its name, its value and a justification.
    """

    __root__: List[Tuple[str, Optional[Union[int, float]], Optional[str]]]

    def __iter__(self):
        """Return an interable of the model."""
        return iter(self.__root__)


class Allergens(BaseModel):
    """Contains lists of parameters that are to be removed."""

    substances: Optional[Substances]
    groups: Optional[Substances]


class Recipe(BaseModel):
    """A set of ingredients and allergens."""

    ingredients: Optional[Substances]
    allergens: Optional[Allergens]


class DishModel(BaseModel):
    """A complete dish."""

    common: Optional[Recipe]
    variants: Optional[Dict[str, "DishModel"]]


class FormatText(BaseModel):
    """Boilerplate text for export formats."""

    common: Optional[List[str]]
    variants: Optional[Dict[str, "FormatText"]]


FormatText.update_forward_refs()


class BoilerplateText(BaseModel):
    """Boilerprate text definitions.

    For header and footer specification.
    """

    common: Optional[List[str]]
    formats: Dict[str, FormatText]


MealType = Dict[str, Optional[Union[int, str]]]
MealsType = Dict[str, MealType]

DishModel.update_forward_refs()


class MealMenuModel(BaseModel):
    """The description of the whole meals catalogue."""

    __root__: MealsType

    @root_validator
    def _check_entries(cls, values):  # noqa: B902
        # Iterate over the meals
        for meal in values["__root__"].keys():
            # Iterate over the dishes
            for dish in values["__root__"][meal]:
                if not (
                    cls._is_custom_dish(dish)
                    or cls._is_staple_dish(dish)
                    or cls._is_reserved_option(dish)
                ):
                    raise AssertionError(
                        f"Meal {meal} contains invalid field/dish {dish}."
                    )
        return values

    @classmethod
    def _is_custom_dish(cls, dish_name: str) -> bool:
        filename = dish_name + ".yaml"
        filepath = os.path.join(ConfigPaths().custom_dishes, filename)
        if os.path.isfile(filepath):
            return True
        else:
            return False

    @classmethod
    def _is_staple_dish(cls, dish_name: str) -> bool:
        filename = dish_name + ".yaml"
        filepath = os.path.join(ConfigPaths().staple_dishes, filename)
        if os.path.isfile(filepath):
            return True
        else:
            return False

    @classmethod
    def _is_reserved_option(cls, option_name: str) -> bool:
        if option_name in ReservedOptionsSequence:
            return True
        else:
            return False

    def __getitem__(self, item):
        """Access the model in a dict-like manner."""
        return self.__root__[item]

    def keys(self) -> KeysView:
        """Return all dict keys."""
        return self.__root__.keys()


class CalibrationModel(BaseModel):
    """The Calibration definition."""

    common: Dict[Formats, List[str]]
    variants: Dict[str, "CalibrationModel"]


class UserDefinedModel(CalibrationModel):
    """The User Defined definition.

    Same as the Calibration.
    """

    pass


def _build_dict_from_yaml(filepath: str) -> Dict:
    """Read a .yaml file as a dictionary.

    Args:
        filepath: The full file-path to a .yaml file.

    Returns:
        Dict: A dictionary equivalent to the .yaml file.
    """
    with open(filepath) as fp:
        model_dict = yaml.load(fp, Loader=yaml.SafeLoader)  # type: Dict
    return model_dict


def get_dish(path: str, dish_name: str) -> DishModel:
    """Read a dish .yaml file.

    Args:
        path: The path to a .yaml file or folder.
        dish_name: If None, then it is assumed that path points to the dish .yaml file.
                    If str, then path is a folder and dish_name is the file name without the extension

    Returns:
        DishModel: A Pydantic model
    """
    filepath = os.path.join(path, dish_name + ".yaml")
    dictionary = _build_dict_from_yaml(filepath)
    return DishModel.parse_obj(dictionary)


def get_boilerplate(path: str, dish_name: str) -> BoilerplateText:
    """Read a boilerplate text model."""
    filepath = os.path.join(path, dish_name + ".yaml")
    dictionary = _build_dict_from_yaml(filepath)
    return BoilerplateText.parse_obj(dictionary)


def get_meals_menu(filepath: str) -> MealMenuModel:
    """Read a meals menu .yaml file.

    Args:
        filepath: The path to a .yaml file.

    Returns:
        MealMenuModel: A Pydantic model
    """
    dictionary = _build_dict_from_yaml(filepath)
    return MealMenuModel.parse_obj(dictionary)


##################################
# Parameter manipulation functions
##################################


def get_param_from_str(string: str, param_type: Union[str, int]) -> Union[int, float]:
    """Convert a string to a parameter value of the given type."""
    if param_type == "INT32" or param_type == 6:
        return int(string)
    elif param_type == "FLOAT" or param_type == 9:
        return float(string)
    else:
        raise ValueError(f"Unhandled parameter type {param_type}")


class Parameter:
    """A class describing a single parameter."""

    name: str
    param_type: Optional[str]  # String, either FLOAT or INT32
    value: Union[int, float]
    reasoning = None
    short_desc = None
    long_desc = None
    default_value: Union[int, float]
    min_value = float("-inf")
    max_value = float("inf")
    increment = None  # Instruction for increments for UIs
    unit = None
    decimal = None  # Suggested increment by the parameter documentation
    reboot_required = False
    group = None
    vid: int = 1  # Vehicle ID, default 1
    cid: int = 1  # Componenet ID, default 1

    def __init__(self, name: str, value: Union[int, float]) -> None:
        """Class constructor."""
        self.name = name.upper()
        self.value = value
        self.param_type = None

    def __str__(self) -> str:
        """__str__ dunder method."""
        if self.param_type == "FLOAT":
            type_str = "F"
            value_str = f"{self.value:f}"
        elif self.param_type == "INT32":
            type_str = "I"
            value_str = f"{self.value:d}"
        else:
            type_str = ""
            value_str = f"{self.value}"

        return f"{self.name:16} ({type_str}):\t{value_str}"

    def get_pretty_value(self, precision: int = 3) -> str:
        """Get a printable string of the parameter value."""
        if self.param_type == "INT32":
            # Number is declared an integer
            string = f"{self.value:d}"
        elif self.param_type is None and self.value % 1 == 0:
            # Number type is unknown but is integer
            string = f"{int(self.value):d}"
        elif self.value == 0:
            # Number type is float and zero
            string = "0.0"
        else:
            # Number is a float
            zeros_post_decimal = math.floor(math.log(abs(self.value)) / math.log(0.1))
            digits = int(precision + zeros_post_decimal)
            digits = max(digits, 1)
            string = f"{self.value:.{digits}f}"

            # Delete trailing decimal zeroes
            if "." in string:
                while string[-1] == "0":
                    string = string[:-1]
                # Make sure at least one decimal zero exists
                if string[-1] == ".":
                    string += "0"

        get_logger().debug(
            f"Converted value of {self.name} from {self.value} to {string}"
        )
        return string


class ParameterList:
    """A class representing a list of Parameter's."""

    source_file: Optional[str] = None
    params: Dict[str, Parameter]

    def __init__(self, original: Optional["ParameterList"] = None):
        """Class constructor."""
        if not original:
            self.params = dict()
        else:
            self.params = original.params

    def __iter__(self) -> Generator[Parameter, None, None]:
        """__iter__ dunder method."""
        for param_name in sorted(self.params.keys()):
            yield self.params[param_name]

    def __sub__(self, other: "ParameterList") -> "ParameterList":
        """Subtract a ParameterList from another ParameterList."""
        param_list = ParameterList(self)
        for param in param_list:
            if param.name in other.keys():
                param_list.remove_param(param)
        return param_list

    def __str__(self) -> str:
        """__str__ dunder method."""
        param_strings = []
        for param_name in sorted(self.params.keys()):
            param_strings.append(self.params[param_name].__str__())
        return "\n".join(param_strings)

    def __len__(self) -> int:
        """__len__ dunder method."""
        return len(self.params)

    def __getitem__(self, key: str) -> Parameter:
        """__getitem__ dunder method."""
        return self.params[key]

    def keys(self) -> KeysView:
        """__keys__ dunder method.

        It returns the names of the parameters it contains.
        """
        return self.params.keys()

    def add_param(
        self, param: Parameter, safe: bool = False, overwrite: bool = True
    ) -> None:
        """Add a Parameter to the list."""
        # param: The parameter object
        # safe: allow adding new parameters
        # overwrite: allow overwriting existing parameters
        get_logger().debug(f"Attempting to add {param} to list")
        if safe and param.name not in self.params.keys():
            raise KeyError(f"{param.name} is not an existing key")
        if not overwrite and param.name in self.params.keys():
            raise KeyError(f"Tried to overwrite key {param.name}")
        # If parameter doesn't exist, create it
        if param.name not in self.params:
            self.params[param.name] = param
        # otherwise copy only the value
        else:
            # Try to deduce parameter type
            if param.param_type is not None:
                new_value = param.value
            elif self.params[param.name].param_type is None:
                new_value = param.value
            else:
                param_type = self.params[param.name].param_type
                if param_type == "INT32":
                    new_value = int(param.value)
                elif param_type == "FLOAT":
                    new_value = float(param.value)
                else:
                    raise ValueError(
                        f"Unsupported parameter type {param_type} for parameter {param.name}"
                    )
            self.params[param.name].value = new_value

    def remove_param(self, param: Parameter, safe: bool = True) -> None:
        """Remove a Parameter from the list."""
        # param: The parameter object
        # safe: don't try to remove not existing parameters
        if safe and param.name not in self.params.keys():
            raise KeyError(f"{param.name} is not an existing key")
        self.params.pop(param.name, None)


# Construct parameters from structured input
############################################


def build_param_from_xml(parameter: XmlElement) -> Parameter:
    """Build a Parameter from an PX4-type xml entry."""
    name = str(parameter.get("name"))
    default_value = str(parameter.get("default"))
    param_type = str(parameter.get("type"))
    value = get_param_from_str(default_value, param_type)  # Assign the default value
    param = Parameter(name, value)
    param.default_value = value
    param.param_type = param_type
    return param


def build_param_from_qgc(row: List[str]) -> Parameter:
    """Build a Parameter from an QGroundControl-type entry."""
    get_logger().debug(f"Decoding parameter file row: {row}")
    vehicle_id = int(row[0])
    componenent_id = int(row[1])
    param_name = row[2]
    param_type_num = int(row[4])
    if param_type_num == 6:
        param_type = "INT32"
    elif param_type_num == 9:
        param_type = "FLOAT"
    else:
        raise ValueError(f"Unknown parameter type: {param_type_num}")

    param_value = get_param_from_str(row[3], param_type)

    param = Parameter(param_name, param_value)
    param.param_type = param_type
    param.vid = vehicle_id
    param.cid = componenent_id

    return param


def build_param_from_ulog_params(row: List[str]) -> Parameter:
    """Build a Parameter from an ulog_params printout entry."""
    param_name = row[0]
    param_value: Union[int, float]
    try:
        param_value = int(row[1])
    except ValueError:
        param_value = float(row[1])

    param = Parameter(param_name, param_value)

    return param


def build_param_from_iter(item: Sequence) -> Parameter:
    """Convert a param list item to a parameter.

    Item should be of the form [name, value, reasoning string]
    """
    name = item[0]
    value = item[1]
    reasoning = item[2]

    if value is None:
        # This is typically the case of Allergens, where no value is needed
        value = 0
    param = Parameter(name, value)
    param.reasoning = reasoning

    return param


# Read parameter text files
###########################


def get_group_params_xml(group: XmlElement) -> Generator[XmlElement, None, None]:
    """Read parameter elements from an PX4-style XML group element.

    Receives an XmlElement
    Returns an XmlElement
    """
    yield from group.findall("parameter")


def read_params_xml(filepath: str) -> ParameterList:
    """Read and parse an PX4-style XML parameter list."""
    tree = eTree.parse(filepath)
    root = tree.getroot()

    param_list = ParameterList()

    # Parse all parameter groups
    for group in root.findall("group"):
        group_name = group.get("name")
        for param_xml in get_group_params_xml(group):
            param = build_param_from_xml(param_xml)
            param.group = group_name.upper()
            get_logger().debug(f"Created new parameter from XML: {param}")
            param_list.add_param(param)

    # Parse all loose parameters
    for param_xml in root.findall("parameter"):
        param = build_param_from_xml(param_xml)
        param_list.add_param(param)

    return param_list


def read_params_qgc(filepath: str) -> ParameterList:
    """Read and parse a QGC/AMC/Auterion Suite parameters file."""
    param_list = ParameterList()

    with open(filepath) as csvfile:
        param_reader = csv.reader(csvfile, delimiter="\t")
        for param_row in param_reader:
            get_logger().debug(f"Examining line: {param_row}")
            if len(param_row) == 0:  # Skip empty lines
                continue
            if param_row[0][0] == "#":  # Skip comment lines
                continue
            # Test for wrong number of elements
            if len(param_row) != 5:
                raise SyntaxError("Wrong number of line elements")
            # Test if 3rd element is a string
            try:
                float(param_row[2])
                raise SyntaxError("First element must be a parameter name string")
            except ValueError:
                pass
            param = build_param_from_qgc(param_row)
            param_list.add_param(param)

    return param_list


def read_params_ulog_param(filepath: str) -> ParameterList:
    """Read and parse the outputs of the ulog_params program."""
    param_list = ParameterList()

    with open(filepath) as csvfile:
        param_reader = csv.reader(csvfile, delimiter=",")
        for param_row in param_reader:
            # Check if line has exactly two elements
            if len(param_row) != 2:
                raise SyntaxError(
                    f"Invalid number of elements for ulog param decoder: {len(param_row)}"
                )
            # Check if first element is a string
            try:
                float(param_row[0])
                raise SyntaxError("First element must be a parameter name string")
            except ValueError:
                pass
            param = build_param_from_ulog_params(param_row)
            param_list.add_param(param)

    return param_list


def read_params(filepath: str) -> ParameterList:
    """Universal parameter reader."""
    get_logger().debug(f"Attempting to read file {filepath}")
    protocols_recognized = 0

    try:
        param_list = read_params_xml(filepath)
        protocols_recognized += 1
    except eTree.ParseError:
        get_logger().debug("File is not of XML format.")
        pass

    try:
        param_list = read_params_ulog_param(filepath)
        protocols_recognized += 1
    except SyntaxError as e:
        get_logger().debug(f"File is not of ulog format:\n{e}")
        pass

    try:
        param_list = read_params_qgc(filepath)
        protocols_recognized += 1
    except SyntaxError:
        get_logger().debug("File is not of QGC format.")
        pass
    # except ValueError:
    #     pass

    if protocols_recognized == 0:
        raise SyntaxError("Could not recognize log protocol.")
    if protocols_recognized > 1:
        raise SyntaxError("Protocol ambiguous, fits more than one parser.")

    # Add filename to list
    comps = os.path.split(filepath)
    filename = comps[-1]
    param_list.source_file = filename
    return param_list
