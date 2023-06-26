from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from EntityLibPy import DataKind

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import (
    EditorHBoxLayout,
    PropSize,
    RemoveButton,
)

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem


class EditorAddMapChild(BaseEditor):
    """Editor allowing user to add a new map child property to an DataKind.map."""

    def __init__(
        self, prop: PropertyItem, source_index, parent: QtWidgets.QWidget = None
    ):
        """Set widgets and item."""
        super().__init__(prop, source_index, parent=parent)
        self.button_action = self.default_action

        self._create_ui()
        self.updated()

    def _create_ui(self):
        layout = EditorHBoxLayout(parent=self)
        layout.setAlignment(QtCore.Qt.AlignRight)

        label = QtWidgets.QLabel("Size", self)
        label.setFixedWidth(20)
        layout.addWidget(label)

        self.prop_size = PropSize(self)
        layout.addWidget(self.prop_size)

        button_name = self.get_button_name()
        self.button = QtWidgets.QPushButton(button_name, self)
        self.button.clicked.connect(self.add_row)
        if not button_name:
            self.button.setVisible(False)
        layout.addWidget(self.button)

    def get_button_name(self):

        name = "Add"

        enum_values = (
            self.item.schema.singular_items.get().linear_items[0].sub_schema.enum_values
        )

        if enum_values:
            missing = [
                e
                for e in enum_values
                if e not in [c.name for c in self.item.child_items]
            ]
            if missing:
                # Deactivate in case the only missing item contains "count"
                if len(missing) == 1 and "count" in missing[0].lower():
                    return

                self.button_action = self.add_enum_map
                return name
            return None

        return name

    def add_enum_map(self) -> Optional[str]:

        enum_values = (
            self.item.lib_property.schema.singular_items.get()
            .linear_items[0]
            .sub_schema.enum_values
        )
        missing = [
            e for e in enum_values if e not in [c.name for c in self.item.child_items]
        ]

        dialog = QtWidgets.QInputDialog()
        dialog.setComboBoxItems(missing)
        text, ok = dialog.getItem(
            self,
            "Choose data to add",
            "Data map:",
            missing,
            0,
            editable=False,
        )

        if ok:
            return str(text)
        return None

    def set_common_data_map(self) -> Optional[str]:

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Set common data map",
            "CommonDataMap:",
        )

        if ok:
            return str(text)
        return None

    def default_action(self) -> Optional[str]:

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Set map name",
            "Map name:",
        )

        if ok:
            return str(text)
        else:
            return None

    def add_row(self):
        """Add a row.

        Row is added on source model.
        Proxy model is sorted.
        Persistent editor is opened on new row.
        Persistent editor is reloaded on row.
        """
        value = self.button_action()

        if value and self.model.add_child(self.source_index, value):
            self.updated()

    def updated(self):
        self.prop_size.update()

    def _set_editor_value(self, value):
        return None

    def _get_editor_value(self):
        return None


class EditorMapItem(BaseEditor):
    """Editor allowing user to easily update a map item."""

    def __init__(
        self, prop: PropertyItem, source_index, parent: QtWidgets.QWidget = None
    ) -> None:
        """Set widgets and item."""
        super().__init__(prop, source_index, parent=parent)

        self.value_widget = None
        self.union_type_widget = None

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        self.layout = EditorHBoxLayout(parent=self)
        self.layout.setAlignment(QtCore.Qt.AlignRight)

        for i, child in enumerate(self.item.child_items):
            if child.name == "Value":
                child_index = self.model.index(
                    i, self.source_index.column(), self.source_index
                )
                self.get_value_widget(child, child_index)

                if not child.editor:
                    child.create_editor(child_index)

                self.union_type_widget = self.create_related_connection(
                    child, child_index
                )
                self.layout.addWidget(self.union_type_widget)
                break

        self.remove_button = RemoveButton()
        self.layout.addWidget(self.remove_button)

    def _set_options(self):
        self.remove_button.clicked.connect(self.remove_row)

        if self.union_type_widget and hasattr(self.union_type_widget, "combobox"):
            self.union_type_widget.combobox.currentTextChanged.connect(
                lambda: self.get_value_widget(
                    self.union_type_widget.item, self.union_type_widget.source_index
                )
            )

    def _set_model_value(self):
        return None

    def _get_editor_value(self):
        return None

    def _set_editor_value(self, value):
        return None

    def get_value_widget(
        self, parent: PropertyItem, parent_index: QtCore.QModelIndex
    ) -> None:

        if self.value_widget:
            self.value_widget.deleteLater()
            self.value_widget = None

        for j, child in enumerate(parent.child_items):
            if child.lib_property.schema.data_kind in [
                DataKind.string,
                DataKind.number,
                DataKind.integer,
                DataKind.boolean,
                DataKind.array,
                DataKind.entityRef,
            ]:
                child_index = self.model.index(
                    j, self.source_index.column(), parent_index
                )
                self.value_widget = self.create_related_connection(child, child_index)
                self.layout.insertWidget(0, self.value_widget)

    def remove_row(self) -> None:
        # Update source index as it may have changed if
        # previous row has already been removed
        row = 0
        for i in range(self.item.parent.child_count()):
            index = self.model.index(i, 1, self.source_index.parent())
            if self.item.name == self.model.get_item(index).name:
                row = i
                break

        if self.model.remove_child(self.source_index.parent(), row):
            self.model.add_deleted_items(self.source_index.parent())
            self.update_parent_editor_size()
