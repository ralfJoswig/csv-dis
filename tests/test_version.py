from __future__ import annotations

import re
import tomllib
from importlib.metadata import version as package_version
from pathlib import Path

from csv_dis import __version__

_ROOT = Path(__file__).resolve().parents[1]


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
    assert __version__ == "1.1.0"


def test_installed_metadata_matches_package() -> None:
    assert package_version("csv-dis") == __version__


def test_pyproject_reads_version_from_package() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert "version" not in project
    assert project["dynamic"] == ["version"]
    dynamic = data["tool"]["setuptools"]["dynamic"]
    assert dynamic["version"] == {"attr": "csv_dis.__version__"}


def test_license_files_are_present() -> None:
    license_text = (_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3" in license_text

    notices = (_ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
    for fragment in ("GPL-3.0-only", "LGPLv3", "MIT", "PSF"):
        assert fragment in notices
