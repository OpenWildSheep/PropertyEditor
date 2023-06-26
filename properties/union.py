from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ._meta import ContainerPropertyItem, PropertyItem
from ..editors.union_type import EditorUnionType

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class UnionItem(ContainerPropertyItem):
    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        # Union items child removal is managed by its parent editor and the EntityLib
        # Just return True to allow the process to work smoothly
        return True

    def _create_child(self, index, root, lib_property, field_name, value, parent=None):
        _, _, _, default_value = self.get_property_child_by_index(
            lib_property, index, False
        )
        # field_name = value

        return super()._create_child(
            index, root, lib_property, field_name, value, parent=parent
        )

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorUnionType(
            self,
            source_index,
            self.lib_property.schema.get_union_types_dict(),
            parent=parent,
        )
