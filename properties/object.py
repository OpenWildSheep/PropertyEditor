from __future__ import annotations

from typing import Any, TYPE_CHECKING

from EntityLibPy import DataKind

from ._meta import ContainerPropertyItem
from ..editors.map import EditorMapItem

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class ObjectItem(ContainerPropertyItem):
    @property
    def value(self) -> Any:
        """Get value."""
        return super().value

    @value.setter
    def value(self, value: Any) -> None:
        return

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        if self.parent and self.parent.data_kind == DataKind.map:
            return EditorMapItem(
                self,
                source_index,
                parent=parent,
            )
        else:
            return super()._get_editor(source_index, parent=parent)
