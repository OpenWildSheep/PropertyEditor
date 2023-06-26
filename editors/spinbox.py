from __future__ import annotations

from typing import Union, TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    EditorSpinbox,
    EditorDoubleSpinbox,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import ContainerPropertyItem, PropertyItem


class EditorSpinboxContainer(BaseEditor):

    spinbox_type = EditorSpinbox

    def __init__(
        self,
        prop: Union[PropertyItem, ContainerPropertyItem],
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        super().__init__(prop, source_index, parent=parent)

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        self.spinbox = self.spinbox_type(parent=self)
        layout = EditorHBoxLayout(parent=self)
        layout.addWidget(self.spinbox)

    def _set_options(self):
        self.spinbox.valueChanged.connect(self.set_model_value)
        self.spinbox.textChanged.connect(self.set_model_value)

    def _get_editor_value(self):
        return self.spinbox.value()

    def _set_editor_value(self, value: Union[int, float]) -> None:
        self.spinbox.setValue(value)


class EditorDoubleSpinboxContainer(EditorSpinboxContainer):

    spinbox_type = EditorDoubleSpinbox

    def _set_options(self):
        self.spinbox.valueChanged.connect(self.set_round_values)
        self.spinbox.textChanged.connect(self.set_round_values)

    def set_round_values(self):
        # Need to round the editor's value
        # as setDecimals() seems to not work correctly,
        # leading to .0000000000000000001 style values
        # when clicking on the spinners
        self.set_editor_value(round(self.get_editor_value(), 4))
        self.set_model_value()

    def _set_editor_value(self, value: Union[int, float]) -> None:
        self.spinbox.setValue(round(value, 3))
