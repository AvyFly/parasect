# noqa: D101, D102, D103
"""Module with helper functions for the whole package."""
import csv
import logging
import math
import os
import re
import typing
from abc import ABC
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Callable
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
from pydantic import StrictBool


class Borg(ABC):
    """Borg API class."""

    def clear(self) -> None:
        """Reset the extra class variables."""
        self._shared_state.clear()

    @property
    @abstractmethod
    def _shared_state(self):
        pass  # pragma: no cover


class Logger(Borg):
    """Singleton to carry package-level settings."""

    _shared_state: Any = {}

    logger: logging.Logger

    def __init__(self, debug: bool = False) -> None:
        """Class constructor."""
        self.__dict__ = self._shared_state

        if len(self._shared_state) == 0:
            self._debug: bool = debug
            self.logger = setup_logger(debug)


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

    _shared_state: Any = {}

    def __init__(self) -> None:
        """Class constructor."""
        self.__dict__ = self._shared_state

        if len(self._shared_state) == 0:
            self.CUSTOM_PATH: Optional[Path] = None
            self.DEFAULT_PARAMS_PATH: Optional[Path] = None

    @property
    def path(self) -> Path:
        """Get the path of the menu folder."""
        return self._get_path()

    @property
    def meals(self) -> Path:
        """Return the meals file path."""
        return self._get_meals_path()

    @property
    def custom_dishes(self) -> Path:
        """Get the path of the custom, user-defined dishes folder."""
        return self._get_custom_dishes_path()

    @property
    def staple_dishes(self) -> Path:
        """Return the path of the staple dishes folder."""
        return self._get_staple_dishes_path()

    @property
    def default_parameters(self) -> Optional[Path]:
        """Return the path of the default parameters file."""
        return self._get_default_parameters_file()

    def _get_path(self) -> Path:
        configs_path = None
        # First check if a specific CUSTOM_PATH has been defined.
        if self.CUSTOM_PATH:
            if not Path(self.CUSTOM_PATH).is_dir():
                raise NotADirectoryError(
                    f"Given configuration path {self.CUSTOM_PATH} doesn't exist"
                )
            configs_path = self.CUSTOM_PATH

        if not configs_path:
            # If not, check if the environmental variable is set
            try:
                configs_path = Path(os.environ["PARASECT_PATH"])
                if not configs_path.expanduser().is_dir():
                    raise NotADirectoryError(
                        f"PARASECT_PATH points to invalid directory {configs_path}"
                    )
            except KeyError:
                get_logger().debug("Environment variable for parasect path not set")

        if configs_path is None:
            raise RuntimeError("Configurations path not specified.")
        get_logger().debug(f"Pointing configurations to {configs_path}")
        return configs_path

    def _get_meals_path(self) -> Path:
        path = self.path / "meals.yaml"  # type: Path
        return path

    def _get_custom_dishes_path(self) -> Path:
        path = self.path / "custom_dishes"  # type: Path
        return path

    def _get_staple_dishes_path(self) -> Path:
        path = self.path / "staple_dishes"  # type: Path
        return path

    def _get_default_parameters_file(self) -> Optional[Path]:
        filepath = None
        try:
            filepath = Path(os.environ["PARASECT_DEFAULTS"]).expanduser()
        except KeyError:
            get_logger().debug("Environment variable for parasect path not set")
        if self.DEFAULT_PARAMS_PATH:
            filepath = self.DEFAULT_PARAMS_PATH
        get_logger().debug(f"Using {filepath} as global default parameter file")
        return filepath


###############################################################################
# Input files definitions in Pydantic
###############################################################################


class Formats(Enum):
    """Supported output formats."""

    csv = "csv"
    """Simple parameter name, value .csv file."""
    px4 = "px4"
    """QGroundControl-style parameter file."""
    px4afv1 = "px4afv1"
    """Legacy PX4 airframe file, prior to version 1.11."""
    px4afv2 = "px4afv2"
    """New PX4 airframe file, version 1.11 and later."""
    apm = "apm"
    """Ardupilot-compatible file."""
    apj = "apj"
    """File compatible with Ardupilot's apj tool."""


ReservedOptions = Literal[
    "defaults",
    "frame_id",
    "sitl",
    "hitl",
    "parent",
    "remove_calibration",
    "remove_operator",
    "add_new",
]
ReservedOptionsSequence = typing.get_args(ReservedOptions)

StapleDishesNames = Literal["calibration", "user_defined", "header", "footer"]
StapleDishesNamesSequence = typing.get_args(StapleDishesNames)


