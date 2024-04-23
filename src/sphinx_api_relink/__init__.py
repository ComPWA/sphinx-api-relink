# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import sphinx.domains.python
from docutils import nodes
from sphinx.addnodes import pending_xref, pending_xref_condition
from sphinx.ext.apidoc import main as sphinx_apidoc

from sphinx_api_relink.linkcode import get_linkcode_resolve

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

__SPHINX_VERSION = tuple(int(i) for i in version("sphinx").split(".") if i.isdigit())
if __SPHINX_VERSION < (7, 3):
    from sphinx.domains.python import parse_reftarget  # type:ignore[attr-defined]
else:
    from sphinx.domains.python._annotations import (  # type:ignore[import-not-found,no-redef]
        parse_reftarget,  # noqa: PLC2701
    )

if TYPE_CHECKING:
    from docutils.parsers.rst.states import Inliner
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import RoleFunction


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("api_github_repo", default=None, rebuild="env")
    app.add_config_value("api_linkcode_debug", default=False, rebuild="env")
    app.add_config_value("api_target_substitutions", default={}, rebuild="env")
    app.add_config_value("api_target_types", default={}, rebuild="env")
    app.add_config_value("generate_apidoc_directory", default="api", rebuild="env")
    app.add_config_value("generate_apidoc_excludes", default=None, rebuild="env")
    app.add_config_value("generate_apidoc_package_path", default=None, rebuild="env")
    app.add_config_value("generate_apidoc_use_compwa_template", True, rebuild="env")
    app.connect("config-inited", set_linkcode_resolve)
    app.connect("config-inited", generate_apidoc)
    app.connect("config-inited", replace_type_to_xref)
    app.add_role("wiki", wiki_role("https://en.wikipedia.org/wiki/%s"))
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def set_linkcode_resolve(app: Sphinx, _: BuildEnvironment) -> None:
    github_repo: str | None = app.config.api_github_repo
    if github_repo is None:
        return
    debug: bool = app.config.api_linkcode_debug
    app.config.linkcode_resolve = get_linkcode_resolve(github_repo, debug)  # type:ignore[attr-defined]
    app.setup_extension("sphinx.ext.linkcode")


def generate_apidoc(app: Sphinx, _: BuildEnvironment) -> None:
    config_key = "generate_apidoc_package_path"
    package_path: list[str] | str | None = getattr(app.config, config_key, None)
    if package_path is None:
        return
    apidoc_dir = Path(app.srcdir) / app.config.generate_apidoc_directory
    shutil.rmtree(apidoc_dir, ignore_errors=True)
    if isinstance(package_path, str):
        package_dirs = [package_path]
    else:
        package_dirs = package_path
    for rel_dir in package_dirs:
        abs_package_path = Path(app.srcdir) / rel_dir
        _run_sphinx_apidoc(
            abs_package_path,
            apidoc_dir,
            excludes=app.config.generate_apidoc_excludes,
            use_compwa_template=app.config.generate_apidoc_use_compwa_template,
        )


def _run_sphinx_apidoc(
    package_path: Path,
    apidoc_dir: str = "api",
    excludes: list[str] | None = None,
    use_compwa_template: bool = True,
) -> None:
    if not package_path.exists():
        msg = f"Package under {package_path} does not exist"
        raise FileNotFoundError(msg)
    args: list[str] = [str(package_path)]
    if excludes is None:
        excludes = []
    version_file = "version.py"
    if (package_path / version_file).exists():
        excludes.append(version_file)
    for file in excludes:
        excluded_path = package_path / file
        if not excluded_path.exists():
            msg = f"Excluded file {excluded_path} does not exist"
            raise FileNotFoundError(msg)
        args.append(str(package_path / file))
    args.extend(f"-o {apidoc_dir} --force --no-toc --separate".split())
    if use_compwa_template:
        template_dir = Path(__file__).parent / "templates"
        args.extend(f"--templatedir {template_dir}".split())
    sphinx_apidoc(args)


