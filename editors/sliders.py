from __future__ import annotations

from typing import Union, TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    StylizedLineEdit,
    DoubleSlider,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem


class EditorDoubleSlider(BaseEditor):
    """Editor slider for floats."""

    def __init__(
        self,
        prop: PropertyItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        layout = EditorHBoxLayout(parent=self)
        layout.setContentsMargins(0, 0, 5, 0)

        self.line_edit = StylizedLineEdit()
        self.line_edit.setFixedWidth(55)
        self.line_edit.textChanged.connect(self.emitDoubleTextChanged)
        layout.addWidget(self.line_edit)

        self.slider = DoubleSlider()
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        layout.addWidget(self.slider)

    def _set_options(self):
        item = self.model.get_item(self.source_index)

        if isinstance(item.minimum, float):
            self.slider.setMinimum(int(item.minimum))
        if isinstance(item.maximum, float):
            self.slider.setMaximum(int(item.maximum))
        self.slider.valueChanged.connect(self.emitDoubleValueChanged)

    def _get_editor_value(self):
        value = self.slider.value()
        return value

    def _set_editor_value(self, value: Union[int, float]):
        self.slider.setValue(value)
        self.line_edit.setText(str(value))
        if self.item.parent.is_color:
            self.item.parent.editor.set_editor_value(None)

    def on_update(self, value: float):
        self._set_editor_value(value)
        self.set_model_value()

    def emitDoubleValueChanged(self):
        """Emit double value changed."""
        value = self.slider.emitDoubleValueChanged()
        self.on_update(value)

    def emitDoubleTextChanged(self):
        """Emit double text changed."""
        value = self.line_edit.text()
        self.on_update(float(value))
