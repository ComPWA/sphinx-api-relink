"""A linkcode resolver for using :code:`sphinx.ext.linkcode` with GitHub."""

from __future__ import annotations

import inspect
import sys
from functools import cache
from os.path import dirname, relpath
from typing import TYPE_CHECKING, Any, TypedDict
from urllib.parse import quote

import requests
from colorama import Fore

from sphinx_api_relink.helpers import (
    _get_branch,
    _get_commit_sha,
    _get_latest_tag,
    print_once,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType


def get_linkcode_resolve(
    github_repo: str, *, debug: bool, rev: str | None = None
) -> Callable[[str, LinkcodeInfo], str | None]:
    """Get a :confval:`linkcode_resolve` function for the given :confval:`api_github_repo`."""

    def linkcode_resolve(domain: str, info: LinkcodeInfo) -> str | None:
        path = _get_path(domain, info, debug)
        if path is None:
            return None
        blob_url = get_blob_url(github_repo, rev=rev)
        if debug:
            msg = f"  {info['fullname']} --> {blob_url}/src/{path}"
            print_once(msg, color=Fore.BLUE)
        return f"{blob_url}/src/{path}"

    return linkcode_resolve


class LinkcodeInfo(TypedDict, total=True):
    """A `TypedDict` for the signature of the function given to :confval:`linkcode_resolve`."""

    module: str
    fullname: str


def _get_path(domain: str, info: LinkcodeInfo, debug: bool) -> str | None:
    obj = __get_object(domain, info)
    if obj is None:
        return None
    try:
        source_file = inspect.getsourcefile(obj)
    except TypeError:
        if debug:
            msg = f"  Cannot source file for {info['fullname']!r} of type {type(obj)}"
            print_once(msg, color=Fore.MAGENTA)
        return None
    if not source_file:
        return None

    module_name = info["module"]
    main_module_path = _get_package(module_name).__file__
    if main_module_path is None:
        msg = f"Could not find file for module {module_name!r}"
        raise ValueError(msg)
    path = quote(relpath(source_file, start=dirname(dirname(main_module_path))))
    source, start_lineno = inspect.getsourcelines(obj)
    end_lineno = start_lineno + len(source) - 1
    linenumbers = f"L{start_lineno}-L{end_lineno}"
    return f"{path}#{linenumbers}"


@cache
def _get_package(module_name: str) -> ModuleType:
    package_name = module_name.split(".", maxsplit=1)[0]
    return __get_module(package_name)


@cache
def __get_module(module_name: str) -> ModuleType:
    module = sys.modules.get(module_name)
    if module is None:
        msg = f"Could not find module {module_name!r}"
        raise ImportError(msg)
    return module


def __get_object(domain: str, info: LinkcodeInfo) -> Any | None:
    if domain != "py":
        print_once(f"Can't get the object for domain {domain!r}")
        return None

    module_name: str = info["module"]
    fullname: str = info["fullname"]

    obj = _get_object_from_module(module_name, fullname)
    if obj is None:
        print_once(f"Module {module_name} does not contain {fullname}")
        return None
    return inspect.unwrap(obj)


def _get_object_from_module(module_name: str, fullname: str) -> Any | None:
    module = __get_module(module_name)
    name_parts = fullname.split(".")
    if len(name_parts) == 1:
        return getattr(module, fullname, None)
    obj: Any = module
    for sub_attr in name_parts[:-1]:
        obj = getattr(obj, sub_attr, None)
    if obj is None:
        print_once(f"Module {module_name} does not contain {fullname}")
        return None
    return obj


@cache
def get_blob_url(github_repo: str, *, rev: str | None = None) -> str:
    """Get the base URL for blobs in the given GitHub repository.

    If :code:`rev` is provided, it is used directly. Otherwise, several attempts are
    made to determine a valid Git ref (commit SHA, tag, or branch) that exists in the
    repository.

    .. warning:: This function makes network requests to GitHub to verify the existence of URLs.
    """
    repo_url = f"https://github.com/{github_repo}"
    if rev:
        return f"{repo_url}/blob/{rev}"
    second_attempt = True
    previous_url = None
    url = f"{repo_url}/blob/main"
    for try_rev in [
        _get_commit_sha(),
        _get_latest_tag(),
        _get_branch(),
        "master",
        "main",
    ]:
        if try_rev is None:
            continue
        url = f"{repo_url}/blob/{try_rev}"
        if previous_url:
            if second_attempt:
                second_attempt = False
                msg = f"The URL {previous_url} seems not to exist"
                print_once(msg, color=Fore.MAGENTA)
            print_once(f"--> falling back to {url}", color=Fore.MAGENTA)
        if _url_exists(url):
            if previous_url:
                print_once(
                    "Disable this fallback behavior by specifying a branch, tag, or"
                    " commit SHA with the 'api_linkcode_rev' config value",
                    color=Fore.MAGENTA,
                )
            return url
        previous_url = url
    print_once(
        "Could not determine a valid Git rev for linkcode URLs. Disable this fallback"
        " behavior by specifying a branch, tag, or commit SHA with the"
        " 'api_linkcode_rev' config value in conf.py"
    )
    return url


@cache
def _url_exists(url: str) -> bool:
    try:
        response = requests.head(url, timeout=5)
        redirect_url = response.headers.get("Location")
        if redirect_url is None:
            return response.status_code < 400  # noqa: PLR2004
        return _url_exists(redirect_url)
    except requests.RequestException:
        return False
