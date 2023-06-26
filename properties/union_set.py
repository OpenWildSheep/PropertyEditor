from __future__ import annotations

from typing import Any, List, Optional

from ._meta import ContainerPropertyItem, PropertyItem


class UnionSetItem(ContainerPropertyItem):

    removable = True

    @property
    def value(self) -> Any:
        """Get value."""
        return super().value

    @value.setter
    def value(self, value: Any) -> None:
        return

    def _get_deleted_items(self):
        return [
            i
            for i in self.lib_property.prefab.unionset_items.keys()
            if i not in self.lib_property.unionset_items.keys()
        ]

    def _get_possible_child_items(self) -> List[str]:
        possible_child_items = []
        if self.lib_property.schema.singular_items:
            singular_items = self.lib_property.schema.singular_items.get()

            child_items_names = [c.name for c in self.child_items]
            if singular_items.one_of:
                for (
                    one_of_key,
                    one_of_value,
                ) in singular_items.get_union_types_dict().items():
                    if one_of_value.user_meta.get("savable", False) and one_of_key not in child_items_names:
                        possible_child_items.append(one_of_key)

            elif singular_items.enum_values:
                possible_child_items = [
                    item
                    for item in singular_items.enum_values
                    if not item.endswith("_COUNT") and item not in child_items_names
                ]

            possible_child_items.sort()
        return possible_child_items

    def _add_child(self, property_name: str, extra: Any = None):
        field_name = default_value = None
        node = self.lib_property.insert_unionset_item(property_name)

        for i in range(self.lib_property.size):
            field_name, _, _, default_value = self.get_property_child_by_index(
                self.lib_property, i, False
            )
            if field_name == property_name:
                break

        return node, field_name, default_value

    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        return self.lib_property.erase_unionset_item(child.name)
