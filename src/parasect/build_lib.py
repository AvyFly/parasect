"""Module providing the generation of parameter sets."""
import os
from pathlib import Path
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from ._helpers import Allergens
from ._helpers import BoilerplateText
from ._helpers import build_param_from_iter
from ._helpers import ConfigPaths
from ._helpers import DishModel
from ._helpers import filter_regex
from ._helpers import Formats
from ._helpers import get_boilerplate
from ._helpers import get_dish
from ._helpers import get_logger
from ._helpers import get_meals_menu
from ._helpers import MealMenuModel
from ._helpers import MealType
from ._helpers import Parameter
from ._helpers import ParameterList
from ._helpers import read_params
from ._helpers import Recipe
from ._helpers import ReservedOptionsSequence
from ._helpers import StapleDishesNamesSequence
from ._helpers import Substances


__all__ = ["Parameter", "ParameterList"]


#####################################
# Parameter file definition functions
#####################################
class Dish:
    """A complete dish description."""

    param_list: ParameterList
    black_groups: ParameterList  # Used to hold the blacklisted groups
    black_params: ParameterList  # Used to hold the blacklisted params
    name = None
    sn = None

    def __init__(
        self,
        dish_model: DishModel,
        model: Optional[str] = None,
        sn: Optional[str] = None,
    ):
        """Class constructor.

        Create a parameter list by passing the configuration file and the top name.
        It will also load the common parameters for that top name.
        """
        self.name = model
        self.sn = sn

        get_logger().debug(f"Creating module {self.__class__}/{self.name}")
        self.param_list = ParameterList()
        self.black_groups = ParameterList()
        self.black_params = ParameterList()

        # Load common list
        get_logger().debug("Parsing common parameters")
        common_list = dish_model.common
        if common_list:
            self.parse_recipe(common_list)

        # Load model parameters
        if model is not None:
            self.parse_model_parameters(dish_model, model, sn)

    def parse_model_parameters(
        self,
        dish_model: DishModel,
        model: str,
        sn: Optional[str] = None,
    ) -> None:
        """Read the model and sn information from the param_dict."""
        # Iterate over all selected models
        # TODO: Make this recursive for variants(models/sns/etc)
        variant_model = self.get_variant(dish_model, model)
        if variant_model is not None:
            # Load common parameters for all SNs of the same model
            common_recipe = variant_model.common
            if common_recipe is not None:
                get_logger().debug(f"Parsing {model} common parameters")
                self.parse_recipe(common_recipe)
            # Load serial number parameters
            if sn:
                sn_recipe = self.get_sn_recipe(model, variant_model, sn)
                self.parse_recipe(sn_recipe)
        else:
            pass

    def get_variant(
        self, dish_model: DishModel, variant_name: str
    ) -> Optional[DishModel]:
        """Extract the variant from a dish."""
        if dish_model.variants:
            try:
                variant = dish_model.variants[variant_name]
            except KeyError as err:
                raise KeyError(
                    f"The variant {variant_name} is not found in the parameter list of {self.__class__}"
                ) from err
            return variant
        else:
            return None

    def get_sn_recipe(
        self, model_name: str, dish_variant: DishModel, sn: str
    ) -> Recipe:
        """Extract the sn list from a model dictionary."""
        if dish_variant.variants:
            try:
                ingredients = dish_variant.variants[sn].common
            except KeyError as err:
                raise KeyError(
                    f"The submodel {model_name}/{sn} is not found in the parameter list"
                ) from err
            if ingredients:
                return ingredients
            else:
                return Recipe()
        else:
            raise SyntaxError(
                f"Tried to request subvariant {sn} but no subvariants are specified."
            )

    def parse_recipe(self, recipe: Recipe) -> None:
        """Parse a dictionary with parameters.

        Accepts a dict with contents:
        a "blacklist" dict (optional): a dictionary with keys "groups" and "parameters" with a parameter list
        inside of it, in case this is a blacklist class
        a "parameters" dict (optional): list of parameter items for normal parameter classes
        """
        # Read blacklist if exists
        if recipe.allergens:
            self.parse_allergens(recipe.allergens)

        # Read edited parameters
        if recipe.ingredients:
            self.parse_substances(recipe.ingredients, self.param_list)

    def parse_allergens(self, black_list: Allergens) -> None:
        """Parse the black list and group blacklist."""
        # Read all blacklisted groups
        get_logger().debug("Parsing blacklisted groups")
        self.parse_substances(black_list.groups, self.black_groups)
        # Read all blacklisted params
        get_logger().debug("Parsing blacklisted parameters")
        self.parse_substances(black_list.substances, self.black_params)

    def parse_substances(
        self, substances: Optional[Substances], storage: ParameterList
    ) -> None:
        """Parse a Substances object into a ParameterList."""
        if substances is not None:
            for item in substances:
                storage.add_param(build_param_from_iter(item))

    def __str__(self):
        """__str__ dunder method."""
        return self.param_list.__str__()

    def __iter__(self):
        """__iter__ dunder method."""
        yield from self.param_list

    def __contains__(self, item: Union[str, Parameter]) -> bool:
        """Answer if the Dish contains a parameter."""
        return self.param_list.__contains__(item)

    def __len__(self):
        """__len__ dunder method."""
        return len(self.param_list)


