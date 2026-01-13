from sphinx_api_relink.helpers import get_git_revision, get_package_version, pin

ORGANIZATION = "ComPWA"
REPO_NAME = "sphinx-api-relink"
PACKAGE_NAME = "sphinx_api_relink"
PACKAGE = "sphinx-api-relink"

add_module_names = False
api_github_repo = f"{ORGANIZATION}/{REPO_NAME}"
api_target_substitutions: dict[str, str | tuple[str, str]] = {
    "BuildEnvironment": "sphinx.environment.BuildEnvironment",
    "Sphinx": "sphinx.application.Sphinx",
}
author = "Common Partial Wave Analysis"
autodoc_default_options = {
    "exclude-members": "setup",
}
autodoc_member_order = "bysource"
autodoc_typehints_format = "short"
autosectionlabel_prefix_document = True
codeautolink_concat_default = True
copybutton_prompt_is_regexp = True
copybutton_prompt_text = r">>> |\.\.\. "  # doctest
copyright = "2026, Common Partial Wave Analysis"  # noqa: A001
default_role = "py:obj"
extensions = [
    "myst_parser",
    "sphinx_api_relink",
    "sphinx_codeautolink",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
]
generate_apidoc_package_path = f"../src/{PACKAGE_NAME}"
html_favicon = "_static/favicon.ico"
html_last_updated_fmt = "%-d %B %Y"
html_logo = (
    "https://raw.githubusercontent.com/ComPWA/ComPWA/04e5199/doc/images/logo.svg"
)
html_show_copyright = False
html_show_sourcelink = False
html_show_sphinx = False
html_sourcelink_suffix = ""
html_static_path = ["_static"]
html_theme = "sphinx_book_theme"
html_theme_options = {
    "icon_links": [
        {
            "name": "Common Partial Wave Analysis",
            "url": "https://compwa.github.io",
            "icon": "_static/favicon.ico",
            "type": "local",
        },
        {
            "name": "Source code",
            "url": f"https://github.com/{ORGANIZATION}/{REPO_NAME}",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": f"https://pypi.org/project/{PACKAGE}",
            "icon": "fa-brands fa-python",
        },
    ],
    "logo": {"text": REPO_NAME},
    "path_to_docs": "docs",
    "repository_branch": get_git_revision(prefer_branch=True),
    "repository_url": f"https://github.com/{ORGANIZATION}/{REPO_NAME}",
    "show_navbar_depth": 2,
    "show_toc_level": 2,
    "use_download_button": False,
    "use_edit_page_button": True,
    "use_fullscreen_button": False,
    "use_issues_button": True,
    "use_repository_button": True,
    "use_source_button": True,
}
html_title = REPO_NAME
intersphinx_mapping = {
    "ampform": ("https://ampform.readthedocs.io/stable", None),
    "myst_nb": (f"https://myst-nb.readthedocs.io/en/{pin('myst-nb')}", None),
    "python": ("https://docs.python.org/3", None),
    "readthedocs": ("https://docs.readthedocs.com/platform/stable", None),
    "sphinx_book_theme": ("https://sphinx-book-theme.readthedocs.io/en/stable", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}
myst_enable_extensions = ["colon_fence"]
nitpick_ignore = [
    ("py:class", "RoleFunction"),
]
nitpicky = True
primary_domain = "py"
project = PACKAGE_NAME
release = get_package_version(PACKAGE_NAME)
version = get_package_version(PACKAGE_NAME)
