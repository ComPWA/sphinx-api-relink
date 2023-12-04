"""Helper functions for your :file:`conf.py` Sphinx configuration file."""

# pyright: reportUnnecessaryIsInstance=false
from __future__ import annotations

import os
import re
import sys

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

__VERSION_REMAPPING: dict[str, dict[str, str]] = {}


def get_branch_name() -> str:
    """Get the branch name from the environment for Read the Docs.

    See https://docs.readthedocs.io/en/stable/builds.html.
    """
    branch_name = os.environ.get("READTHEDOCS_VERSION", "stable")
    if branch_name == "latest":
        return "main"
    if re.match(r"^\d+$", branch_name):  # PR preview
        return "stable"
    return branch_name


def get_execution_mode() -> str:
    if "FORCE_EXECUTE_NB" in os.environ:
        print("\033[93;1mWill run ALL Jupyter notebooks!\033[0m")  # noqa: T201
        return "force"
    if "EXECUTE_NB" in os.environ:
        return "cache"
    return "off"


def get_package_version(package_name: str) -> str:
    """Get the version (MAJOR.MINOR.PATCH) of a Python package."""
    v = version(package_name)
    return ".".join(v.split(".")[:3])


def pin(
    package_name: str, version_remapping: dict[str, dict[str, str]] | None = None
) -> str:
    if version_remapping is None:
        version_remapping = __VERSION_REMAPPING
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    constraints_path = f"../.constraints/py{python_version}.txt"
    if not os.path.exists(constraints_path):
        msg = (
            f"Could not find {constraints_path}. Did you pin your constraints with"
            " https://github.com/ComPWA/update-pip-constraints?"
        )
        raise FileNotFoundError(msg)
    with open(constraints_path) as stream:
        constraints = stream.read()
    package_name = package_name.lower()
    for line in constraints.split("\n"):
        line = line.split("#")[0]  # remove comments
        line = line.strip()
        line = line.lower()
        if not line.startswith(package_name):
            continue
        if not line:
            continue
        line_segments = tuple(line.split("=="))
        if len(line_segments) != 2:  # noqa: PLR2004
            continue
        _, installed_version, *_ = line_segments
        installed_version = installed_version.strip()
        remapped_versions = version_remapping.get(package_name)
        if remapped_versions is not None:
            existing_version = remapped_versions.get(installed_version)
            if existing_version is not None:
                return existing_version
        return installed_version
    return "stable"


def pin_minor(package_name: str) -> str:
    installed_version = pin(package_name)
    if installed_version == "stable":
        return installed_version
    matches = re.match(r"^([0-9]+\.[0-9]+).*$", installed_version)
    if matches is None:
        msg = f"Could not find documentation for {package_name} v{installed_version}"
        raise ValueError(msg)
    return matches[1]


def set_intersphinx_version_remapping(
    version_remapping: dict[str, dict[str, str]]
) -> None:
    if not isinstance(version_remapping, dict):
        msg = (
            "intersphinx_relink_versions must be a dict, got a"
            f" {type(version_remapping).__name__}"
        )
        raise TypeError(msg)
    for k, v in version_remapping.items():
        if not isinstance(k, str):
            msg = (
                "intersphinx_relink_versions keys must be str,"
                f" got a {type(k).__name__}"
            )
            raise TypeError(msg)
        if not isinstance(v, dict):
            msg = (
                "intersphinx_relink_versions values must be dict,"
                f" got a {type(v).__name__}"
            )
            raise TypeError(msg)
        for k2, v2 in v.items():
            if not isinstance(k2, str):
                msg = (
                    "intersphinx_relink_versions values must be dict[str, str],"
                    f" got a {type(k2).__name__}"
                )
                raise TypeError(msg)
            if not isinstance(v2, str):
                msg = (
                    "intersphinx_relink_versions values must be dict[str, str],"
                    f" got a {type(v2).__name__}"
                )
                raise TypeError(msg)
    __VERSION_REMAPPING.update(version_remapping)