class Calibration(Dish):
    """Parameter class holding calibration parameters."""

    def __init__(self, frame: Optional[str] = None):
        """Class constructor."""
        param_dict = get_dish(ConfigPaths().staple_dishes, "calibration")
        super().__init__(param_dict, model=frame)


class Operator(Dish):
    """Parameter class holding operator-defined parameters."""

    def __init__(self, frame: Optional[str] = None):
        """Class constructor."""
        param_dict = get_dish(ConfigPaths().staple_dishes, "operator")
        super().__init__(param_dict)


class Meal:
    """An order able to build the full parameter list of a vehicle."""

    name = ""
    frame_id: int
    is_sitl = False
    is_hitl = False
    add_header = False
    header: Optional[str] = None
    add_footer = False
    footer: Optional[str] = None
    parent: Optional["Meal"] = None
    add_new = False
    remove_calibration_flag = False
    remove_operator_flag = False
    param_list: ParameterList
    default_param_list: ParameterList
    custom_dishes_names = None

    def __init__(
        self,
        meals_menu: MealMenuModel,
        default_params_filepath: Optional[Path],
        configs_path: Path,
        name: str = "Unknown",
    ):
        """Class constructor."""
        self.name = name
        get_logger().debug(f"Building new recipe {self.name}")

        # Pick your own recipe configuration
        meal_dict = meals_menu[name]

        # Parse frame_id
        if "frame_id" in meal_dict.keys():
            self.frame_id = meal_dict["frame_id"]
        else:
            self.frame_id = 0

        # Parse the default parameters
        self.parse_default_parameters(meal_dict, configs_path, default_params_filepath)

        self.parse_parent(
            meal_dict,
            meals_menu,
            default_params_filepath,
            configs_path,
        )

        # Set the base parameters
        self.load_base_parameters()

        # Decide if new parameters are allowed in this Meal
        if default_params_filepath or self.parent:
            self.add_new = False
        else:
            self.add_new = True

        self.parse_header_footer(meal_dict)

        # Check if this Recipe refers to a SITL model
        if "sitl" in meal_dict.keys():
            self.is_sitl = meal_dict["sitl"]

        # Check if this Recipe refers to a HITL model
        if "hitl" in meal_dict.keys():
            self.is_hitl = meal_dict["hitl"]

        # Check if it is explicitly allowed to add new (non-existing in the parent recipe) parameters
        if "add_new" in meal_dict.keys():
            self.add_new = meal_dict["add_new"]

        self.decide_on_calibration(meal_dict)

        self.decide_on_operator(meal_dict)

        # Read configuration specific modules
        dishes_dict = self.collect_dishes(meal_dict)  # type: Dict[str, Dish]

        # Compile all custom parameters flat to make sure they don't overwrite each other
        (
            edited_param_list,
            black_param_list,
            black_group_list,
        ) = self.collect_parameter_lists(dishes_dict)

        self.apply_edits(edited_param_list, default_params_filepath)

        # Remove blacklist parameters
        self.remove_blacklist(black_param_list, black_group_list)

        self.remove_calibration()

        self.remove_operator()

    def parse_parent(
        self,
        meal_dict: MealType,
        all_meals: MealMenuModel,
        default_params_filepath: Optional[Path],
        configs_path: Path,
    ) -> None:
        """Check if a parent key is passed and load its presets."""
        if "parent" in meal_dict.keys():
            parent_name = meal_dict["parent"]
            get_logger().debug(f"Reading modules of parent {parent_name}.")
            self.parent = Meal(
                all_meals, default_params_filepath, configs_path, parent_name  # type: ignore # Pydantic guarantees this is a string
            )

    def parse_header_footer(self, meal_dict: MealType) -> None:
        """Store the desired header and footer files."""
        # Bring in the parent's options first
        if self.parent and self.parent.add_header:
            self.add_header = True
            self.header = self.parent.header

        if self.parent and self.parent.add_footer:
            self.add_footer = True
            self.footer = self.parent.footer

        # Overwrite with newly specified ones
        if "header" in meal_dict.keys():
            self.add_header = True
            self.header = meal_dict["header"]  # type: ignore # Pydantic guarantees this is a string
        if "footer" in meal_dict.keys():
            self.add_footer = True
            self.footer = meal_dict["footer"]  # type: ignore # Pydantic guarantees this is a string

    def parse_default_parameters(
        self,
        meal_dict: MealType,
        configs_path: Path,
        default_params_filepath: Optional[Path],
    ) -> None:
        """Generate the default parameters list.

        If a defaults path is passed in the meal, then it is used.
        If its value is None, then explicitly don't set up any defaults.
        If no defaults are passed in the meal, then the externally passed path is used.
        """
        if "defaults" in meal_dict.keys():
            defaults_value = meal_dict["defaults"]
            get_logger().debug(f"Using defaults from meal: {defaults_value}.")
            if defaults_value:
                defaults_path = Path(defaults_value)  # type: ignore
                # 'defaults' is guaranteed to be a string or None. Pathing errors will surface on access.
                # If a non-None defaults is passed,
                # if the path passed is not absolute, assume is relative to the menu folder
                if not defaults_path.is_absolute():
                    defaults_path = configs_path / defaults_path
                self.default_param_list = read_params(defaults_path)
            else:
                # If defaults is None, force an empty set.
                self.default_param_list = ParameterList()
        elif default_params_filepath:
            get_logger().debug(
                f"Using defaults externally passed: {default_params_filepath}."
            )
            self.default_param_list = read_params(default_params_filepath)
        else:
            get_logger().debug("Using empty defaults.")
            self.default_param_list = ParameterList()

    def load_base_parameters(self) -> None:
        """Load base parameter list."""
        if self.parent:
            # If a parent is specified, load their parameters
            self.param_list = self.parent.param_list
        else:
            # Otherwise use defaults
            self.param_list = self.default_param_list

    def decide_on_calibration(self, meal_dict: MealType) -> None:
        """Check if calibration data is to be preserved."""
        if "remove_calibration" in meal_dict.keys():
            self.remove_calibration_flag = meal_dict["remove_calibration"]  # type: ignore # Pydantic guarantees this is a bool
        elif self.parent is not None:
            # We assume that the parent has already removed calibration
            self.remove_calibration_flag = False

    def decide_on_operator(self, meal_dict: MealType) -> None:
        """Check if user data is to be preserved."""
        if "remove_operator" in meal_dict.keys():
            self.remove_operator_flag = meal_dict["remove_operator"]  # type: ignore # Pydantic guarantees this is a bool
        elif self.parent is not None:
            # We assume that the parent has already removed user data
            self.remove_operator_flag = False

    def collect_parameter_lists(
        self, modules_dict: Dict[str, Dish]
    ) -> Tuple[ParameterList, ParameterList, ParameterList]:
        """Parse all modules and collect edited, blacklisted and blacklisted groups parameters."""
        edited_param_list = ParameterList()
        black_param_list = ParameterList()
        black_group_list = ParameterList()

        for module in modules_dict.values():
            get_logger().debug(f"Examining params of module {module.name}/{module.sn}")
            for param in module.param_list:
                get_logger().debug(f"Adding parameter {param} to edited_param_list")
                edited_param_list.add_param(param, safe=False, overwrite=False)
            for param in module.black_params:
                get_logger().debug(f"Adding parameter {param} to black_param_list")
                black_param_list.add_param(param, safe=False, overwrite=False)
            for group in module.black_groups:
                get_logger().debug(f"Adding group {group} to black_group_list")
                black_group_list.add_param(group, safe=False, overwrite=False)

        return edited_param_list, black_param_list, black_group_list

    def remove_blacklist(
        self, black_param_list: ParameterList, black_group_list: ParameterList
    ) -> None:
        """Remove the blacklisted parameters from the recipe."""
        for param in self.param_list:
            if param.group and param.group in black_group_list:
                get_logger().debug(
                    f"Removing parameter {param} because its group is blacklisted."
                )
                self.param_list.remove_param(param)
            if param in black_param_list:
                get_logger().debug(
                    f"Removing parameter {param} because it is blacklisted."
                )
                self.param_list.remove_param(param)

    def remove_calibration(self) -> None:
        """Remove calibration parameter from the blacklist."""
        if self.remove_calibration_flag:
            get_logger().debug(f"Removing calibration for {self.name}")
            # Remove calibration values (need to keep their list up-to-date)
            filter_regex([s.name for s in Calibration()], self.param_list)

    def remove_operator(self) -> None:
        """Remove user data from the recipe."""
        if self.remove_operator_flag:
            get_logger().debug(f"Removing user data for {self.name}")
            # Remove user-defined values
            filter_regex([s.name for s in Operator()], self.param_list)

    def apply_edits(
        self,
        edited_param_list: ParameterList,
        default_params_filepath: Optional[Path],
    ) -> None:
        """Edit custom parameters."""
        if not self.add_new:
            # New parameters compared to default (or parent) set are not expected
            for parameter in edited_param_list:
                get_logger().debug(
                    f"Modifying parameter {parameter} from vehicle edit list"
                )
                self.param_list.add_param(parameter, safe=True)
        else:
            # New parameters are expected to be added, that don't exist in the original set.
            for param in edited_param_list:
                # Try to guess the new parameter type based on the default parameter set
                if param.param_type is None and param in self.default_param_list:
                    param.param_type = self.default_param_list[param.name].param_type

                get_logger().debug(
                    f"Adding parameter {param} from vehicle edit list to initial set"
                )
                self.param_list.add_param(param, safe=False)

    def collect_dishes(self, meal_dict: MealType) -> Dict[str, Dish]:
        """Collect all dishes from the configuration dict."""
        dishes_dict = dict()
        for dish_name in meal_dict.keys():
            # Do not parse staple dishes or options
            if (
                dish_name in ReservedOptionsSequence
                or dish_name in StapleDishesNamesSequence
            ):
                continue

            # Parse the model/serial-number designation
            dish_designation = meal_dict[dish_name]
            model: Optional[str]
            sn: Optional[str]
            if dish_designation is not None:
                model_sn = dish_designation.split("/")  # type: ignore # Pydantic guarantees this is a string
                model = model_sn[0]
                if len(model_sn) > 1:
                    sn = model_sn[1]
                else:
                    sn = None
            else:
                model = None
                sn = None

            # Edit configuration custom values
            get_logger().debug(f"Loading module {dish_name}/{model}/{sn}")
            dish = get_dish(ConfigPaths().custom_dishes, dish_name)
            dishes_dict[dish_name] = Dish(dish, model, sn)

        return dishes_dict

    def build_header_footer(
        self,
        boilerplate_model: BoilerplateText,
        variant_name: Optional[str],
        format_type: Formats,
    ) -> Generator[str, None, None]:
        """Grab the header and footer sections from the corresponding dish."""
        # Load common list
        get_logger().debug("Parsing common header/footer parameters")

        # Read text common across text_types
        common_text = boilerplate_model.common
        if common_text is not None:
            for row in common_text:
                yield row + "\n"

        # Read text specific to the text_type
        format_text = boilerplate_model.formats[format_type.value].common
        if format_text is not None:
            for row in format_text:
                yield row + "\n"

        # Read text specific to the meal
        if variant_name is not None:
            variants = boilerplate_model.formats[format_type.value].variants
            if variants is not None:
                meal_text = variants[variant_name].common
                for row in meal_text:  # type: ignore # Pydantic guarantees this is a List[str]
                    yield row + "\n"

    def __str__(self):
        """__str__ dunder method."""
        return self.param_list.__str__()

    def __contains__(self, item: Union[str, Parameter]) -> bool:
        """Answer if the Meal contains a parameter."""
        return self.param_list.__contains__(item)

    def retrieve_header_footer(
        self, option: str, fmt: Formats
    ) -> Generator[str, None, None]:
        """Retrieve a header or footer for a format export.

        INPUTS:
            option: "header" or "footer".
            fmt: String representation of one of export Formats.
        """
        # Return empty if the meal needs no header or footer.
        if option == "header" and not self.add_header:
            return
        if option == "footer" and not self.add_footer:
            return

        variant = getattr(self, option)
        get_logger().debug(
            f"Loading header/footer parameter {option}/{variant} for {fmt}."
        )
        model = get_boilerplate(ConfigPaths().staple_dishes, option)
        yield from self.build_header_footer(model, variant, fmt)  # noqa

    def export_to_px4(self) -> Generator[str, None, None]:
        """Export as PX4 parameter file."""
        # Read header
        yield from self.retrieve_header_footer("header", Formats.px4)

        param_hashes = sorted(self.param_list.keys())
        for param_hash in param_hashes:
            param_name = self.param_list[param_hash].name
            param_value = self.param_list[param_hash].get_pretty_value()
            internal_type = self.param_list[param_hash].param_type
            if internal_type == "FLOAT":
                param_type = 9
            elif internal_type == "INT32":
                param_type = 6
            else:
                raise TypeError(
                    f"Unknown parameter type {internal_type} for parameter {param_name}"
                )

            vid = self.param_list[param_hash].vid
            cid = self.param_list[param_hash].cid
            yield f"{vid}\t{cid}\t{param_name}\t{param_value}\t{param_type}\n"

    def export_to_px4af(self, version: int) -> Generator[str, None, None]:
        """PX4 airframe file build helper."""
        # Diversivy versions
        if version == 1:
            directive = "set"
            dish = Formats.px4afv1
        elif version == 2:
            directive = "set-default"
            dish = Formats.px4afv2
        else:
            raise ValueError(f"PX4 aiframe version {version} not supported.")

        # Read header
        yield from self.retrieve_header_footer("header", dish)

        if not self.is_sitl:
            indentation = "\t"
        else:
            indentation = ""

        param_hashes = sorted(self.param_list.keys())
        for param_hash in param_hashes:
            param_name = self.param_list[param_hash].name
            param_value = self.param_list[param_hash].get_pretty_value()

            yield f"{indentation}param {directive} {param_name} {param_value}\n"

        # Read footer
        yield from self.retrieve_header_footer("footer", dish)

    def export_to_px4afv1(self) -> Generator[str, None, None]:
        """Export as legacy PX4 airframe file.

        Utilizes the 'param set' directive.
        """
        yield from self.export_to_px4af(1)

    def export_to_px4afv2(self) -> Generator[str, None, None]:
        """Export as new-style PX4 airframe file.

        Utilizes the 'param set-default' directive.
        """
        yield from self.export_to_px4af(2)

    def export_to_csv(self) -> Generator[str, None, None]:
        """Export as csv file."""
        # Read header
        yield from self.retrieve_header_footer("header", Formats.csv)

        indentation = ""

        param_hashes = sorted(self.param_list.keys())
        for param_name in param_hashes:
            param_name = self.param_list[param_name].name
            param_value = self.param_list[param_name].get_pretty_value()

            yield f"{indentation}{param_name},{param_value}\n"

        # Read footer
        yield from self.retrieve_header_footer("footer", Formats.csv)

    def export_to_apm(
        self, include_readonly: bool = False
    ) -> Generator[str, None, None]:
        """Export as apm parameter file.

        INPUTS:
            include_readonly: flag to enable including @READONLY on a parameter.
                Necessary for apj tools, unsuitable for loading via a GCS.
        """
        # Read header
        yield from self.retrieve_header_footer("header", Formats.apm)

        indentation = ""

        param_hashes = sorted(self.param_list.keys())
        for param_name in param_hashes:
            param_name = self.param_list[param_name].name
            param_value = self.param_list[param_name].get_pretty_value()
            is_readonly = self.param_list[param_name].readonly
            if include_readonly and is_readonly:
                readonly_string = "\t@READONLY"
            else:
                readonly_string = ""

            yield f"{indentation}{param_name}\t{param_value}{readonly_string}\n"

        # Read footer
        yield from self.retrieve_header_footer("footer", Formats.apm)

    def apply_additions_px4(self) -> None:
        # Add the AUTOSTART value for each configuration
        autostart = Parameter("SYS_AUTOSTART", self.frame_id)
        autostart.param_type = "INT32"
        self.param_list.add_param(autostart, safe=(not self.add_new))

    def export(self, format: Formats) -> Iterable[str]:
        """Export general method."""
        # Perform format-related additions.
        if format == Formats.csv:
            return self.export_to_csv()
        elif format == Formats.px4:
            self.apply_additions_px4()
            return self.export_to_px4()
        elif format == Formats.px4afv1:
            self.apply_additions_px4()
            return self.export_to_px4afv1()
        elif format == Formats.px4afv2:
            self.apply_additions_px4()
            return self.export_to_px4afv2()
        elif format == Formats.apm:
            return self.export_to_apm(include_readonly=False)
        elif format == Formats.apj:
            return self.export_to_apm(include_readonly=True)
        else:
            raise ValueError(f"Output format {format} not supported.")


