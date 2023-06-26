from __future__ import annotations

from typing import TYPE_CHECKING

from ._meta import PropertyItem
from ..editors.checkbox import EditorCheckbox

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class BooleanItem(PropertyItem):
    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorCheckbox(
            self,
            source_index,
            parent=parent,
        )
