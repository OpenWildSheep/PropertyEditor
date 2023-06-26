from typing import Optional

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    PropSize,
    AddRemoveButton,
    ChoiceDialog,
)


class EditorChildrenManager(BaseEditor):
    """Editor allowing user to add a new child property."""

    def __init__(self, item, source_index, parent: QtWidgets.QWidget = None):
        """Set widgets and item."""
        super().__init__(item, source_index, parent=parent)

        self._create_ui()
        self._set_options()
        self.updated()

    def _create_ui(self):
        layout = EditorHBoxLayout(parent=self)
        layout.setAlignment(QtCore.Qt.AlignRight)

        label = QtWidgets.QLabel("Size", self)
        label.setFixedWidth(20)
        layout.addWidget(label)

        self.prop_size = PropSize(self)
        layout.addWidget(self.prop_size)

        self.add_button = AddRemoveButton("+")
        layout.addWidget(self.add_button)

        self.remove_button = AddRemoveButton("-")
        layout.addWidget(self.remove_button)

    def _set_options(self):
        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_row)

    def open_choice_popup(self, add_mode=True):
        popup = ChoiceDialog(
            self.item, self.model.app.get_style(), parent=self, add_mode=add_mode
        )
        result = popup.exec_()
        if result:
            return popup.combobox.currentText()
        return None

    def _get_editor_value(self):
        if not self.item.get_possible_child_items():
            return None
        return self.open_choice_popup()

    def _set_editor_value(self, value):
        return None

    def add_row(self):
        """Add a row based on combobox selection.

        Row is added on source model.
        Proxy model is sorted.
        Persistent editor is opened on new row.
        Persistent editor is reloaded on row.
        """
        value = self.get_editor_value()
        if value is not None:
            if self.model.add_child(self.source_index, value):
                self.updated()

    def get_row_to_remove(self) -> Optional[int]:
        if not self.item.child_items:
            return None

        result = self.open_choice_popup(add_mode=False)
        if result:
            for i, prop in enumerate(self.item.child_items):
                if prop.name == result:
                    return i

        return None

    def remove_row(self):
        """Remove a row based on combobox selection.

        Row is removed on source model.
        Proxy model is sorted.
        """
        row = self.get_row_to_remove()
        if row is not None and self.model.remove_child(self.source_index, row):
            self.model.add_deleted_items(self.source_index)
            self.updated()

    def updated(self):
        self.prop_size.update()
        self.remove_button.setVisible(bool(self.prop_size.get()))
