from __future__ import annotations

from typing import List, TYPE_CHECKING, Union

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import EditorHBoxLayout, BetterScrollComboBox

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem, ContainerPropertyItem


class EditorList(BaseEditor):
    def __init__(
        self,
        prop: Union[ContainerPropertyItem, PropertyItem],
        source_index: QtCore.QModelIndex,
        values: list,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self._create_ui(values)
        self._set_options()

    def _create_ui(self, values: List[str]):
        self.combobox = BetterScrollComboBox(self)
        for val in values:
            self.combobox.addItem(val)

        main_layout = EditorHBoxLayout(parent=self)
        main_layout.addWidget(self.combobox)

    def _set_options(self):
        self.combobox.currentTextChanged.connect(self.set_model_value)

    def _get_editor_value(self):
        return self.combobox.currentText()

    def _set_editor_value(self, value):
        self.combobox.setCurrentText(value)
