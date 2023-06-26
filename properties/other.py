from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from PropertyEditor.config import Config
from PropertyEditor.editors.add_back import AddBackItem
from PropertyEditor.editors.instance_of import EditorInstanceOf
from PropertyEditor.editors.spinbox import EditorDoubleSpinboxContainer
from PropertyEditor.properties._meta import BaseItem

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem
    from PySide2 import QtCore, QtWidgets


class InstanceOfItem(BaseItem):
    """Representation of special InstanceOf property.

    Usable with a QAbstractItemModel.
    """

    def __init__(self, parent: PropertyItem = None):
        """Initialize."""
        super().__init__(parent)

        self.name = "InstanceOf"
        self._lib_property = parent.lib_property
        self._value = self.lib_property.first_instance_of
        self.tooltip = f"Object is an instance of {self.value}"

        # Hack to always have to InstanceOf at the end of its hierarchy
        # As it's sorted alphabetically, using multiple "z" characters
        # will always put it at the end
        self._sort_value = "z" * 12

    @property
    def is_set(self) -> bool:
        """Get is_set."""
        if self.value:
            return True
        else:
            return False

    @property
    def is_path(self):
        return True

    @property
    def value(self) -> Any:
        """Get value."""
        return self.lib_property.first_instance_of

    @value.setter
    def value(self, value: Any) -> None:
        """Set value."""
        if self.lib_property.prefab and self.lib_property.prefab.value == value:
            self.unset()
        elif Path(self.rawdata_path, value).is_file():
            self.lib_property.instance_of = value

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorInstanceOf(
            self,
            source_index,
            parent=parent,
        )

    def add_instance_of(self):
        self.parent.add_instance_of()


class DeletedItem(BaseItem):
    """Representation of deleted property.

    Usable with a QAbstractItemModel.
    """

    def __init__(self, name, parent: PropertyItem = None):
        """Initialize."""
        super().__init__(parent=parent)

        self.name = name
        self.display_name = f"{name} (Deleted)"
        self._lib_property = parent.lib_property
        self._value = None

    def get_name(self) -> Optional[str]:
        return self.display_name

    def get_config_color(self, config: Config):
        return config.color.deleted_element

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return AddBackItem(
            self,
            source_index,
            parent=parent,
        )


class EulerValueItem(BaseItem):
    def __init__(self, name, value, parent: EulerValueItem = None):
        """Initialize."""
        super().__init__(parent)

        self.name = name
        self._lib_property = parent.lib_property
        self._value = value
        self._base_value = value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = val
        self.parent.update_value()

    def _get_editor(
        self, source_index: QtCore.QModelIndex, parent: QtWidgets.QWidget = None
    ):
        return EditorDoubleSpinboxContainer(
            self,
            source_index,
            parent=parent,
        )
