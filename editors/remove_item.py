from __future__ import annotations

from typing import TYPE_CHECKING, Union

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import EditorHBoxLayout, RemoveButton

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem, ContainerPropertyItem


class EditorRemoveItem(BaseEditor):
    """Editor allowing user to remove an item."""

    def __init__(
        self,
        prop: Union[ContainerPropertyItem, PropertyItem],
        source_index,
        parent: QtWidgets.QWidget = None,
    ):
        """Set widgets and item."""
        super().__init__(prop, source_index, parent=parent)

        layout = EditorHBoxLayout(parent=self)
        layout.setAlignment(QtCore.Qt.AlignRight)

        self._create_button()
        layout.addWidget(self.button)

    def _create_button(self) -> None:
        self.button = RemoveButton()
        self.button.clicked.connect(self.remove_row)

    def remove_row(self) -> None:
        self.source_index = self.model.ensure_right_index(
            self.source_index.parent(), self.item
        )
        if self.model.remove_child(self.source_index.parent(), self.source_index.row()):
            self.model.add_deleted_items(self.source_index.parent())
            self.update_parent_editor_size()

    def _get_editor_value(self):
        return None

    def _set_editor_value(self, value):
        return None
