from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.editors.add_array_child import EditorAddArrayChild
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    RemoveButton,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import BaseItem


class EditorPrimitiveSetString(BaseEditor):
    """Editor for string primitive set child."""

    def __init__(
        self,
        prop: BaseItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        main_layout = EditorHBoxLayout(parent=self)

        self.line_edit = QtWidgets.QLineEdit(self)
        main_layout.addWidget(self.line_edit)

        if self.item.parent.can_remove_item(self.item.value):
            self.button = RemoveButton()
            self.button.clicked.connect(self.remove_row)
            main_layout.addWidget(self.button)

    def _set_options(self):
        self.line_edit.setEnabled(False)
        self.line_edit.setStyleSheet(
            "QtWidgets.QLineEdit{background: #333; color: #888; border: none}"
        )

    def _get_editor_value(self) -> str:
        return self.line_edit.text()

    def _set_editor_value(self, value: Any) -> None:
        if value is None:
            value = ""
        self.line_edit.setText(str(value))

    def remove_row(self):
        row = 0
        for i in range(self.item.parent.child_count()):
            index = self.model.index(i, 1, self.source_index.parent())
            if self.item.name == self.model.get_item(index).name:
                row = i
                break

        if self.model.remove_child(self.source_index.parent(), row):
            self.update_parent_editor_size()


class EditorAddPrimitiveSetChild(EditorAddArrayChild):
    def add_row(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Set primitive set item",
            "Primitive set value:",
        )

        if ok and text:
            if text in self.item.contains(text):
                return

            elif self.model.add_child(self.source_index, text):
                self.updated()

    def remove_row(self):
        row = self.item.child_count() - 1
        if row is not None and self.model.remove_child(self.source_index, row):
            self.updated()
