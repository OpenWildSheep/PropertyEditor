from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    BetterScrollComboBox,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem


class EditorUnionType(BaseEditor):
    """Editor allowing user to set union object's type."""

    def __init__(
        self,
        prop: PropertyItem,
        source_index: QtCore.QModelIndex,
        union_types: dict,
        parent: QtWidgets.QWidget = None,
    ):
        """Set widgets and item."""
        super().__init__(prop, source_index, parent=parent)
        self.union_types = union_types

        layout = EditorHBoxLayout(parent=self)
        layout.setAlignment(QtCore.Qt.AlignRight)

        self.combobox = BetterScrollComboBox(self)
        for item in union_types.keys():
            self.combobox.addItem(item)
        self.combobox.setCurrentText(self.item.lib_property.union_type)
        self.combobox.currentTextChanged.connect(self.set_model_value)
        layout.addWidget(self.combobox)

    def _get_editor_value(self):
        return self.combobox.currentText()

    def _set_editor_value(self, value):
        self.combobox.setCurrentText(value)

    def _set_model_value(self):
        value = self.get_editor_value()
        self.item.lib_property.set_union_type(value)

        self.model.remove_child(self.source_index, 0)
        self.model.reset_last_child(self.source_index)
        self.updated()

        for related in self.related:
            related.set_editor_value(value)

    def updated(self):
        self.item.editor.set_editor_value(self.get_editor_value())
