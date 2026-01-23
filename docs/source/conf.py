# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import pathlib
from docutils import nodes

# Add the project's `src` directory to sys.path for autodoc.
# Resolve relative to this file so Sphinx works regardless of CWD.
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str((HERE / ".." / ".." / "src").resolve()))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ALY"
copyright = "2025-2026, Mohamed Aly"
author = "Mohamed Aly"
release = "1.0.0"
version = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Auto-generate docs from docstrings
    "sphinx.ext.autosummary",  # Summary tables for autodoc
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.napoleon",  # Support Google/NumPy docstrings
    "sphinx.ext.intersphinx",  # Link to other Sphinx docs
    "sphinx.ext.graphviz",  # Graphviz diagrams
    "sphinxcontrib.plantuml",  # PlantUML diagrams
    "sphinx.ext.todo",  # TODO directives
    "sphinx.ext.mathjax",  # Math rendering
    "sphinx.ext.ifconfig",  # Conditional content
]

# Autodoc settings
autodoc_default_options = {
    # Do not expand `members`/`undoc-members` globally; keep defaults minimal
    "member-order": "bysource",
    "special-members": "__init__",
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_class_signature = "separated"

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = []


# -- Graphviz configuration --------------------------------------------------
graphviz_output_format = "svg"
graphviz_dot_args = [
    "-Nfontname=sans-serif",
    "-Efontname=sans-serif",
    "-Gfontname=sans-serif",
]

# -- PlantUML configuration --------------------------------------------------
# PlantUML configuration
# Check for plantuml.jar in multiple locations
import shutil

# Check if Java is available
java_available = shutil.which("java") is not None

# Look for plantuml.jar in multiple locations
plantuml_jar_locations = [
    os.path.join(os.path.dirname(__file__), "plantuml.jar"),  # docs/source/
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "plantuml.jar"),  # docs/
]

plantuml_jar_path = None
for path in plantuml_jar_locations:
    if os.path.exists(path):
        plantuml_jar_path = path
        break

if plantuml_jar_path and java_available:
    # Use local PlantUML jar
    plantuml = f'java -jar "{plantuml_jar_path}"'
    print(f"Using local PlantUML: {plantuml}")
else:
    # Fallback
    plantuml = "java -jar plantuml.jar"
    if not java_available:
        print("WARNING: Java not found. PlantUML diagrams may not render.")
        print("To fix: Install Java or download plantuml.jar to docs/")
    elif not plantuml_jar_path:
        print("WARNING: plantuml.jar not found. PlantUML diagrams may not render.")
        print("To fix: Download plantuml.jar to docs/ or docs/source/")

plantuml_output_format = "svg"
plantuml_latex_output_format = "pdf"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"  # ReadTheDocs theme for better appearance
html_static_path = ["_static"]
html_css_files = ['static.css']
html_logo = None
html_title = "ALY Tool Documentation"

# Theme options
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "titles_only": False,
}


# -- Options for LaTeX output ------------------------------------------------
latex_engine = "xelatex"
latex_toplevel_sectioning = "section"

latex_elements = {
    "papersize": "a4paper",
    "pointsize": "12pt",

    # Clean, consistent fonts (Latin Modern)
    "fontpkg": r"""
\usepackage{fontspec}
\defaultfontfeatures{Scale=MatchLowercase,Ligatures=TeX}
\setmainfont{Latin Modern Roman}
\setsansfont{Latin Modern Sans}
\setmonofont{Latin Modern Mono}[Scale=0.9]
""",

    "preamble": r"""
% --- Unicode helpers ---
\usepackage{newunicodechar}
\newunicodechar{‾}{\textasciimacron}
\newunicodechar{θ}{\ensuremath{\theta}}

% Box-drawing characters via a font that actually has them (Consolas on Windows)
\newfontfamily\BoxDrawingFont{Consolas}
\newunicodechar{─}{{\BoxDrawingFont ─}}
\newunicodechar{│}{{\BoxDrawingFont │}}
\newunicodechar{┌}{{\BoxDrawingFont ┌}}
\newunicodechar{┐}{{\BoxDrawingFont ┐}}
\newunicodechar{└}{{\BoxDrawingFont └}}
\newunicodechar{┘}{{\BoxDrawingFont ┘}}
\newunicodechar{├}{{\BoxDrawingFont ├}}
\newunicodechar{┤}{{\BoxDrawingFont ┤}}
\newunicodechar{┬}{{\BoxDrawingFont ┬}}
\newunicodechar{┴}{{\BoxDrawingFont ┴}}
\newunicodechar{┼}{{\BoxDrawingFont ┼}}
\newunicodechar{═}{{\BoxDrawingFont ═}}
\newunicodechar{║}{{\BoxDrawingFont ║}}

% --- Figures: keep them near where they’re defined ---
\usepackage{float}
\floatplacement{figure}{H}

% --- Code blocks: avoid ugly page breaks ---
\usepackage{etoolbox}
\usepackage{needspace}
\makeatletter
% Reserve about 3 lines of space before a Sphinx verbatim block
\preto{\sphinxVerbatim}{\Needspace{3\baselineskip}}

% Force new page at each \section
\preto\section{\clearpage}
% For \subsection, only start a new page if there isn't enough space remaining
\preto\subsection{\Needspace{3\baselineskip}}

% Helper: keep a short paragraph together with the following block.
% Use in RST before the paragraph you want to move together with the next block:
% .. raw:: latex
% 
%    \KeepWithNext{3\baselineskip}
\newcommand{\KeepWithNext}[1]{\Needspace{#1}}
\makeatother

% Reduce vertical stretching that causes awkward breaks
\raggedbottom

% Improve widow/orphan control
\widowpenalty=10000
\clubpenalty=10000

% --- Layout tweaks ---
\usepackage{ragged2e}
% Uncomment if you like ragged right:
% \raggedright

\setlength{\headheight}{15pt} % fix fancyhdr warnings
""",

    "babel": r"\usepackage[english]{babel}",
    "fncychap": "",
    "extraclassoptions": "openany,oneside",
}



latex_documents = [
    (
        "index",
        "ALY-Advanced-Logic-Yieldflow.tex",
        "ALY (Advanced Logic Yieldflow)",
        "Mohamed",
        "manual",
    ),
]

# -- Options for manual page output ------------------------------------------
man_pages = [("index", "aly", "ALY (Advanced Logic Yieldflow)", [author], 1)]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (
        "index",
        "ALY-Advanced-Logic-Yieldflow",
        "ALY (Advanced Logic Yieldflow)",
        author,
        "ALY-Advanced-Logic-Yieldflow",
        "Implementation specification for ALY (Advanced Logic Yieldflow).",
        "Miscellaneous",
    ),
]

# Numbering
numfig = True
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
    "code-block": "Listing %s",
    "section": "Section %s",
}
