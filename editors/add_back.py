from PySide2 import QtWidgets

from PropertyEditor.editors.remove_item import EditorRemoveItem


class AddBackItem(EditorRemoveItem):
    """Editor allowing user to add back a removed item."""

    def _create_button(self):
        self.button = QtWidgets.QPushButton("Revert to prefab")
        self.button.clicked.connect(self.add_back_item)

    def add_back_item(self):
        self.model.add_back_item(self.source_index.parent(), self.item)
        self.update_parent_editor_size()
