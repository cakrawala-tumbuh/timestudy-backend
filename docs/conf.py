"""Sphinx configuration for TimeStudy Backend documentation."""

# -- Project information -------------------------------------------------------
project = "TimeStudy Backend"
copyright = "2024, Andhitia Rama"
author = "Andhitia Rama"
release = "1.0.0"

# -- Extensions ----------------------------------------------------------------
extensions = [
    "sphinx.ext.napoleon",       # Google / NumPy docstring styles
    "sphinx.ext.viewcode",       # [source] links to highlighted source
    "sphinx.ext.intersphinx",    # cross-project links (Python, SQLAlchemy)
    "autoapi.extension",         # automatic API docs from source without import
    "myst_parser",               # write docs in Markdown
    "sphinx_copybutton",         # copy-button on code blocks
]

# -- sphinx-autoapi ------------------------------------------------------------
autoapi_dirs = ["../app"]
autoapi_type = "python"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_python_class_content = "both"   # include both class & __init__ docstrings
autoapi_member_order = "groupwise"
autoapi_add_toctree_entry = True

# -- Napoleon ------------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# -- Intersphinx ---------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.11", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# -- HTML output ---------------------------------------------------------------
html_theme = "furo"
html_title = "TimeStudy Backend"
html_short_title = "TimeStudy API"

html_theme_options = {
    "source_repository": "https://github.com/cakrawala-tumbuh/timestudy-backend",
    "source_branch": "master",
    "source_directory": "docs/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/cakrawala-tumbuh/timestudy-backend",
            "html": "",
            "class": "fa-brands fa-github fa-2x",
        },
    ],
}

# -- Source suffixes -----------------------------------------------------------
source_suffix = {
    ".rst": None,
    ".md": "myst_parser",
}
