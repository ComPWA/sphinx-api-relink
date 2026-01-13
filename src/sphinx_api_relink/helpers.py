"""Helper functions for your :file:`conf.py` Sphinx configuration file.

To have interlinked APIs that remain correct in older versions of your documentation
(see :doc:`versioning on Read the Docs <readthedocs:versions>`), it is important to link
against pinned versions of external packages. Many of these functions are useful for the
configuration options of the :mod:`~sphinx.ext.intersphinx` extension.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from functools import cache, lru_cache
from importlib.metadata import PackageNotFoundError, version

from colorama import Fore, Style

__DEFAULT_BRANCH = "main"
__VERSION_REMAPPING: dict[str, dict[str, str]] = {}


def get_branch_name() -> str:
    """Get the branch name from the environment in a CI job.

    See :envvar:`READTHEDOCS_VERSION` and `GITHUB_REF
    <https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#github-context>`_
    on GitHub Docs.

    .. seealso:: :func:`get_git_revision` for a more robust alternative that also works locally.
    """
    branch_name = os.environ.get("READTHEDOCS_VERSION")
    if branch_name == "latest":
        return __DEFAULT_BRANCH
    if branch_name is None:
        branch_name = os.environ.get("GITHUB_REF", __DEFAULT_BRANCH)
        branch_name = branch_name.replace("refs/heads/", "")
        branch_name = branch_name.replace("refs/pull/", "")
        branch_name = branch_name.replace("refs/tags/", "")
        if re.match(r"^\d+/[a-z]+$", branch_name) is not None:
            branch_name = __DEFAULT_BRANCH  # PR preview
    print_once(f"Linking pages to this Git ref: {branch_name}", color=Fore.MAGENTA)
    return branch_name


def get_execution_mode() -> str:
    """Get the Jupyter notebook execution mode from environment variables.

    Returns ``"force"`` if the ``FORCE_EXECUTE_NB`` environment variable is set,
    ``"cache"`` if the ``EXECUTE_NB`` environment variable is set, and ``"off"``
    otherwise. You can use this to set the :doc:`nb_execution_mode
    <myst_nb:configuration>` option for the :doc:`MyST-NB <myst_nb:index>` package.

    .. code-block:: python

        from sphinx_api_relink.helpers import get_execution_mode

        nb_execution_mode = get_execution_mode()
    """
    if "FORCE_EXECUTE_NB" in os.environ:
        print("\033[93;1mWill run ALL Jupyter notebooks!\033[0m")  # noqa: T201
        return "force"
    if "EXECUTE_NB" in os.environ:
        return "cache"
    return "off"


def get_git_revision(*, prefer_branch: bool = False) -> str:
    """Get the current Git revision (branch, tag, or commit SHA) in your local repository.

    This is a more robust alternative to :func:`get_branch_name` that also works locally
    or with private GitHub repositories. It can for instance be used to set the
    :confval:`api_linkcode_rev` option.

    .. code-block:: python

        from sphinx_api_relink.helpers import get_git_revision

        api_linkcode_rev = get_git_revision()

    Another example is to use this function to set the :ref:`repository_branch
    <sphinx_book_theme:source-buttons:source>` option of the :doc:`Sphinx Book Theme
    <sphinx_book_theme:index>`.

    .. code-block:: python

        from sphinx_api_relink.helpers import get_git_revision

        html_theme_options = {
            "repository_branch": get_git_revision(prefer_branch=True),
            "use_edit_page_button": True,
        }

    :param prefer_branch:

        If `True`, return the current branch name if no tag is found. If `False`, return
        the commit SHA if no tag is found. In the :confval:`html_theme_options` example
        above, we chose to prefer the branch name, because that makes more sense for
        editing pages on GitHub.

        .. seealso:: https://github.com/ComPWA/sphinx-api-relink/issues/22
    """
    tag = _get_latest_tag()
    if tag is not None:
        return tag
    if prefer_branch:
        branch = _get_branch()
        if branch is not None:
            return branch
    return _get_commit_sha()


def _get_branch() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    )
    branch_name = result.stdout.strip()
    if branch_name == "HEAD":
        return None
    return branch_name


@lru_cache(maxsize=1)
def _get_commit_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    )
    commit_hash = result.stdout.strip()
    return commit_hash[:7]


def _get_latest_tag() -> str | None:
    try:
        result = subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match"],  # noqa: S607
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        return result.strip()
    except subprocess.CalledProcessError:
        return None


def get_package_version(package_name: str) -> str:
    """Get the version of a Python package using :func:`importlib.metadata.version`.

    The version is returned in the full MAJOR.MINOR.PATCH format.

    .. code-block:: python

        from sphinx_api_relink.helpers import get_package_version

        version = get_package_version("sphinx-api-relink")
    """
    v = version(package_name)
    return ".".join(v.split(".")[:3])


def pin(package_name: str) -> str:
    """Get the version number of a package based on constraints or installed version.

    This is useful when setting the :confval:`intersphinx_mapping` in your :doc:`Sphinx
    configuration <sphinx:usage/configuration>`:

    .. code-block:: python

        from sphinx_api_relink.helpers import pin

        intersphinx_mapping = {
            "attrs": (f"https://www.attrs.org/en/{pin('attrs')}", None),
        }
    """
    package_name = package_name.lower()
    installed_version = _get_version_from_constraints(package_name)
    if installed_version is None:
        try:
            installed_version = version(package_name)
        except PackageNotFoundError:
            return "stable"
    return _remap_version(package_name, installed_version)


def _remap_version(package: str, version: str) -> str:
    remapping = __VERSION_REMAPPING.get(package, {})
    for pattern, replacement in remapping.items():
        if re.match(pattern, version):
            return replacement
    return remapping.get(version, version)


def _get_version_from_constraints(package_name: str) -> str | None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    constraints_path = f"../.constraints/py{python_version}.txt"
    if not os.path.exists(constraints_path):
        return None
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
        return installed_version.strip()
    return None


def pin_minor(package_name: str) -> str:
    """Get the version of a package with only the MAJOR.MINOR components.

    Some packages use documentation URLs that only specify the MAJOR.MINOR version. An
    example is the NumPy API (e.g. https://numpy.org/doc/1.24).

    .. code-block:: python

        from sphinx_api_relink.helpers import pin_minor

        intersphinx_mapping = {
            "numpy": (f"https://numpy.org/doc/{pin_minor('numpy')}", None),
        }
    """
    installed_version = pin(package_name)
    if installed_version == "stable":
        return installed_version
    matches = re.match(r"^([0-9]+\.[0-9]+).*$", installed_version)
    if matches is None:
        msg = f"Could not find documentation for {package_name} v{installed_version}"
        raise ValueError(msg)
    return matches[1]


def set_intersphinx_version_remapping(
    version_remapping: dict[str, dict[str, str]],
) -> None:
    """Remap versions returned by the :func:`pin` and :func:`pin_minor` functions.

    Since the :func:`pin` and :func:`pin_minor` functions return the installed version
    of a package, it may be necessary to remap certain versions to match the versions
    used in the documentation URLs of external packages, in particular when those
    packages have not yet released the API website for a specific release.

    This function has to be called in the :file:`conf.py` file before using the
    :func:`pin` and :func:`pin_minor` functions.

    .. code-block:: python


        from sphinx_api_relink.helpers import set_intersphinx_version_remapping

        set_intersphinx_version_remapping({
            "ipython": {
                "8.12.2": "8.12.1",
                "8.12.3": "8.12.1",
            },
            "ampform": {"0.15.12.dev.*": "0.15.11"},
        })

    """
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


@cache
def print_once(message: str, *, color: str = Fore.RED) -> None:
    """Prints a message to the console only once, with optional color formatting.

    Colors can be specified using ANSI escape codes from the
    https://github.com/tartley/colorama library. The default color is red.

    .. code-block:: python

        from colorama import Fore
        from sphinx_api_relink.helpers import print_once

        print_once("This is an important message!", color=Fore.GREEN)
    """
    colored_text = f"{color}{message}{Style.RESET_ALL}"
    print(colored_text)  # noqa: T201
