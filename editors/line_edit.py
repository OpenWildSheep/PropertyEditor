from __future__ import annotations

from typing import TYPE_CHECKING, Union

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    StylizedLineEdit,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem, ContainerPropertyItem


class EditorLineEdit(BaseEditor):
    def __init__(
        self,
        prop: Union[ContainerPropertyItem, PropertyItem],
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        self.line_edit = StylizedLineEdit(parent=self)
        self.line_edit.textChanged.connect(self.set_model_value)

        self.main_layout = EditorHBoxLayout(parent=self)
        self.main_layout.addWidget(self.line_edit)

    def _set_options(self):
        self.deselected = False

    def _get_editor_value(self):
        return self.line_edit.text()

    def _set_editor_value(self, value):
        self.line_edit.setText(str(value))