def build_meals(names: Optional[List[str]] = None) -> Dict[str, Meal]:
    """Build the meal of the provided aircraft."""
    meals_menu = get_meals_menu(ConfigPaths().meals)

    # Pick meal if specified
    if names is not None:
        meals_to_parse = names
    else:
        meals_to_parse = list(meals_menu.keys())

    # Go over the selected meals
    meals_dict = dict()
    for meal_name in meals_to_parse:
        if meal_name not in meals_menu.keys():
            raise KeyError(f"Meals Menu file does not contain: {meal_name}")
        default_params_filepath = ConfigPaths().default_parameters
        configs_path = ConfigPaths().path
        meals_dict[meal_name] = Meal(
            meals_menu, default_params_filepath, configs_path, meal_name
        )

    return meals_dict


def build_filename(format: Formats, meal: Meal) -> str:
    """Generate the output filename."""
    if format == Formats.csv:
        return f"{meal.name}.csv"
    elif format in (Formats.px4,):
        return f"{meal.name}.params"
    elif format == Formats.px4afv1 or format == Formats.px4afv2:
        filename = f"{meal.frame_id}_{meal.name}"
        if meal.is_hitl:
            filename += ".hil"
        return filename
    elif format in (Formats.apm, Formats.apj):
        return f"{meal.name}.param"
    else:
        raise ValueError(f"Unsupported format {format}")


