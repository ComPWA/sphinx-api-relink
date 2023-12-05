"""A linkcode resolver for using :code:`sphinx.ext.linkcode` with GitHub."""

from __future__ import annotations

import inspect
import subprocess
import sys
from functools import lru_cache
from os.path import dirname, relpath
from typing import TYPE_CHECKING, Any, Callable, TypedDict
from urllib.parse import quote

import requests
from colorama import Fore, Style

if TYPE_CHECKING:
    from types import ModuleType


class LinkcodeInfo(TypedDict, total=True):
    module: str
    fullname: str


def get_linkcode_resolve(
    github_repo: str, debug: bool
) -> Callable[[str, LinkcodeInfo], str | None]:
    def linkcode_resolve(domain: str, info: LinkcodeInfo) -> str | None:
        path = _get_path(domain, info, debug)
        if path is None:
            return None
        blob_url = get_blob_url(github_repo)
        if debug:
            msg = f"  {info['fullname']} --> {blob_url}/src/{path}"
            print_once(msg, color=Fore.BLUE)
        return f"{blob_url}/src/{path}"

    return linkcode_resolve


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


@lru_cache(maxsize=None)
def _get_package(module_name: str) -> ModuleType:
    package_name = module_name.split(".")[0]
    return __get_module(package_name)


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=1)
def get_blob_url(github_repo: str) -> str:
    ref = _get_commit_sha()
    repo_url = f"https://github.com/{github_repo}"
    blob_url = f"{repo_url}/blob/{ref}"
    if _url_exists(blob_url):
        return blob_url
    print_once(f"The URL {blob_url} seems not to exist", color=Fore.MAGENTA)
    tag = _get_latest_tag()
    if tag is not None:
        blob_url = f"{repo_url}/tree/{tag}"
        print_once(f"--> falling back to {blob_url}", color=Fore.MAGENTA)
        if _url_exists(blob_url):
            return blob_url
    blob_url = f"{repo_url}/tree/main"
    print_once(f"--> falling back to {blob_url}", color=Fore.MAGENTA)
    if _url_exists(blob_url):
        return blob_url
    blob_url = f"{repo_url}/tree/master"
    print_once(f"--> falling back to {blob_url}", color=Fore.MAGENTA)
    return blob_url


@lru_cache(maxsize=1)
def _get_commit_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S603, S607
        capture_output=True,
        check=True,
        text=True,
    )
    commit_hash = result.stdout.strip()
    return commit_hash[:7]


def _get_latest_tag() -> str | None:
    try:
        result = subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match"],  # noqa: S603, S607
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        return result.strip()
    except subprocess.CalledProcessError:
        return None


@lru_cache(maxsize=None)
def _url_exists(url: str) -> bool:
    try:
        response = requests.head(url)  # noqa: S113
        return response.status_code < 300  # noqa: PLR2004, TRY300
    except requests.RequestException:
        return False


@lru_cache(maxsize=None)
def print_once(message: str, *, color: str = Fore.RED) -> None:
    colored_text = f"{color}{message}{Style.RESET_ALL}"
    print(colored_text)  # noqa: T201
