from PySide2 import QtWidgets
from PropertyEditor.editors.add_array_child import EditorAddArrayChild


class EditorAddObjectToSet(EditorAddArrayChild):
    """Editor allowing user to add a new objectSet child."""

    def add_row(self):
        """Add a row.

        Row is added on source model.
        Proxy model is sorted.
        Persistent editor is opened on new row.
        Persistent editor is reloaded on row.
        """

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Set map name",
            "Map name:",
        )

        if not ok or not text:
            return

        if self.model.add_child(self.source_index, str(text)):
            self.updated()
