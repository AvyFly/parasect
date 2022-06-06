"""Sphinx configuration."""
from datetime import datetime
from pathlib import Path

from directory_tree import display_tree  # type: ignore

import parasect


project = "Parasect"
author = "George Zogopoulos"
copyright = f"{datetime.now().year}, Avy B.V."
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
]
autodoc_typehints = "description"
html_theme = "furo"

##############################################################################
# Build assets

# Build the Generic Meals
parasect_src_path = Path(__file__).parent.parent.resolve()
docs_assets_path = parasect_src_path / "docs" / "assets"
generic_menu_path = parasect_src_path / "tests" / "assets" / "generic" / "menu"
parasect.build(
    None,
    parasect.Formats("csv"),
    str(generic_menu_path),
    None,
    str(docs_assets_path / "generic_menu_csv"),
)

# Build Generic Meals directory tree
tree_string = display_tree(generic_menu_path, string_rep=True)
output_filepath = docs_assets_path / "generic_menu.inc"
with output_filepath.open("w") as f:
    f.write(tree_string)
