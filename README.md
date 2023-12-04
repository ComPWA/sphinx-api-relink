# PDG role for Sphinx

[![PyPI package](https://badge.fury.io/py/sphinx-api-relink.svg)](https://pypi.org/project/sphinx-api-relink)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/sphinx-api-relink)](https://pypi.org/project/sphinx-api-relink)
[![BSD 3-Clause license](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Open in Visual Studio Code](https://img.shields.io/badge/vscode-open-blue?logo=visualstudiocode)](https://open.vscode.dev/ComPWA/sphinx-api-relink)
[![CI status](https://github.com/ComPWA/sphinx-api-relink/workflows/CI/badge.svg)](https://github.com/ComPWA/sphinx-api-relink/actions?query=branch%3Amain+workflow%3ACI)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy.readthedocs.io)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ComPWA/sphinx-api-relink/main.svg)](https://results.pre-commit.ci/latest/github/ComPWA/sphinx-api-relink/main)
[![Spelling checked](https://img.shields.io/badge/cspell-checked-brightgreen.svg)](https://github.com/streetsidesoftware/cspell/tree/master/packages/cspell)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This package is a plugin for the [`sphinx.ext.autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) extension. The [`autodoc_type_aliases`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_type_aliases) configuration does not always work well when using postponed evaluation of annotations ([PEP 563](https://peps.python.org/pep-0563), i.e. `from __future__ import annotations`) or when importing through [`typing.TYPE_CHECKING`](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING), because `sphinx.ext.autodoc` generates the API dynamically (not statically, as opposed to [`sphinx-autoapi`](https://github.com/readthedocs/sphinx-autoapi)).

## Installation

Just install through [PyPI](https://pypi.org) with `pip`:

```bash
pip install sphinx-api-relink
```

Next, in your [Sphinx configuration file](https://www.sphinx-doc.org/en/master/usage/configuration.html) (`conf.py`), add `"sphinx_api_relink"` to your `extensions`:

```python
extensions = [
    "sphinx_api_relink",
]
```

## Usage

There are two ways to relink type hint references in your API. The first one, **`api_target_substitutions`**, should be used when the target is different than the type hint itself:

```python
api_target_substitutions: dict[str, str | tuple[str, str]] = {
    "sp.Expr": "sympy.core.expr.Expr",
    "Protocol": ("obj", "typing.Protocol"),
}
```

The second, **`api_target_types`**, is useful when you want to redirect the reference **type**. This is for instance useful when Sphinx thinks the reference is a [`class`](https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-class), but it should be an [`obj`](https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-obj):

```python
api_target_types: dict[str, str] = {
    "RangeDefinition": "obj",
}
```

## Generate API

To generate the API for [`sphinx.ext.autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html), add this to your `conf.py`:

```python
api_package_path = "../src/my_package"  # relative to conf.py
```

The API is generated with the same style used by the ComPWA repositories (see e.g. [ampform.rtfd.io/en/stable/api/ampform.html](https://ampform.readthedocs.io/en/stable/api/ampform.html)). To use the default template, set:

```python
generate_apidoc_use_compwa_template = False
```

Other configuration values (with their defaults):

```python
generate_apidoc_directory = "api"
generate_apidoc_excludes = ["version.py"]
```
