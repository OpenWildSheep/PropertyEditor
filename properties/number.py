from __future__ import annotations

from typing import TYPE_CHECKING

from .integer import IntegerItem
from ..editors.sliders import EditorDoubleSlider
from ..editors.spinbox import EditorDoubleSpinboxContainer

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class NumberItem(IntegerItem):
    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        if isinstance(self.minimum, float) or isinstance(self.maximum, float):
            return EditorDoubleSlider(self, source_index, parent=parent)
        else:
            return EditorDoubleSpinboxContainer(
                self,
                source_index,
                parent=parent,
            )