class Substances(BaseModel):
    """A general list of substances.

    Each is made up by its name, its value and a justification.
    """

    __root__: List[Tuple[str, Optional[Union[float, int]], Optional[str]]]

    def __iter__(self):
        """Return an interable of the model."""
        return iter(self.__root__)


class Allergens(BaseModel, extra="forbid"):
    """Contains lists of parameters that are to be removed."""

    substances: Optional[Substances]
    groups: Optional[Substances]


class Recipe(BaseModel, extra="forbid"):
    """A set of ingredients and allergens."""

    ingredients: Optional[Substances] = None
    allergens: Optional[Allergens] = None


class DishModel(BaseModel, extra="forbid"):
    """A complete dish."""

    common: Optional[Recipe]
    variants: Optional[Dict[str, "DishModel"]]


class FormatText(BaseModel, extra="forbid"):
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


MealType = Dict[str, Optional[Union[StrictBool, int, str]]]
MealsType = Dict[str, MealType]

DishModel.update_forward_refs()


def check_type(key: str, value: Any, des_type: Any) -> None:
    """Type if value with name key is of type."""
    if not isinstance(value, des_type):
        raise TypeError(f"Value of {key}={value} should be {des_type}.")


class MealMenuModel(BaseModel):
    """The description of the whole meals catalogue."""

    __root__: MealsType

    @root_validator
    def _check_entries(cls, values):  # noqa: B902
        # Iterate over the meals
        for meal, content in values["__root__"].items():
            # Iterate over the dishes
            for dish_name in content.keys():
                cls._check_content_names(dish_name, meal)
            cls._check_content_values(content)

        return values

    @classmethod
    def _check_content_names(cls, entry_name: str, meal: str) -> None:
        """Raise an error if the names of the Meal contents are invalid."""
        if not (
            cls._is_custom_dish(entry_name)
            or cls._is_staple_dish(entry_name)
            or cls._is_reserved_option(entry_name)
        ):
            raise AssertionError(
                f"Meal {meal} contains invalid field/dish {entry_name}."
            )

    @classmethod
    def _is_custom_dish(cls, dish_name: str) -> bool:
        filename = dish_name + ".yaml"
        filepath = ConfigPaths().custom_dishes / filename
        if os.path.isfile(filepath):
            return True
        else:
            return False

    @classmethod
    def _is_staple_dish(cls, dish_name: str) -> bool:
        filename = dish_name + ".yaml"
        filepath = ConfigPaths().staple_dishes / filename
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

    @classmethod
    def _check_content_values(cls, contents: MealType) -> None:
        """Raise an error if the contents of the Meal are invalid."""
        # Iterate over the dishes and other entries
        for key, value in contents.items():
            if key in StapleDishesNamesSequence:
                check_type(key, value, (str, type(None)))
            elif key in ["parent"]:
                check_type(key, value, str)
            elif key in [
                "sitl",
                "hitl",
                "remove_calibration",
                "remove_operator",
                "add_new",
            ]:
                check_type(key, value, bool)
            elif key in ["frame_id"]:
                check_type(key, value, int)
            elif key in ["defaults"]:
                check_type(key, value, (str, type(None)))
            else:  # This is a custom dish
                check_type(key, value, (str, type(None)))

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


def _build_dict_from_yaml(filepath: Path) -> Dict:
    """Read a .yaml file as a dictionary.

    Args:
        filepath: The full file-path to a .yaml file.

    Returns:
        Dict: A dictionary equivalent to the .yaml file.
    """
    with open(filepath) as fp:
        model_dict = yaml.load(fp, Loader=yaml.SafeLoader)  # type: Dict
    return model_dict


def get_dish(path: Path, dish_name: str) -> DishModel:
    """Read a dish .yaml file.

    Args:
        path: The path to a .yaml file or folder.
        dish_name: If None, then it is assumed that path points to the dish .yaml file.
                    If str, then path is a folder and dish_name is the file name without the extension

    Returns:
        DishModel: A Pydantic model
    """
    filepath = path / (dish_name + ".yaml")
    dictionary = _build_dict_from_yaml(filepath)
    return DishModel.parse_obj(dictionary)


def get_boilerplate(path: Path, dish_name: str) -> BoilerplateText:
    """Read a boilerplate text model."""
    filepath = path / (dish_name + ".yaml")
    dictionary = _build_dict_from_yaml(filepath)
    return BoilerplateText.parse_obj(dictionary)


def get_meals_menu(filepath: Path) -> MealMenuModel:
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