def build_helper(
    meal_ordered: Optional[str],
    format: Formats,
    input_folder: Optional[str],
    default_params: Optional[str],
    output_folder: Optional[str] = None,
    sitl: bool = False,
) -> None:
    """Build parameter sets.

    Args:
        meal_ordered: Specify which meal should be built. All meals specified in the menu will be built if left None.
        format: The autopilot format to export as.
        input_folder: The directory where the Meals Menu is created.
        default_params: If set, this file will provide the full parameters set for all the Meals.
        output_folder: The directory where the meals will be exported.
        sitl: Filter for Meals marked as "sitl".
            None: Disregard this meal keyword.
            True: Only build "sitl" meals.
            False: Don't build "sitl" meals.

    Raises:
        ValueError: If *meal_ordered* is None (hence all the meals will be exported) but no *output_folder* is specified.
    """
    meal_list: Optional[List[str]]
    if meal_ordered is not None:
        meal_list = [meal_ordered]
    else:
        meal_list = None

    if input_folder:
        ConfigPaths().CUSTOM_PATH = Path(input_folder)
        get_logger().debug(f"Setting CUSTOM_PATH to {ConfigPaths().custom_dishes}")

    if default_params:
        ConfigPaths().DEFAULT_PARAMS_PATH = Path(default_params)
        get_logger().debug(
            f"Setting DEFAULT_PARAMS override to {ConfigPaths().default_parameters}"
        )

    get_logger().debug(f"Building configuration {meal_ordered} for format {format}")

    # Generate the meals
    meals_dict = build_meals(meal_list)

    # Write output files in selected output
    output_folder_path = convert_str_to_path(output_folder)

    if meal_list is None:
        # Export all meals
        if output_folder_path is None:
            raise ValueError(
                "You must specify an output folder for the meals parameters, see build command help"
            )
        for _, meal in meals_dict.items():
            # Skip config if sitl/non-sitl is requested
            if (sitl) and (not meal.is_sitl):
                continue
            if (not sitl) and meal.is_sitl:
                continue

            export_meal(meal, format, output_folder_path)
    else:
        # Export only a single config
        meal = meals_dict[meal_list[0]]
        export_meal(meal, format, output_folder_path)


def convert_str_to_path(path: Optional[str]) -> Optional[Path]:
    """Convert a str path representation to Optional[Path]."""
    if path:
        return Path(path)
    else:
        return None


def make_folder(folder_path: Path) -> None:
    """Create folder."""
    if not os.path.isabs(folder_path):
        folder_path = Path.cwd() / folder_path
    folder_path = folder_path.expanduser()

    if not os.path.exists(folder_path):
        try:
            os.mkdir(folder_path)
        except OSError:
            print("Failed to create folder")


def export_meal(config: Meal, format: Formats, output_path: Optional[Path]) -> None:
    """Export a configuration to a folder or the screen."""
    if output_path is not None:
        make_folder(output_path)
        filename = build_filename(format, config)

        with open(output_path / filename, "w") as fd:
            for row in config.export(format):
                fd.write(row)
    else:
        # Print configuration on the screen
        for row in config.export(format):
            print(row, end="")
