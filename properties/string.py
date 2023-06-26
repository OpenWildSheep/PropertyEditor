from __future__ import annotations

from typing import TYPE_CHECKING

from ._meta import PropertyItem
from ..editors.path import EditorPath
from ..editors.line_edit import EditorLineEdit
from ..editors.list import EditorList

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class StringItem(PropertyItem):
    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        if self.schema.enum_values:
            return EditorList(
                self,
                source_index,
                self.schema.enum_values,
                parent=parent,
            )
        elif self.name != "Name" or self.parent.name != self.value:
            return EditorLineEdit(
                self,
                source_index,
                parent=parent,
            )

    def allow_paste(self, copy_data) -> bool:
        if super().allow_paste(copy_data):
            if bool(self.schema.enum_values) != bool(copy_data.enum_values):
                return False

            elif (
                self.schema.enum_values
                and copy_data.value not in self.schema.enum_values
            ):
                return False
            return True
        return False


class PathItem(PropertyItem):

    path = True

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorPath(
            self,
            source_index,
            parent=parent,
        )