def replace_type_to_xref(app: Sphinx, _: BuildEnvironment) -> None:
    target_substitutions = _get_target_substitutions(app)
    ref_targets = {
        k: v if isinstance(v, str) else v[1] for k, v in target_substitutions.items()
    }
    ref_types = _get_target_types(app)
    ref_types.update({
        v[1]: v[0] for v in target_substitutions.values() if isinstance(v, tuple)
    })

    def _new_type_to_xref(
        target: str,
        env: BuildEnvironment | None = None,  # type:ignore[assignment]
        suppress_prefix: bool = False,
    ) -> pending_xref:
        reftype, target, title, refspecific = parse_reftarget(target, suppress_prefix)
        target = ref_targets.get(target, target)
        reftype = ref_types.get(target, reftype)
        if env is None:
            msg = "Environment cannot be None"
            raise TypeError(msg)
        return pending_xref(
            "",
            *_create_nodes(env, title),
            refdomain="py",
            reftype=reftype,
            reftarget=target,
            refspecific=refspecific,
            **_get_env_kwargs(env),
        )

    if __SPHINX_VERSION < (7, 3):
        sphinx.domains.python.type_to_xref = _new_type_to_xref  # pyright:ignore[reportPrivateImportUsage]
    else:
        sphinx.domains.python._annotations.type_to_xref = _new_type_to_xref


def _get_target_substitutions(app: Sphinx) -> dict[str, str | tuple[str, str]]:
    config_key = "api_target_substitutions"
    target_substitutions = getattr(app.config, config_key, {})
    if not isinstance(target_substitutions, dict):
        msg = f"{config_key} must be a dict, got {type(target_substitutions).__name__}"
        raise TypeError(msg)
    for k, v in target_substitutions.items():
        if not isinstance(k, str):
            msg = f"{config_key} keys must be str, got {type(k).__name__}"
            raise TypeError(msg)
        if not isinstance(v, (str, tuple)):
            msg = (
                f"{config_key} values must be str or a tuple, got"
                f" {type(v).__name__} for key {k!r}"
            )
            raise TypeError(msg)
        if isinstance(v, tuple) and len(v) != 2:  # noqa: PLR2004
            msg = (
                f"If dict values of {config_key} are a tuple, they must have length 2,"
                f" but got {len(v)} for key {k!r}"
            )
            raise TypeError(msg)
    return target_substitutions


def _get_target_types(app: Sphinx) -> dict[str, str]:
    config_key = "api_target_types"
    target_types = getattr(app.config, config_key, {})
    if not isinstance(target_types, dict):
        msg = f"{config_key} must be a dict, got {type(target_types).__name__}"
        raise TypeError(msg)
    for k, v in target_types.items():
        if not isinstance(k, str):
            msg = f"{config_key} keys must be str, got {type(k).__name__} for key {k!r}"
            raise TypeError(msg)
        if not isinstance(v, str):
            msg = (
                f"{config_key} values must be str, got {type(v).__name__} for key {k!r}"
            )
            raise TypeError(msg)
    return target_types


def _get_env_kwargs(env: BuildEnvironment) -> dict:
    if env:
        return {
            "py:module": env.ref_context.get("py:module"),
            "py:class": env.ref_context.get("py:class"),
        }
    return {}


def _create_nodes(env: BuildEnvironment, title: str) -> list[nodes.Node]:
    short_name = title.split(".")[-1]
    if env.config.python_use_unqualified_type_names:
        return [
            pending_xref_condition("", short_name, condition="resolved"),
            pending_xref_condition("", title, condition="*"),
        ]
    return [nodes.Text(short_name)]


def wiki_role(pattern: str) -> RoleFunction:
    def role(  # noqa: PLR0913, PLR0917
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options: dict | None = None,
        content: list[str] | None = None,
    ) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        output_text = text
        output_text = output_text.replace("_", " ")
        url = pattern % (text,)
        if options is None:
            options = {}
        reference_node = nodes.reference(rawtext, output_text, refuri=url, **options)
        return [reference_node], []

    return role  # type:ignore[return-value]
