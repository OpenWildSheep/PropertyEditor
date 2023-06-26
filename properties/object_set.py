from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from ._meta import ContainerPropertyItem, PropertyItem
from ..editors.object_set import EditorAddObjectToSet

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class ObjectSetItem(ContainerPropertyItem):

    removable = True

    @property
    def value(self) -> Any:
        """Get value."""
        return super().value

    @value.setter
    def value(self, value: Any) -> None:
        return

    def _get_deleted_items(self) -> List[PropertyItem]:
        prop_items = [i for i in self.lib_property.objectset_keys]
        return [
            i for i in self.lib_property.prefab.objectset_keys if i not in prop_items
        ]

    def _add_child(self, property_name: str, extra: Any = None):
        field_name = str(property_name)
        node = self.lib_property.insert_objectset_item(field_name)

        return node, field_name, None

    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        return self.lib_property.erase_objectset_item(child.name)

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorAddObjectToSet(self, source_index, parent=parent)