def cast_param_value(value: Any, param_type: Optional[str]) -> Union[int, float]:
    """Convert a string to a parameter value of the given type."""
    if param_type is None:
        raise TypeError("Unknown type to cast value to.")
    elif param_type == "INT32":
        return int(value)
    elif param_type == "FLOAT":
        return float(value)
    else:
        raise TypeError(f"Unhandled parameter type {param_type}")


class Parameter:
    """A class describing a single parameter."""

    name: str
    param_type: Optional[str]  # String, either FLOAT or INT32
    _value: Union[int, float]
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
    readonly: bool
    group: Optional[str] = None
    vid: int  # Vehicle ID, default 1
    cid: int  # Component ID, default 1

    def __init__(
        self,
        name: str,
        value: Union[int, float],
        param_type: Optional[str] = None,
        vid: int = 1,
        cid: int = 1,
    ) -> None:
        """Class constructor."""
        self.name = name
        self.value = value
        self.param_type = param_type
        self.vid = vid
        self.cid = cid
        self.readonly = False

    @property
    def value(self) -> Union[int, float]:
        """Getter for parameter value."""
        if self.param_type == "INT32":
            return int(self._value)
        else:
            return self._value

    @value.setter
    def value(self, new_value: Union[int, float]) -> None:
        """Setter for parameter value."""
        self._value = new_value

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
            string = f"{self.value:.{digits}f}"  # There will be at least one decimal place, because digits >= 1

            # Delete trailing decimal zeroes
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
            self.params = dict(original.params)

    @classmethod
    def build_param_hash_from_param(cls, p: Parameter) -> str:
        """Build the params dictionary hash from a Parameter entry."""
        return cls.build_param_hash(p.name, p.cid)

    @staticmethod
    def build_param_hash(name: str, cid: int) -> str:
        """Build the params dictionary."""
        return f"{name}:{cid}"

    @staticmethod
    def decode_parameter_hash(hash: str) -> Tuple[str, int]:
        """Deduce parameter details from the hash."""
        parts = hash.split(":")
        name = parts[0]
        if len(parts) == 1:
            cid = 1
        else:
            cid = int(parts[1])
        return name, cid

    def __iter__(self) -> Generator[Parameter, None, None]:
        """__iter__ dunder method."""
        for param_name in sorted(self.params.keys()):
            yield self.params[param_name]

    def __sub__(self, other: "ParameterList") -> "ParameterList":
        """Subtract a ParameterList from another ParameterList."""
        param_list = ParameterList(self)
        for param in param_list:
            if param in other:
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

    def __getitem__(self, key: Union[str, Tuple[str, int]]) -> Parameter:
        """__getitem__ dunder method."""
        if isinstance(key, str):
            # The key is only a parameter name. Assume cid == 1.
            name, cid = self.decode_parameter_hash(key)
        else:
            # The cid is provided.
            name, cid = key
        param_hash = self.build_param_hash(name, cid)
        return self.params[param_hash]

    def __contains__(self, item: Union[str, Parameter]) -> bool:
        """Answer if the parameter list contains a parameter."""
        if isinstance(item, str):
            # Assume cid == 1.
            param_hash = self.build_param_hash(item, 1)
            return param_hash in self.params.keys()
        else:  # item is Parameter
            param_hash = self.build_param_hash_from_param(item)
            return param_hash in self.params.keys()

    def keys(self) -> KeysView:
        """__keys__ dunder method.

        It returns the names of the parameters it contains.
        """
        return self.params.keys()

    def update_param(self, param: Parameter) -> None:
        """Update a parameter with the values of another.

        All relevant values must be copied.
        """
        param_hash = self.build_param_hash_from_param(param)

        # Try to deduce parameter type
        if param.param_type is not None:
            # If we know the new parameter type, use that.
            new_value = param.value
        elif self.params[param_hash].param_type is None:
            # If we don't know the existing parameter type either, just paste it.
            new_value = param.value
        else:
            # We know the target type, cast the new parameter value.
            param_type = self.params[param_hash].param_type
            new_value = cast_param_value(param.value, param_type)
        self.params[param_hash].value = new_value

        # Copy the rest of the attributes. This list must be kept up to date.
        attr_list = [
            "reasoning",
            "short_desc",
            "long_desc",
            "default_value",
            "min_value",
            "max_value",
            "increment",
            "unit",
            "decimal",
            "reboot_required",
            "readonly",
            "group",
            "vid",
            "cid",
        ]
        for attr in attr_list:
            try:
                new_attr_value = getattr(param, attr)
            except AttributeError:
                continue
            if new_attr_value and (
                not isinstance(new_attr_value, str) or len(new_attr_value) > 1
            ):
                # The new value is not None and if it's a string, it's not empty.
                setattr(self.params[param_hash], attr, new_attr_value)

    def add_param(
        self, param: Parameter, safe: bool = False, overwrite: bool = True
    ) -> None:
        """Add a Parameter to the list."""
        # param: The parameter object
        # safe: allow adding new parameters
        # overwrite: allow overwriting existing parameters
        get_logger().debug(f"Attempting to add {param} to list")
        param_hash = self.build_param_hash_from_param(param)
        if safe and param_hash not in self.params.keys():
            raise KeyError(f"{param.name} with cid={param.cid} is not an existing key")
        if not overwrite and param_hash in self.params.keys():
            raise KeyError(f"Tried to overwrite key {param.name} with cid={param.cid}")
        # If parameter doesn't exist, create it
        if param_hash not in self.params:
            get_logger().debug(f"Creating new {param.name}")
            self.params[param_hash] = param
        # otherwise copy only the values
        else:
            get_logger().debug(f"Overwriting {param.name}")
            self.update_param(param)

    def remove_param(self, param: Parameter, safe: bool = True) -> None:
        """Remove a Parameter from the list."""
        # param: The parameter object
        # safe: don't try to remove not existing parameters
        param_hash = self.build_param_hash_from_param(param)
        if safe and param_hash not in self.params:
            raise KeyError(f"{param.name} with cid={param.cid} is not an existing key")
        get_logger().debug(f"Removing {param.name}.")
        self.params.pop(param_hash, None)


