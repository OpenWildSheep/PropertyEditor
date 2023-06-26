from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtGui, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.widgets.color_picker import ColorPicker
from PropertyEditor.widgets.widgets import EditorHBoxLayout

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import ContainerPropertyItem


class EditorColor(BaseEditor):
    """Editor for color with children row."""

    def __init__(
        self,
        prop: ContainerPropertyItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        super().__init__(prop, source_index, parent=parent)

        self.rows = self.item.child_count()
        self.spins = []
        self.color = QtGui.QColor(*[0.0 for _ in range(self.rows)])

        self._create_ui()
        self._set_options()
        self.update_color_viewer()

    def _create_ui(self):

        self.color_viewer = QtWidgets.QPushButton(self)
        self.color_viewer.setToolTip(self.color.name())
        self.color_viewer.clicked.connect(self.choose_color)

        main_layout = EditorHBoxLayout(parent=self)
        main_layout.addWidget(self.color_viewer)

    def _set_options(self):
        self.setStyleSheet("QPushButton {border: 1px solid #222}")

    def update_color_viewer(self):
        tooltip = "R {} | G {} | B {}".format(
            round(self.color.redF(), 3),
            round(self.color.greenF(), 3),
            round(self.color.blueF(), 3),
        )

        if self.rows == 4:
            background_color = "rgba({},{},{},{})".format(
                self.color.red(),
                self.color.green(),
                self.color.blue(),
                self.color.alpha(),
            )
            tooltip += " | A {}".format(round(self.color.alphaF(), 3))

        else:
            background_color = "rgb({}, {}, {})".format(
                self.color.red(),
                self.color.green(),
                self.color.blue(),
            )

        self.color_viewer.setStyleSheet(
            "QPushButton {{background: {};}}".format(background_color)
        )
        self.color_viewer.setToolTip(tooltip)

    def choose_color(self) -> None:
        use_alpha = self.color.alphaF() if self.rows == 4 else None
        self.color_dialog = ColorPicker(
            initial=self.color, use_alpha=use_alpha, parent=self
        )
        self.color_dialog.currentColorChanged.connect(self.set_color)
        self.color_dialog.show()

    def set_color(self) -> None:
        self.color = self.color_dialog.current_color()
        self.update_color_viewer()
        self.set_model_value(None)
        self.update_color_viewer()

    def _set_editor_value(self, _) -> None:
        """Set editor data from each child rows."""
        for i in range(self.rows):
            source_property = self.item.child_items[i]
            value = source_property.value or 0.0

            if i == 0:
                self.color.setRedF(value)
            elif i == 1:
                self.color.setGreenF(value)
            elif i == 2:
                self.color.setBlueF(value)
            elif i == 3:
                self.color.setAlphaF(value)

        self.update_color_viewer()

    def _set_model_value(self, *args) -> None:
        """Update right child's row's editor."""
        color = [
            self.color.redF(),
            self.color.greenF(),
            self.color.blueF(),
            self.color.alphaF(),
        ]

        for i, value in enumerate(color):
            round_value = round(value, 3)
            child_item = self.item.get_child_at_pos(i)

            if not child_item.editor:
                index = self.source_index.model().index(
                    i, self.source_index.column(), self.source_index
                )
                child_item.create_editor(index)

            child_item.editor.set_editor_value(round_value)
            child_item.editor.set_model_value()

    def _get_editor_value(self):
        return None
