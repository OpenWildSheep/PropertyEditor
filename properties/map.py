from __future__ import annotations

from typing import List, Optional, Any, TYPE_CHECKING

from ._meta import ContainerPropertyItem, PropertyItem
from ..editors.map import EditorAddMapChild

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class MapItem(ContainerPropertyItem):

    removable = True

    def _get_deleted_items(self) -> List[PropertyItem]:
        prop_items = [i for i, _ in self.lib_property.map_items]
        return [i for i, _ in self.lib_property.prefab.map_items if i not in prop_items]

    def _add_child(self, property_name: str, extra: Any = None):
        field_name = str(property_name)
        node = self.lib_property.insert_map_item(field_name)

        return node, field_name, None

    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        return self.lib_property.erase_map_item(child.name)

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorAddMapChild(
            self,
            source_index,
            parent=parent,
        )