def filter_regex(regex_list: List[str], param_list: ParameterList) -> None:
    """Remove from param_list all parameters that match any of the regex_list."""
    regex_obj_list = [re.compile(s) for s in regex_list]
    for param in param_list:
        if any(r.fullmatch(param.name) for r in regex_obj_list):
            get_logger().debug(f"Matched {param.name} to a regex.")
            param_list.remove_param(param)


# Construct parameters from structured input
############################################


def build_param_from_xml(parameter: XmlElement) -> Parameter:
    """Build a Parameter from an PX4-type xml entry."""
    name = str(parameter.get("name"))
    default_value = str(parameter.get("default"))
    param_type = str(parameter.get("type"))
    value = cast_param_value(default_value, param_type)  # Assign the default value
    param = Parameter(name, value)
    param.default_value = value
    param.param_type = param_type
    return param


def build_param_from_qgc(row: List[str]) -> Parameter:
    """Build a Parameter from an QGroundControl-type entry."""
    get_logger().debug(f"Decoding parameter file row: {row}")
    vehicle_id = int(row[0])
    componenent_id = int(row[1])
    # Test if parameter name is a number
    try:
        float(row[2])
        raise SyntaxError("Third element must be a parameter name string")
    except ValueError:
        param_name = row[2]
    param_type_num = int(row[4])
    if param_type_num == 6:
        param_type = "INT32"
    elif param_type_num == 9:
        param_type = "FLOAT"
    else:
        raise ValueError(f"Unknown parameter type: {param_type_num}")

    param_value = cast_param_value(row[3], param_type)

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


def build_param_from_mavproxy(item: Sequence) -> Parameter:
    """Convert a mavproxy parameter line to a parameter.

    item should be a 3-length sequence of strings.
    """
    name = item[0]
    value: Union[int, float]
    value = item[1]
    try:
        value = int(item[1])
    except ValueError:
        value = float(item[1])
    reasoning = item[2]

    param = Parameter(name, value)
    param.reasoning = reasoning

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

    # Mark the parameter as readonly (supported in Ardupilot)
    if reasoning and reasoning.find("@READONLY") > 1:
        get_logger().debug(f"Marking {name} as READONLY.")
        param.readonly = True

    return param


# Read parameter text files
###########################

parsers: List[Callable[[Path], ParameterList]] = []


def parser(parser_func: Callable) -> Callable:
    """Decorator to mark and collect parser functions."""
    parsers.append(parser_func)
    return parser_func


def get_group_params_xml(group: XmlElement) -> Generator[XmlElement, None, None]:
    """Read parameter elements from an PX4-style XML group element.

    Receives an XmlElement
    Returns an XmlElement
    """
    yield from group.findall("parameter")


