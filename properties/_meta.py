from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

from EntityLibPy import (
    CopyMode,
    DataKind,
    Property,
    OverrideValueSource,
    EntityLib,
    Schema,
)

from PropertyEditor.config import Config

if TYPE_CHECKING:
    from PropertyEditor.editors._meta import BaseEditor
    from PySide2 import QtCore, QtWidgets


class BaseItem:
    """Base class to use Property as QTreeView item."""

    def __init__(self, parent: Optional[BaseItem, PropertyItem] = None):
        """Initialize."""
        self._name = None
        self._parent = parent

        self._lib_property = None

        self._default_value = None
        self._value = None
        self._sort_value = None

        self._root_node = None
        self._node_ref = None

        self.editor = None
        self.child_items = []
        self.instance_of = None

    @property
    def name(self) -> str:
        """Get name."""
        return self._name

    @name.setter
    def name(self, property_name: str) -> None:
        self._name = property_name

    @property
    def parent(self) -> ContainerPropertyItem:
        """Get parent."""
        return self._parent

    @property
    def value(self) -> Any:
        """Get value."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        if value != self._value:
            self._value = value

    @property
    def root_node(self) -> Property:
        return self._root_node

    @property
    def node_ref(self) -> Property:
        return self._node_ref

    @property
    def lib_property(self) -> Optional[Property]:
        """Get node."""
        if self._lib_property:
            return self._lib_property
        elif self.root_node and self.node_ref:
            return self.root_node.resolve_noderef(self.node_ref)
        return None

    @property
    def entity_lib(self) -> Optional[EntityLib]:
        return self.lib_property.entitylib

    @property
    def rawdata_path(self) -> str:
        return str(self.entity_lib.rawdata_path)

    @property
    def schema(self) -> Optional[Schema]:
        return self.lib_property.schema

    @property
    def schema_name(self) -> Optional[str]:
        if self.schema:
            return self.schema.name
        return None

    @property
    def data_kind(self) -> Optional[DataKind]:
        if self.schema:
            return self.schema.data_kind
        return None

    @property
    def user_meta(self) -> dict:
        return self.schema.user_meta or {}

    @property
    def prefab(self) -> Property:
        return self.lib_property.prefab

    @property
    def is_default(self) -> bool:
        return self.lib_property.is_default

    @property
    def is_removable(self) -> bool:
        if not self.parent:
            return False
        return getattr(self.parent, "removable", False)

    @property
    def is_container(self) -> bool:
        return getattr(self, "container", False)

    @property
    def is_color(self) -> bool:
        return getattr(self, "color", False)

    @property
    def is_sub_color(self) -> bool:
        """Get if property is a sub color."""
        return getattr(self, "sub_color", False)

    @property
    def is_path(self) -> bool:
        return getattr(self, "path", False)

    @property
    def is_local(self) -> bool:
        if self.parent and self.parent.parent:
            if self.parent and self.parent.is_local:
                return True
            elif self.has_prefab and self.prefab.parent:
                return not bool(self.prefab.parent.parent)

        return False

    @property
    def is_set(self) -> bool:
        """Get is_set."""
        return self.lib_property.is_set

    @property
    def has_prefab(self) -> bool:
        """Get if node has prefab."""
        return self.lib_property.has_prefab

    @property
    def has_prefab_overrides(self) -> bool:
        """Get if node has prefab overrides."""
        return self.has_prefab and not self.is_default

    @property
    def maximum(self) -> Optional[int, float]:
        """Get maximum from schema or schema.user_meta."""
        if hasattr(self.lib_property.schema, "maximum"):
            return self.lib_property.schema.maximum
        elif "max" in self.user_meta.get("range", {}):
            return self.lib_property.user_meta["range"]["max"]
        return None

    @property
    def minimum(self) -> Optional[int, float]:
        """Get minimum from schema or schema.user_meta."""
        if hasattr(self.lib_property.schema, "minimum"):
            return self.lib_property.schema.minimum
        elif "min" in self.lib_property.schema.user_meta.get("range", {}):
            return self.lib_property.schema.user_meta["range"]["min"]
        return None

    @property
    def sort_value(self) -> str:
        if not self._sort_value:
            return self.name
        return self._sort_value

    @sort_value.setter
    def sort_value(self, value: str) -> None:
        self._sort_value = value

    @staticmethod
    def get_config_color(config: "Config") -> Tuple[int, int, int]:
        return config.color.light_grey

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        raise NotImplementedError

    def child_count(self) -> int:
        return 0

    def get_tooltip(self) -> Optional[str]:
        return None

    def get_name(self) -> Optional[str]:
        return self.name

    def get_value(self) -> Optional[Any]:
        return self.value

    def index_in_parent(self) -> int:
        if self.parent:
            return self.parent.child_items.index(self)
        return 0

    def revert_to_prefab(self) -> bool:
        return True

    def save_to_prefab(self, path: str) -> None:
        return

    def get_possible_child_items(self) -> list:
        return []

    def get_prefab_history(self) -> list:
        return [i for i in self.lib_property.get_prefab_history] if self.prefab else []

    def get_prefab_history_paths(self) -> list:
        return [i.prefab_path for i in self.get_prefab_history()]

    def debug_data(self) -> str:
        return f"""
{self.name} | {self.__class__.__name__}
_______________________
Value: {self.value}
Data kind: {self.data_kind}
Size: {self.child_count()} | {self.lib_property.size}
Is Set: {self.is_set}
Has prefab: {self.has_prefab}
Is default: {self.is_default}
Schema name: {self.lib_property.schema.name}
Paths: {self.lib_property.file_path} | {self.lib_property.path_token}
Memory address: {id(self)}
Prefab history: {', '.join(self.get_prefab_history_paths())}
Is local: {self.is_local}
Parent: {self.parent}
Instance Of: {self.lib_property.instance_of}
Editor: {self.editor} | Related {self.editor.related if self.editor else None}
        """

    def _get_child_items(self, child_level: int = 3) -> List[PropertyItem]:
        return []

    def get_child_items(self, child_level: int = 3):
        return self._get_child_items(child_level=child_level)

    def create_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ) -> Optional[BaseEditor]:

        if self.editor:
            # When using filtering, C++ editor's instance can have been removed
            # in that case just skip the error and create a new editor
            try:
                self.editor.setParent(parent)
                return self.editor
            except RuntimeError:
                pass

        editor = self.get_editor(source_index, parent=parent)
        if editor:
            self.editor = editor
            return editor

    def get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ) -> Optional[BaseEditor]:
        # Get child items first as they are needed for some editors
        self._get_child_items()
        return self._get_editor(source_index, parent=parent)

    def remove_from_parent(self) -> bool:
        if self.parent:
            return self.parent.remove_child_item(self)

    def reset_editors(self) -> None:
        if self.editor:
            self.editor.set_editor_value(self.value)

    def reset_children(self) -> None:
        return

    def not_deleted_child_count(self) -> int:
        """Get child count without the DeletedProperty items."""
        from PropertyEditor.properties.other import DeletedItem

        return len([c for c in self.child_items if not isinstance(c, DeletedItem)])

    def allow_copy(self) -> bool:
        return True

    def allow_paste(self, copy_data) -> bool:
        if self.data_kind == copy_data.data_kind:
            return True
        return False

    def __repr__(self) -> str:
        value = f"{self.name} | {self.value} | {self.child_count()}"
        if self.lib_property.schema:
            value += f" | {self.data_kind}"
        if hasattr(self, "instance_of"):
            value += f" | {bool(self.instance_of)}"

        return value


class PropertyItem(BaseItem):
    """Manage the use of Property with a QAbstractItemModel."""

    def __init__(
        self,
        root: Optional[PropertyItem],
        lib_property: Property,
        property_name: str,
        default_value: Any,
        parent=None,
    ):
        """Initialize."""
        super().__init__(parent=parent)

        self.name = property_name

        self._lib_property = lib_property

        self._default_value = default_value or self.schema.get_default_value()

        self._root = root if root else self
        self._root_node = root.lib_property if root else lib_property
        self._node_ref = lib_property.absolute_noderef if lib_property else None
        self._config = None

        self.add_instance_of()

    @property
    def value(self) -> Any:
        """Get value."""
        return self.lib_property.value

    @value.setter
    def value(self, value: Any) -> None:
        """Set value."""
        if value != self.lib_property.value:
            self.lib_property.value = value

    @property
    def config(self) -> Config:
        if self._root._config:
            return self._root._config
        elif self._config:
            return self._config
        raise Exception("Config is not set.")

    @staticmethod
    def get_property_child_by_index(
        node: Property,
        index: int,
        inline: bool,
    ) -> (str | None, Property | None, Any | None, Any | None):
        """Get element at n position in property."""
        kind = node.schema.data_kind
        field_name = new_node = value = default_value = None

        if kind == DataKind.array:
            field_name = str(index)
            if index >= node.size:
                field_name = index
            else:
                new_node = node.get_array_item(index)
                default_value = (
                    node.schema.get_default_value()[index]
                    if node.schema.get_default_value()
                    else []
                )

        elif kind == DataKind.map:
            for i, key in enumerate(node.map_keys):
                if i == index:
                    field_name = key
                    new_node = node.get_map_item(key)
                    break

        elif kind == DataKind.object:
            if not inline:
                field_name = next(
                    itertools.islice(node.schema.properties.keys(), index, None)
                )
                new_node = node.get_object_field(field_name)

        elif kind == DataKind.objectSet:
            for i, key in enumerate(node.objectset_keys):
                if i == index:
                    field_name = key
                    new_node = node.get_objectset_item(key)
                    break

        elif kind == DataKind.unionSet:
            for i, key in enumerate(node.unionset_keys):
                if i == index:
                    field_name = key
                    new_node = node.get_unionset_item(key)
                    break

        elif kind in [
            DataKind.boolean,
            DataKind.integer,
            DataKind.number,
            DataKind.string,
        ]:
            if index == 0:
                field_name = index
                new_node = node
                value = node.value
                default_value = node.schema.get_default_value()
            else:
                field_name = index
                new_node = node

        elif kind == DataKind.primitiveSet:
            field_name = str(index)
            if index >= node.size:
                field_name = index
            default_value = node.primset_keys[index]

        elif kind == DataKind.union:
            if index == 0:
                field_name = str(node.union_type)
                new_node = node.get_union_data()
                value = node.union_type
            elif index == 1:
                field_name = "Data"
                new_node = node.get_union_data()

        return field_name, new_node, value, default_value

    def get_tooltip(self) -> str:
        """Get data to display in the view."""
        description = self.schema.description or "No description"

        status = "Status: "
        if self.is_set:
            status += "is set"
        elif self.is_default and self.data_kind not in self.config.container_types:
            status += "is default"
        elif self.has_prefab:
            if self.is_local:
                status += "local changes"
            else:
                status += "comes from prefab"

        history = ""
        prefab_history = self.get_prefab_history_paths()
        if prefab_history:
            prefab_history.reverse()
            history += "\nPrefab history:\n - " + "\n - ".join(prefab_history[1:])
        else:
            history += "\nNo prefab history"

        return f"{description}\n{status}\n{history}"

    def revert_to_prefab(self) -> bool:
        if not self.lib_property:
            return False

        size_before_unset = self.lib_property.size
        self.lib_property.unset()

        size_changed = False
        # Reset all child properties editors
        if self.lib_property.size == size_before_unset:

            # Revert parent if none of its children is set anymore
            if self.parent and all(not c.is_set for c in self.parent.child_items):
                self.parent.revert_to_prefab()

            for child in self.child_items:
                child.reset_editors()

        # Otherwise let unset caller to manage
        # the rows and children update
        else:
            size_changed = True

        return size_changed

    def save_to_prefab(self, path: str) -> Tuple[Optional[Property], Optional[Path]]:
        if not path:
            print("Can't find a prefab related to {}".format(self.name))
            return None, None

        file_path = Path(path)
        if self.rawdata_path not in path:
            file_path = Path(self.rawdata_path, path)

        if not file_path.is_file:
            print(f"{file_path} is not an existing file. Can't save to prefab.")
            return None, None

        for prefab in self.get_prefab_history():
            if Path(prefab.prefab_path).as_posix() == Path(path).as_posix():
                self.lib_property.copy_into(
                    prefab.node,
                    CopyMode.CopyOverride,
                    OverrideValueSource.Override,
                )
                self.revert_to_prefab()
                self.reset_editors()
                return prefab, file_path
        return None, None

    def add_instance_of(self) -> None:
        if self.instance_of:
            return

        if self.lib_property and self.lib_property.instance_of:
            from PropertyEditor.properties.other import InstanceOfItem

            self.instance_of = InstanceOfItem(self)
            self.child_items.append(self.instance_of)


class ContainerPropertyItem(PropertyItem):

    container = True

    @staticmethod
    def _create_child(index, root, lib_property, field_name, value, parent=None):
        data_kind = lib_property.schema.data_kind

        if data_kind == DataKind.array:
            from .array import ColorItem, QuatItem, ArrayItem

            if lib_property.schema.user_meta.get("widget", False) == "color":
                prop_type = ColorItem
            elif lib_property.schema.name == "Quat":
                prop_type = QuatItem
            else:
                prop_type = ArrayItem

        elif data_kind == DataKind.number:
            from .number import NumberItem

            prop_type = NumberItem

        elif data_kind == DataKind.integer:
            from .integer import IntegerItem

            prop_type = IntegerItem

        elif data_kind == DataKind.boolean:
            from .boolean import BooleanItem

            prop_type = BooleanItem

        elif data_kind == DataKind.string:
            from .string import PathItem, StringItem

            if lib_property.schema.user_meta.get("path", False):
                prop_type = PathItem
            elif "path" in field_name.lower() or (
                lib_property.value
                and Path(
                    str(lib_property.entitylib.rawdata_path), str(lib_property.value)
                ).is_file()
            ):
                prop_type = PathItem
            else:
                prop_type = StringItem

        elif data_kind == DataKind.entityRef:
            from .entity_ref import EntityRefItem

            prop_type = EntityRefItem

        elif data_kind == DataKind.objectSet:
            from .object_set import ObjectSetItem

            prop_type = ObjectSetItem

        elif data_kind == DataKind.unionSet:
            from .union_set import UnionSetItem

            prop_type = UnionSetItem

        elif data_kind == DataKind.map:
            from .map import MapItem

            prop_type = MapItem

        elif data_kind == DataKind.primitiveSet:
            from .primitive_set import PrimitiveSetItem

            prop_type = PrimitiveSetItem

        elif data_kind == DataKind.union:
            from .union import UnionItem

            prop_type = UnionItem

        elif data_kind == DataKind.object:
            from .object import ObjectItem

            prop_type = ObjectItem

        else:
            raise NotImplementedError(f"Can't created child with {data_kind}")

        return prop_type(root, lib_property, field_name, value, parent=parent)

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        if self.get_possible_child_items():
            from PropertyEditor.editors.add_child import EditorChildrenManager

            return EditorChildrenManager(
                self,
                source_index,
                parent=parent,
            )
        elif self.is_removable:
            from PropertyEditor.editors.remove_item import EditorRemoveItem

            return EditorRemoveItem(
                self,
                source_index,
                parent=parent,
            )

    def _remove_child_item(self, child: BaseItem = None) -> bool:
        raise NotImplementedError

    def _get_possible_child_items(self):
        return []

    def _add_child(
        self, property_name: str, extra: Any = None
    ) -> Tuple[Optional[Property], Optional[str], Optional[Any]]:
        raise NotImplementedError

    def _get_deleted_items(self) -> List[str]:
        return []

    def allow_copy(self) -> bool:
        return False

    def child_count(self) -> int:
        return len(self.child_items)

    def append_child(self, item: BaseItem) -> None:
        """Append a new child."""
        self.child_items.append(item)

    def get_child_at_pos(self, index: int) -> Optional[BaseItem]:
        if 0 <= index < len(self.child_items):
            return self.child_items[index]
        return None

    def get_child_by_name(self, name: str) -> BaseItem:
        for child in self.child_items:
            if child.name == name:
                return child
        raise NameError(f"Can't find a {name} child property for {self.name}")

    def get_child_index(self, item: BaseItem) -> int:
        for i, child in enumerate(self.child_items):
            if child == item:
                return i
        raise IndexError(f"Can't find a {item.name} child property for {self.name}")

    def reset_children(self) -> None:
        for item in [i for i in self.child_items]:
            del item
        self.child_items = []
        self._get_child_items()

    def remove_child_at(self, row: int) -> bool:
        return self.remove_child_item(child=self.child_items[row])

    def remove_child_item(self, child: BaseItem = None) -> bool:
        from PropertyEditor.properties.other import DeletedItem

        if not self.child_items:
            return False

        elif not child:
            child = self.child_items[-1]

        if isinstance(child, DeletedItem) or self._remove_child_item(child):
            self.child_items.remove(child)
            return True

        raise Exception(f"{child} removal from {self} failed!")

    def get_possible_child_items(self) -> list:
        return self._get_possible_child_items()

    def _get_child_items(self, child_level: int = 3) -> List[PropertyItem]:
        """Get child items.

        As we can't load a whole scene at start, for performance reasons,
        load a only a specific depth.
        The other properties will be loaded when needed.
        """
        from PropertyEditor.properties.other import InstanceOfItem

        if not self.lib_property:
            raise Exception(f"{self} has no lib_property. This should never happen.")

        if (
            not self.child_items
            or len(self.child_items) == 1
            and isinstance(self.child_items[0], InstanceOfItem)
        ):
            for index in range(self.lib_property.size):
                (
                    field_name,
                    lib_property,
                    value,
                    default_value,
                ) = self.get_property_child_by_index(self.lib_property, index, False)

                child = self._create_child(
                    index,
                    self._root,
                    lib_property,
                    field_name,
                    default_value,
                    parent=self,
                )

                self.append_child(child)
            self.add_deleted_items()

        self.add_instance_of()

        if child_level:
            for child in self.child_items:
                if child.is_container:
                    child._get_child_items(child_level=child_level - 1)

        return self.child_items

    def add_child(self, property_name: str) -> Optional[BaseItem]:
        prop, field_name, default_value = self._add_child(property_name)
        if prop and field_name:
            child_property = self._create_child(
                self.child_count(),
                self._root,
                prop,
                field_name,
                None,
                parent=self,
            )

            self.append_child(child_property)
            child_property._get_child_items()
            return child_property

        return prop

    def get_not_deleted_child_items(self):
        from PropertyEditor.properties.other import DeletedItem

        return [i for i in self.child_items if not isinstance(i, DeletedItem)]

    def get_deleted_items(self) -> List[str]:
        from PropertyEditor.properties.other import DeletedItem

        if not self.prefab:
            return []

        deleted_items = self._get_deleted_items()
        if not deleted_items:
            return []

        existing_deleted_items = [
            c.name for c in self.child_items if isinstance(c, DeletedItem)
        ]
        return [d for d in deleted_items if d not in existing_deleted_items]

    def missing_deleted_items(self) -> bool:
        return bool(self.get_deleted_items())

    def add_deleted_items(self) -> None:
        from PropertyEditor.properties.other import DeletedItem

        for item in self.get_deleted_items():
            self.append_child(
                DeletedItem(
                    item,
                    parent=self,
                )
            )

    def reset_editors(self) -> None:
        super().reset_editors()
        for child in self.child_items:
            if not child.editor:
                continue
            child.editor.set_editor_value(child.value)
            child.reset_editors()
