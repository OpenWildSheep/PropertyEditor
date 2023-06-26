from __future__ import annotations

from typing import TYPE_CHECKING

from EntityLibPy import EntityRef

from ._meta import PropertyItem
from .string import EditorLineEdit

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class EntityRefItem(PropertyItem):

    path = True

    @property
    def value(self) -> str:
        return str(self.lib_property.value)

    @value.setter
    def value(self, value: str) -> None:
        self.lib_property.set_entityref(EntityRef(value))

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorLineEdit(
            self,
            source_index,
            parent=parent,
        )