@parser
def read_params_xml(filepath: Path) -> ParameterList:
    """Read and parse an PX4-style XML parameter list."""
    try:
        tree = eTree.parse(filepath)
        root = tree.getroot()

        param_list = ParameterList()

        # Parse all parameter groups
        for group in root.findall("group"):
            group_name = group.get("name")
            for param_xml in get_group_params_xml(group):
                param = build_param_from_xml(param_xml)
                param.group = group_name
                get_logger().debug(f"Created new parameter from XML: {param}")
                param_list.add_param(param)

        # Parse all loose parameters
        for param_xml in root.findall("parameter"):
            param = build_param_from_xml(param_xml)
            param_list.add_param(param)

        return param_list
    except eTree.ParseError as e:
        raise SyntaxError("File is not of XML format.") from e


@parser
def read_params_qgc(filepath: Path) -> ParameterList:
    """Read and parse a QGC/AMC/Auterion Suite parameters file."""
    param_list = ParameterList()

    try:
        with open(filepath) as csvfile:
            param_reader = csv.reader(csvfile, delimiter="\t")
            for param_row in param_reader:  # pragma: no branch
                get_logger().debug(f"Examining line: {param_row}")
                if len(param_row) == 0:  # Skip empty lines
                    continue
                if param_row[0][0] == "#":  # Skip comment lines
                    continue
                # Test for wrong number of elements
                if len(param_row) != 5:
                    raise SyntaxError("Wrong number of line elements")
                param = build_param_from_qgc(param_row)
                param_list.add_param(param)

        if len(param_list.params) == 0:
            raise (SyntaxError("Could not extract any parameter from file."))

        return param_list
    except SyntaxError as e:
        raise SyntaxError(f"File is not of QGC format:\n{e}") from e


@parser
def read_params_ulog_param(filepath: Path) -> ParameterList:
    """Read and parse the outputs of the ulog_params program."""
    param_list = ParameterList()

    try:
        with open(filepath) as csvfile:
            param_reader = csv.reader(csvfile, delimiter=",")
            for param_row in param_reader:  # pragma: no branch
                if param_row[0][0] == "#":  # Skip comment lines
                    continue
                # Check if line has exactly two elements
                if len(param_row) != 2:
                    raise SyntaxError(
                        f"Invalid number of elements for ulog param decoder: {len(param_row)}"
                    )
                # Check if first element is a string
                try:
                    float(param_row[0])
                    raise SyntaxError(
                        "First row element must be a parameter name string"
                    )
                except ValueError:
                    pass
                param = build_param_from_ulog_params(param_row)
                param_list.add_param(param)

        if len(param_list.params) == 0:
            raise (SyntaxError("Could not extract any parameter from file."))

        return param_list
    except SyntaxError as e:
        raise SyntaxError(f"File is not of ulog format:\n{e}") from e


def split_mavproxy_row(row: str) -> Sequence:
    """Split a line, assuming it is mavproxy syntax."""
    params = row.split()
    # Check if line has exactly two elements
    if len(params) not in (2, 3):
        raise SyntaxError(
            f"Invalid number of elements for mavproxy param decoder: {len(params)}"
        )
    # Check if first element is a string
    try:
        float(params[0])
        raise SyntaxError("First row element must be a parameter name string.")
    except ValueError:
        pass
    try:
        float(params[1])
    except ValueError as e:
        raise SyntaxError("First row element must be a parameter name string.") from e
    # Insert empty reasoning if item 3 doesn't exist.
    if len(params) == 2:
        params.append("")

    return params


@parser
def read_params_mavproxy(filepath: Path) -> ParameterList:
    """Read and parse the outputs of mavproxy."""
    param_list = ParameterList()

    try:
        with open(filepath) as f:
            for line in f:  # pragma: no branch
                if line[0] == "#":  # Skip comment lines
                    continue
                params = split_mavproxy_row(line)
                param = build_param_from_mavproxy(params)
                param_list.add_param(param)

        if len(param_list.params) == 0:
            raise (SyntaxError("Could not extract any parameter from file."))

        return param_list
    except SyntaxError as e:
        raise SyntaxError(f"File is not of mavproxy format:\n{e}") from e


def read_params(filepath: Path) -> ParameterList:
    """Universal parameter reader."""
    get_logger().debug(f"Attempting to read file {filepath}")
    protocols_recognized = 0

    for parser in parsers:
        try:
            param_list = parser(filepath)
            protocols_recognized += 1
        except SyntaxError as e:
            get_logger().debug(e)
            pass

    if protocols_recognized == 0:
        raise SyntaxError("Could not recognize log protocol.")
    if protocols_recognized > 1:
        raise SyntaxError("Protocol ambiguous, fits more than one parser.")

    # Add filename to list
    comps = os.path.split(filepath)
    filename = comps[-1]
    param_list.source_file = filename
    return param_list
