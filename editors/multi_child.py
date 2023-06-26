from __future__ import annotations

from typing import TYPE_CHECKING, Union

from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.widgets import EditorHBoxLayout

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem, ContainerPropertyItem


class EditorMultiChild(BaseEditor):
    """Editor for multi children row."""

    EDITOR_HEIGHT = 20

    def __init__(
        self,
        prop: Union[ContainerPropertyItem, PropertyItem],
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self.labels = []
        self.child_editors = []

        self._create_ui()
        self._set_options()

    def _create_ui(self):
        main_layout = EditorHBoxLayout(parent=self)

        for i in range(self.model.rowCount(self.source_index)):
            child_index = self.model.index(
                i, self.source_index.column(), self.source_index
            )

            child = self.model.get_item(child_index)

            label = QtWidgets.QLabel(child.name)
            label.setFixedWidth(self.EDITOR_HEIGHT)
            label.setAlignment(QtCore.Qt.AlignCenter)
            main_layout.addWidget(label)
            self.labels.append(label)

            editor = self.create_related_connection(
                child,
                child_index,
            )
            editor.setFixedHeight(self.EDITOR_HEIGHT)
            main_layout.addWidget(editor)
            self.child_editors.append(editor)

    def _set_options(self) -> None:
        self.setStyleSheet("QtWidgets.QLabel {text-align: center};")

    def _set_editor_value(self, _) -> None:
        return
        for i, child in enumerate(self.item.child_items):
            child.editor.set_editor_value(child.value)
            pixmap = self.model.app.get_data(child, 0, QtCore.Qt.DecorationRole)
            self.labels[i].setPixmap(pixmap)

    def _get_editor_value(self):
        return None
