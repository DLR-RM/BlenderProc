import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
sys.path.append(os.path.abspath("./ext"))
from blenderproc.version import __version__

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'BlenderProc'
copyright = '2023, DLR RMC'
author = 'DLR RMC'
release = '2023'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.intersphinx',
    'sphinx.ext.imgmath',
    'sphinx.ext.viewcode',
    'moduleoverview',
    'sphinx_rtd_theme',
    'm2r2'
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = ['.rst', '.md']
release = __version__
version = __version__



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'display_version': True
}
html_static_path = ['_static']
html_css_files = [
    'css/theme_overrides.css',
]
html_sidebars = {
    '**': [
        'localtoc.html',
    ]
}