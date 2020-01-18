"""
Update migration on the test app

Helper for use during development, when making changes to the models in the test app.

The existing migration is removed to speed and simplify tests. Ensure tests are always
run on a clean database.

Invoke with::

    python tests/makemigrations.py
"""
import shutil
from pathlib import Path

from django.core import management

from tests.conftest import pytest_configure


if __name__ == "__main__":
    shutil.rmtree(Path("tests/app/migrations"))
    pytest_configure()
    management.call_command("makemigrations", "app")
