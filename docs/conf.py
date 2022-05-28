"""Sphinx configuration."""
from datetime import datetime


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
