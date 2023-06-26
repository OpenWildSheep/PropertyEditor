from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from EntityLibPy import DataKind

from ._meta import ContainerPropertyItem, PropertyItem, BaseItem
from .union_set import UnionSetItem
from ..editors.primitive_set import EditorAddPrimitiveSetChild, EditorPrimitiveSetString

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class PrimitiveSetContentItem(BaseItem):
    def __init__(
        self,
        parent: PropertyItem,
        property_name: str,
        value,
    ):
        """Initialize."""
        super().__init__(parent)

        self.name = property_name
        self.tooltip = property_name
        self._lib_property = parent.lib_property
        self._value = value

        self.primitive_type = self.lib_property.primset_key_kind

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.lib_property.insert_primset_item(value)

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        if self.primitive_type == DataKind.string:
            return EditorPrimitiveSetString(
                self,
                source_index,
                parent=parent,
            )

        return EditorAddPrimitiveSetChild(
            self,
            source_index,
            parent=parent,
        )


class PrimitiveSetItem(ContainerPropertyItem):
    @property
    def value(self) -> Any:
        """Get value."""
        return super().value

    @value.setter
    def value(self, value: Any) -> None:
        return

    def contains(self, value: str):
        return self.lib_property.primset_contains(value)

    def _get_possible_child_items(self) -> List[str]:
        return UnionSetItem._get_possible_child_items(self)

    def add_child(self, property_name: str) -> PrimitiveSetContentItem:
        prop, field_name, default_value = self._add_child(property_name)

        child_property = PrimitiveSetContentItem(self, field_name, default_value)

        self.append_child(child_property)
        child_property._get_child_items()
        return child_property

    def _add_child(self, property_name: str, extra: Any = None):
        field_name = str(len(self.child_items))
        self.lib_property.insert_primset_item(property_name)
        return None, field_name, property_name

    def can_remove_item(self, value):
        if self.prefab and self.prefab.primset_contains(value):
            return False
        return True

    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        if not self.contains(child.value):
            return False

        self.lib_property.erase_primset_key(child.value)
        return True

    def _create_child(self, index, root, lib_property, field_name, value, parent=None):
        return PrimitiveSetContentItem(
            self,
            field_name,
            value,
        )

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorAddPrimitiveSetChild(
            self,
            source_index,
            parent=parent,
        )
