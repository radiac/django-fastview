"""
Basic high-level checks on the JavaScript library
"""
import json
from pathlib import Path

import fastview


def test_major_minor_versions_match__patch_ignored():
    """
    Check the major and minor versions in both the Python and JavaScript packages match.

    This is a build check to ensure deployments on PyPI and npm stay in sync for
    ``major.minor`` releases (``major.minor.patch`` does not need to match).
    """
    # Get and sanity check the package.json path
    js_package_path = Path(fastview.__file__).parent.parent / "package.json"
    assert js_package_path.is_file()

    # Load and sanity check package.json
    js_package = json.loads(js_package_path.read_text())
    assert "version" in js_package

    # Drop the patch from the Collect the versions as ``[major, minor, patch`` arrays
    js_version = js_package["version"].rsplit(".", 1)[0]
    py_version = fastview.__version__.rsplit(".", 1)[0]

    assert js_version == py_version
