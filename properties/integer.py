from __future__ import annotations

from typing import TYPE_CHECKING

from ._meta import PropertyItem
from ..editors.spinbox import EditorSpinboxContainer

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class IntegerItem(PropertyItem):
    @property
    def sub_color(self) -> bool:
        return (
            True if self.parent and getattr(self.parent, "is_color", False) else False
        )

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorSpinboxContainer(
            self,
            source_index,
            parent=parent,
        )
