# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

autoclass_content = "both"  # include both class docstring and __init__
autodoc_default_options = {
        # Make sure that any autodoc declarations show the right members
        "members": True,
        # "inherited-members": True,
        "private-members": True,
        "show-inheritance": True,
}
autosummary_generate = True  # Make _autosummary files and include them
napoleon_numpy_docstring = False  # Force consistency, leave only Google
napoleon_use_rtype = False  # More legible

project = 'CSST Analyzer'
copyright = '2023, Joe Kern'
author = 'Joe Kern'
release = 'v1.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinxcontrib.napoleon',
              'sphinx.ext.autosummary', 'enum_tools.autoenum']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
