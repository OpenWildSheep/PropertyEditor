from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, Union, Optional, Tuple, TYPE_CHECKING

from PySide2 import QtCore

if TYPE_CHECKING:
    from PropertyEditor.app import PropertyEditorApp
    from PropertyEditor.properties._meta import (
        PropertyItem,
        ContainerPropertyItem,
        BaseItem,
    )


class Model(QtCore.QAbstractItemModel):
    """Custom model to manage Property items."""

    def __init__(
        self,
        app: PropertyEditorApp,
        root_item: ContainerPropertyItem,
        loaded_file: Optional[Path] = None,
    ):
        """Initialize."""
        QtCore.QAbstractItemModel.__init__(self)
        self.app = app
        self.loaded_item: ContainerPropertyItem = root_item
        self.loaded_file: Path = loaded_file

    @property
    def relative_path(self) -> Optional[Path]:
        return (
            self.app.get_rawdata_relative_path(self.loaded_file)
            if self.loaded_file
            else None
        )

    @contextlib.contextmanager
    def _add_row(self, parent_index: QtCore.QModelIndex) -> Tuple[PropertyItem, int]:
        parent_index = self.ensure_column_0(parent_index)

        item = self.get_item(parent_index)
        last_row = self.rowCount(parent_index)

        self.beginInsertRows(parent_index, last_row, last_row)
        yield item, last_row
        self.endInsertRows()

    @contextlib.contextmanager
    def _remove_row(
        self, parent_index: QtCore.QModelIndex, row: int
    ) -> Tuple[PropertyItem, QtCore.QModelIndex]:
        parent_index = self.ensure_column_0(parent_index)

        child_index = self.index(row, 0, parent_index)
        child_item = self.get_item(child_index)

        self.beginRemoveRows(parent_index, row, row)
        yield child_item, child_index
        self.endRemoveRows()

    @contextlib.contextmanager
    def reset_model(self):
        self.beginResetModel()
        yield
        self.endResetModel()

    def ensure_column_0(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if index.column() == 1:
            return self.index(index.row(), 0, index.parent())
        return index

    def ensure_column_1(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if index.column() == 0:
            return self.index(index.row(), 1, index.parent())
        return index

    def ensure_right_index(self, parent_index: QtCore.QModelIndex, prop: BaseItem):
        prop_row = self.rowCount(parent_index) - 1
        for row in range(prop_row + 1):
            test_index = self.index(row, 1, parent_index)
            if prop.name == self.get_item(test_index).name:
                prop_row = row
                break

        return self.index(prop_row, 1, parent_index)

    def rowCount(self, index: QtCore.QModelIndex = None, *args, **kwargs) -> int:
        if not index.isValid():
            return self.loaded_item.child_count()
        return self.get_item(index).child_count()

    def columnCount(self, index: QtCore.QModelIndex = None, *args, **kwargs) -> int:
        return 2

    def data(
        self,
        index: QtCore.QModelIndex,
        role: QtCore.Qt.ItemDataRole = None,
    ) -> Union[None, str]:
        """Get data."""
        if not index.isValid():
            return None
        return self.app.get_data(self.get_item(index), index.column(), role)

    def headerData(
        self,
        column: int,
        orientation: QtCore.Qt.Orientation,
        role: QtCore.Qt.DisplayRole = None,
    ) -> Union[None, str]:
        """Get header data."""
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "Property"
            elif column == 1:
                return "Value"

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        """Get flags."""
        if index.isValid():
            if index.column() == 0:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            elif index.column() == 1:
                return (
                    QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsSelectable
                    | QtCore.Qt.ItemIsEditable
                    | QtCore.Qt.ItemNeverHasChildren
                )

        return QtCore.Qt.ItemFlags()

    def root_index(self):
        return self.index(-1, -1)

    def index(
        self, row: int, column: int, parent: QtCore.QModelIndex = None
    ) -> QtCore.QModelIndex:
        if not parent or not parent.isValid():
            parent_item = self.loaded_item
        else:
            parent_item = self.get_item(parent)

        child_item = parent_item.get_child_at_pos(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QObject:
        """Get parent."""
        if not index.isValid():
            return QtCore.QModelIndex()

        parent_item = self.get_item(index).parent
        if not parent_item or parent_item == self.loaded_item:
            return QtCore.QModelIndex()

        return self.createIndex(
            parent_item.index_in_parent(), index.column(), parent_item
        )

    def get_item(
        self, index: QtCore.QModelIndex
    ) -> Optional[Union[ContainerPropertyItem, PropertyItem, BaseItem]]:
        if index.isValid():
            return index.internalPointer()
        return None

    def set_item_value(self, prop: BaseItem, value: Any):
        if prop.value != value:
            prop.value = value
            self.app.set_current_tab_edited()

    def add_child(
        self, index: QtCore.QModelIndex, value: Any
    ) -> Optional[PropertyItem]:
        with self._add_row(index) as (item, row):
            child = item.add_child(value)
        if child:
            self.app.update_row(index, row)
            return child
        return None

    def add_deleted_items(self, index: QtCore.QModelIndex) -> None:
        index = self.ensure_column_0(index)

        item: ContainerPropertyItem = self.get_item(index)
        if not item.missing_deleted_items():
            return

        with self._add_row(index) as (item, row):
            item.add_deleted_items()
        self.app.update_row(index, row)

    def add_back_item(self, parent_index: QtCore.QModelIndex, prop: PropertyItem):
        index = self.ensure_right_index(parent_index, prop)
        self.remove_child(parent_index, index.row())

        child = self.add_child(parent_index, prop.name)
        if child:
            child.revert_to_prefab()
            self.app.update_row(parent_index, index.row())

    def reset_last_child(self, parent_index: QtCore.QModelIndex):
        with self._add_row(parent_index) as (item, row):
            item.reset_children()
        self.app.update_row(parent_index, row)

    def remove_child(self, parent_index: QtCore.QModelIndex, row: int) -> bool:
        with self._remove_row(parent_index, row) as (item, source_index):
            result = item.remove_from_parent()
            if result:
                self.app.set_current_tab_edited()
        return result

    def iter_indexes(self):
        def recurse(parent_index: QtCore.QModelIndex):
            for row in range(self.rowCount(parent_index)):
                child_index = self.index(row, 1, parent_index)
                yield child_index
                if self.rowCount(child_index):
                    yield from recurse(child_index)

        yield from recurse(self.root_index())
