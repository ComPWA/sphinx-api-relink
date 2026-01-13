# Helper tools for API linking

:::{title} Welcome
:::

This package provides helper tools and additional configuration options for the {mod}`~sphinx.ext.autodoc` and {mod}`~sphinx.ext.linkcode` Sphinx extensions. The {confval}`autodoc_type_aliases` configuration option does not always work well when using postponed evaluation of annotations ([PEP 563](https://peps.python.org/pep-0563)) or when importing through {obj}`typing.TYPE_CHECKING`, because {mod}`~sphinx.ext.autodoc` generates the API dynamically (not statically, as opposed to [`sphinx-autoapi`](https://github.com/readthedocs/sphinx-autoapi)).

## Installation

Just install through [PyPI](https://pypi.org) with `pip`:

```bash
pip install sphinx-api-relink
```

Next, in your {doc}`Sphinx configuration file <sphinx:usage/configuration>`, add `"sphinx_api_relink"` to your {confval}`extensions`:

```python
extensions = [
    "sphinx_api_relink",
]
```

## Generate API

To generate the API for [`sphinx.ext.autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html), specify the {confval}`generate_apidoc_package_path` in your {doc}`Sphinx configuration <sphinx:usage/configuration>`:

```python
generate_apidoc_package_path = "../src/my_package"  # relative to conf.py
```

Multiple packages can be listed as well:

```python
generate_apidoc_package_path = [
    "../src/package1",
    "../src/package2",
]
```

The API is generated with the same style used by the ComPWA repositories (see e.g. the {mod}`ampform` API). To use the default {mod}`~sphinx.ext.apidoc` template, set:

```python
generate_apidoc_use_compwa_template = False
```

:::{tip}
See the {doc}`API page <api/sphinx_api_relink>` for all configuration options and helper functions.
:::

## Relink type hints

There are two ways to relink type hint references in your API. The first one, {confval}`api_target_substitutions`, should be used when the target is different than the type hint itself:

```python
api_target_substitutions: dict[str, str | tuple[str, str]] = {
    "sp.Expr": "sympy.core.expr.Expr",
    "Protocol": ("obj", "typing.Protocol"),
}
```

The second, {confval}`api_target_types`, is useful when you want to redirect the reference **type** (see {doc}`sphinx:usage/domains/python`). This is for instance useful when Sphinx thinks the reference is a [`class`](https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-class), but it should be an [`obj`](https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-obj):

```python
api_target_types: dict[str, str] = {
    "RangeDefinition": "obj",
}
```

The extension can also link to the source code on GitHub through the [`sphinx.ext.linkcode`](https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html) extension. To activate, specify the GitHub organization and the repository name as follows:

```
api_github_repo: str = "ComPWA/sphinx-api-relink"
```

Set `api_linkcode_debug = True` to print the generated URLs to the console and `api_linkcode_rev = "main"` to disable determining the branch, tag, or commit SHA automatically.

## Developer installation

:::{include} ../CONTRIBUTING.md
:start-after: **[compwa.github.io/develop](https://compwa.github.io/develop)**!
:::

```{toctree}
:hidden:
API <api/sphinx_api_relink>
Changelog <https://github.com/ComPWA/sphinx-api-relink/releases>
Upcoming features <https://github.com/ComPWA/sphinx-api-relink/milestones?direction=asc&sort=title&state=open>
Help developing <https://compwa.github.io/develop>
```
