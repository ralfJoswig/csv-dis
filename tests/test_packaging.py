from __future__ import annotations

import ctypes
import os
import struct
import sys
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_EXE = _ROOT / "dist" / "csv-dis" / "csv-dis.exe"


def _load(name: str, path: Path) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def build() -> ModuleType:
    return _load("build_exe", _ROOT / "tools" / "build_exe.py")


def test_build_embeds_icon_and_package_data(build: ModuleType) -> None:
    args = build.build_arguments()
    icon = build.ICON
    assert icon.exists()
    assert args[args.index("--name") + 1] == "csv-dis"
    assert args[args.index("--icon") + 1] == str(icon)
    assert "--windowed" in args
    assert args[args.index("--paths") + 1] == str(build.SRC)

    source, target = args[args.index("--add-data") + 1].split(os.pathsep)
    assert Path(source) == icon
    assert target == f"csv_dis{os.sep}assets"


def test_build_entry_point_exposes_main(build: ModuleType) -> None:
    assert build.ENTRY.exists()
    launcher = _load("launcher", build.ENTRY)
    from csv_dis.app import main

    assert launcher.main is main


def test_build_target_is_in_dist(build: ModuleType) -> None:
    assert build.executable() == _EXE
    assert build.DIST == _ROOT / "dist"


def test_build_copies_license_files(build: ModuleType) -> None:
    assert build.LICENSE_FILES == ("LICENSE", "THIRD-PARTY-NOTICES.md")
    for name in build.LICENSE_FILES:
        assert (_ROOT / name).is_file()
        if _EXE.exists():
            assert (build.DIST / build.NAME / name).is_file()


def test_pyproject_dev_dependencies_include_pyinstaller() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = data["project"]["optional-dependencies"]["dev"]
    assert any(entry.lower().startswith("pyinstaller") for entry in dev)


@pytest.mark.skipif(sys.platform != "win32", reason="nur unter Windows")
def test_app_user_model_id_is_set() -> None:
    from csv_dis.app import APP_USER_MODEL_ID, _set_app_user_model_id

    _set_app_user_model_id()
    shell32 = ctypes.windll.shell32

    def get() -> str:
        value = ctypes.c_wchar_p()
        assert (
            shell32.GetCurrentProcessExplicitAppUserModelID(ctypes.byref(value)) == 0
        )
        return value.value or ""

    assert get() == APP_USER_MODEL_ID


@pytest.mark.skipif(
    not _EXE.exists(), reason="dist/csv-dis/csv-dis.exe ist nicht gebaut"
)
def test_built_executable_is_gui_with_icons() -> None:
    data = _EXE.read_bytes()
    header = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[header : header + 4] == b"PE\0\0"
    optional = header + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    assert magic in (0x10B, 0x20B)
    subsystem = struct.unpack_from("<H", data, optional + 68)[0]
    assert subsystem == 2  # WINDOWS_GUI, kein Konsolenfenster

    shell32 = ctypes.windll.shell32
    count = shell32.ExtractIconExW(str(_EXE), -1, None, None, 0)
    assert count >= 1
