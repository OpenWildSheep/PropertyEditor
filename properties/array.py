from __future__ import annotations

import math
from typing import Any, List, Optional, TYPE_CHECKING

from EntityLibPy import Property

from .other import EulerValueItem
from ._meta import PropertyItem, ContainerPropertyItem
from ..editors.add_array_child import EditorAddArrayChild
from ..editors.color import EditorColor
from ..editors.multi_child import EditorMultiChild

if TYPE_CHECKING:
    from PySide2 import QtCore, QtWidgets


class ArrayItem(ContainerPropertyItem):
    @property
    def is_removable(self) -> bool:
        if not self.parent.lib_property.schema.max_items:
            return True
        return False

    @property
    def value(self) -> Any:
        """Get value."""
        return super().value

    @value.setter
    def value(self, value: Any) -> None:
        return

    def _add_child(self, property_name: str, extra: Any = None):
        node = self.lib_property.push_back()
        field_name = str(self.lib_property.size - 1)
        return node, field_name, None

    def _remove_child_item(self, child: Optional[PropertyItem] = None) -> bool:
        self.lib_property.pop_back()
        return True

    def _get_child_items(self, child_level: int = 3) -> List[PropertyItem]:
        result = super()._get_child_items(child_level=child_level)
        self.rename_child_items()
        return result

    def rename_child_items(self) -> None:
        if self.name in ["Position", "Orientation", "Scale"] or "Axis" in self.name:
            if self.child_count() == 4:
                value = "XYZW"
            elif self.child_count() == 3:
                value = "XYZ"
            else:
                return

            for child in self.child_items:
                actual_name = child.name
                if actual_name.isnumeric():
                    child.name = value[int(actual_name)]

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):

        if 5 > self.child_count() > 0 and self.child_count() == self.schema.max_items:
            return EditorMultiChild(self, source_index, parent=parent)

        return EditorAddArrayChild(
            self,
            source_index,
            parent=parent,
        )


class ColorItem(ContainerPropertyItem):

    color = True

    def _get_child_items(self, child_level: int = 3) -> List[PropertyItem]:
        result = super()._get_child_items(child_level=child_level)
        self.rename_child_items()
        return result

    def rename_child_items(self) -> None:
        for child in self.child_items:
            actual_name = child.name
            if actual_name.isnumeric():
                child.name = "RGBA"[int(actual_name)]
                child.sort_value = actual_name

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorColor(
            self,
            source_index,
            parent=parent,
        )


class QuatItem(ContainerPropertyItem):
    def __init__(
        self,
        root: Optional[PropertyItem],
        lib_property: Property,
        property_name: str,
        default_value: Any,
        parent=None,
    ):
        super().__init__(
            root, lib_property, property_name, default_value, parent=parent
        )
        self.real_child_items = []

    def _get_child_items(self, child_level: int = 2) -> None:
        if not self.child_items:
            self.real_child_items = super()._get_child_items(child_level=child_level)

            # Reset child items as we want to use Euler values instead of quaternions
            # Quaternions items are stored into self.real_child_items
            # And Eulers will be added to child items just after
            self.child_items = []

            euler = self.quat_to_euler()
            for i, axis in enumerate("XYZ"):
                self.child_items.append(EulerValueItem(axis, euler[i], self))

    @property
    def euler(self) -> List[float]:
        return [math.radians(c.value) for c in self.child_items]

    @property
    def quaternion(self) -> List[float]:
        return [c.lib_property.value for c in self.real_child_items]

    def quat_to_euler(self) -> List[float]:
        x, y, z, w = self.quaternion

        t0 = 2.0 * (w * x + y * z)
        t1 = 1 - 2 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)

        t2 = 2 * (w * y - z * x)
        t2 = 1 if t2 > 1 else t2
        t2 = -1 if t2 < -1 else t2
        pitch_y = math.asin(t2)

        t3 = 2 * (w * z + x * y)
        t4 = 1 - 2 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)

        return [math.degrees(roll_x), math.degrees(pitch_y), math.degrees(yaw_z)]

    def euler_to_quat(self) -> List[float]:
        roll, pitch, yaw = self.euler

        qx = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) - math.cos(
            roll / 2
        ) * math.sin(pitch / 2) * math.sin(yaw / 2)
        qy = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) + math.sin(
            roll / 2
        ) * math.cos(pitch / 2) * math.sin(yaw / 2)
        qz = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) - math.sin(
            roll / 2
        ) * math.sin(pitch / 2) * math.cos(yaw / 2)
        qw = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) + math.sin(
            roll / 2
        ) * math.sin(pitch / 2) * math.sin(yaw / 2)

        # Round to 15th decimal to avoid e-16 values instead of 0
        return [round(qx, 15), round(qy, 15), round(qz, 15), round(qw, 15)]

    def update_value(self) -> None:
        quaternion = self.euler_to_quat()
        for i, value in enumerate(quaternion):
            self.real_child_items[i].lib_property.value = value

    def unset(self) -> None:
        if not self.lib_property:
            return

        self.lib_property.unset()

        # Reset all child properties
        euler = self.quat_to_euler()
        for i, child in enumerate(self.child_items):
            child.update_parent = False
            child.value = euler[i]
            child.is_set = False
            child.reset_editors()
            child.update_parent = True

        # Unset parent if none of its children is set anymore
        if all(not c.is_set for c in self.parent.child_items):
            self.parent.unset()

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorMultiChild(
            self,
            source_index,
            parent=parent,
        )

    def debug_data(self) -> str:
        return f"""
{self.name} | {self.__class__.__name__}
_______________________
Value: {self.value}
Data kind: {self.data_kind}
Size: {self.child_count()} | {self.lib_property.size}
Is Set: {self.is_set}
Has prefab: {self.has_prefab}
Instance of: {self.instance_of.value if self.instance_of else None}
Schema name: {self.lib_property.schema.name}
Euler as radians: {self.euler}
Quaternion: {self.quaternion}
Child is set: {[c.is_set for c in self.real_child_items]}
Paths: {self.lib_property.file_path} | {self.lib_property.path_token}
Memory address: {id(self)}
        """
