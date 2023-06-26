from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors.line_edit import EditorLineEdit
from PropertyEditor.widgets.widgets import EditorButton

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem


class EditorPath(EditorLineEdit):
    """Editor widget for paths.

    Contains a line edit and a button to open a FileDialog.
    """

    def __init__(
        self,
        prop: PropertyItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

    def _create_ui(self):
        super()._create_ui()

        self.button = EditorButton("Browse")
        self.button.clicked.connect(self.open_dialog)
        self.main_layout.addWidget(self.button)

    def _set_model_value(self):
        value = self.get_editor_value()
        if (not value and not self.item.value) or value == self.item.value:
            return

        super()._set_model_value()

    def open_dialog(self) -> None:
        """Open a FileDialog at the 'right' place."""
        value = self.get_editor_value()
        path = Path(self.source_index.model().app.rawdata_path, value).parent

        extension = None
        if value:
            split = value.split(".")

            if len(split) > 1:
                extension = split[-1]
            if not extension:
                user_meta = self.item.lib_property.schema.user_meta
                if user_meta:
                    extension = user_meta.get("path", {}).get("glob")
            if extension and not extension.startswith("*."):
                extension = f"{extension.capitalize()} (*.{extension})"

        dialog_filter = "All (*.*)"
        if extension:
            dialog_filter = f"{extension};;{dialog_filter}"

        dialog = QtWidgets.QFileDialog()
        dialog.setDirectory(path.as_posix())
        file_name = dialog.getOpenFileName(
            self,
            "Open File",
            path.as_posix(),
            dialog_filter,
        )
        file_name = file_name[0]
        if not file_name:
            return

        file_name = self.model.app.get_rawdata_relative_path(Path(file_name)).as_posix()

        self._set_editor_value(file_name)
        self.set_model_value()
