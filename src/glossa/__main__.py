"""
Entry point for the `glossa` package, invoked as a module.

Usage
-----
To launch the command-line interface, execute::

    python -m glossa


See Also
--------
glossa.cli: Module implementing the application's command-line interface.
"""
from .cli import app

app()
