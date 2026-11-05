"""Dialog für den Filter einer einzelnen Spalte."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from .column_types import ColumnType, column_type_label
from .query import (
    Filter,
    FilterOperator,
    QueryError,
    build_filter_expr,
    needs_value,
    operator_label,
    operators_for,
)


class FilterDialog(QDialog):
    """Popup mit Operator und Wert; ungültige Eingaben werden markiert."""

    def __init__(
        self,
        column: str,
        column_type: ColumnType,
        current: Filter | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Filter: {column}")
        self.setModal(True)
        self._column = column
        self._column_type = column_type
        self._removed = False
        self._result: Filter | None = None

        title = QLabel(f"<b>{column}</b>")
        hint = QLabel(f"Erkannter Typ: {column_type_label(column_type)}")
        hint.setStyleSheet("color: palette(mid);")

        self.operator_combo = QComboBox()
        self.operator_combo.setObjectName("operator_combo")
        for operator in operators_for(column_type):
            self.operator_combo.addItem(operator_label(operator), operator)
        self.operator_combo.currentIndexChanged.connect(self._operator_changed)

        self.value_edit = QLineEdit()
        self.value_edit.setObjectName("value_edit")
        self.value_edit.returnPressed.connect(self.accept)
        if column_type is ColumnType.DATE:
            self.value_edit.setPlaceholderText(
                "YYYY-MM-DD oder YYYY-MM-DD HH:MM[:SS]"
            )
        elif column_type is ColumnType.NUMBER:
            self.value_edit.setPlaceholderText("z. B. 12.5")

        self.error_label = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setStyleSheet("color: #b00020;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        form = QFormLayout()
        form.addRow("Operator", self.operator_combo)
        form.addRow("Wert", self.value_edit)

        buttons = QDialogButtonBox()
        apply_button = buttons.addButton(
            "Anwenden", QDialogButtonBox.ButtonRole.AcceptRole
        )
        apply_button.setDefault(True)
        buttons.addButton(
            "Abbrechen", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.remove_button = buttons.addButton(
            "Filter entfernen", QDialogButtonBox.ButtonRole.DestructiveRole
        )
        self.remove_button.setObjectName("remove_button")
        self.remove_button.setEnabled(current is not None)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.remove_button.clicked.connect(self._remove)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

        if current is not None:
            index = self.operator_combo.findData(current.operator)
            if index >= 0:
                self.operator_combo.setCurrentIndex(index)
            self.value_edit.setText(current.value)
        self._operator_changed()
        self.value_edit.setFocus()

    def result_filter(self) -> Filter | None:
        """Der gewählte Filter; `None` bedeutet „Filter entfernen“."""
        return self._result

    def _operator_changed(self) -> None:
        operator = self.operator_combo.currentData()
        self.value_edit.setEnabled(needs_value(operator))
        self._clear_error()

    def _remove(self) -> None:
        self._removed = True
        self._result = None
        self.accept()

    def accept(self) -> None:
        if self._removed:
            self._result = None
            super().accept()
            return

        operator: FilterOperator = self.operator_combo.currentData()
        value = self.value_edit.text()
        if needs_value(operator) and not value.strip():
            self._show_error("Bitte einen Wert eingeben.")
            return
        try:
            build_filter_expr(self._column, self._column_type, operator, value)
        except QueryError as exc:
            self._show_error(str(exc))
            return
        self._result = Filter(self._column, operator, value.strip())
        super().accept()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
        self.value_edit.setStyleSheet("border: 1px solid #b00020;")

    def _clear_error(self) -> None:
        self.error_label.hide()
        self.value_edit.setStyleSheet("")
