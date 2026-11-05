"""Einstiegspunkt der Anwendung."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from . import __version__
from .main_window import MainWindow
from .resources import app_icon
from .splash import SPLASH_MIN_MS, create_splash

APP_USER_MODEL_ID = "RalfJoswig.csv-dis"


def _set_app_user_model_id() -> None:
    """Eigene App-ID, damit Windows Fenster und Icon zusammenhält."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )
    except (AttributeError, OSError):
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    _set_app_user_model_id()
    app = QApplication(args)
    app.setApplicationName("csv-dis")
    app.setApplicationDisplayName("csv-dis")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())

    splash = create_splash(__version__)
    splash.show()
    app.processEvents()

    window = MainWindow()
    window.show()

    path = Path(args[1]) if len(args) > 1 else None

    def finish_startup() -> None:
        splash.finish(window)
        splash.deleteLater()
        if path is not None:
            window.open_path(path)

    # Erst nach dem Splash laden, damit sich Splash und Fortschrittsdialog
    # nicht überlagern.
    QTimer.singleShot(SPLASH_MIN_MS, finish_startup)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
