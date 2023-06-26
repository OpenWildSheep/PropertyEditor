from __future__ import annotations

import contextlib
from typing import List, TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import PropertyItem


class Proxy(QtCore.QSortFilterProxyModel):
    """Custom proxy model to manage both wildcard and filters."""

    def __init__(self, parent: QtWidgets.QWidget):
        """Initialize."""
        super().__init__(parent=parent)

        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(0)

        self.override_filter = None
        self.force_all = True
        self.matching_node_references = []
        self.filtered = []

    def filterAcceptsRow(
        self, source_row: int, source_parent: QtCore.QModelIndex
    ) -> bool:
        """Accept rows matching regex and their children.

        Not the most optimized way to manage children.
        For now, we use an attribute on each child to know if we show it or not.
        And we reset this attribute when wildCard is updated (see setFilterWildcard()).
        """
        index = self.sourceModel().index(source_row, 0, source_parent)
        match_filter = self.match_filter(index)

        if not all(
            [
                match_filter,
                self.filter_overrides(source_row, source_parent),
            ]
        ):
            return False

        return True

    def match_filter(self, source_index: QtCore.QModelIndex) -> bool:
        if self.force_all:
            return True
        elif not self.matching_node_references:
            return False

        prop = self.sourceModel().get_item(source_index)
        if not prop:
            return False

        if any(
            [
                prop.lib_property.absolute_noderef in i
                for i in self.matching_node_references
            ]
        ):
            self.filtered.append(source_index)
            return True

        elif any(
            [
                i in prop.lib_property.absolute_noderef
                for i in self.matching_node_references
            ]
        ):
            return True

    def filter_overrides(
        self, source_row: int, source_parent: QtCore.QModelIndex
    ) -> bool:
        """Accept row matching filter overrides."""
        if not self.override_filter or self.override_filter == "All":
            return True

        item = self.get_item(source_row, source_parent)
        if (self.override_filter == "Overrides" and not item.has_prefab_overrides) or (
            self.override_filter == "LocalOverrides" and not item.is_set
        ):
            return False

        return True

    @contextlib.contextmanager
    def filter_update_context(self):

        yield
        self.setFilterWildcard("*")

    def select_overrides_updated(self, override_filter: str) -> None:
        """Select overrides changed."""
        with self.filter_update_context():
            self.override_filter = override_filter

    def get_search_matching_properties(self, search_value: str) -> List[str]:
        return [
            node.absolute_noderef
            for node in self.sourceModel().loaded_item.lib_property.search_child(
                search_value
            )
        ]

    def search_filter_updated(self, search_pattern: str) -> None:
        with self.filter_update_context():
            if search_pattern:
                self.matching_node_references = self.get_search_matching_properties(
                    search_pattern
                )
                self.force_all = False
            else:
                self.matching_node_references = []
                self.filtered = []
                self.force_all = True

    def get_item(self, source_row, source_parent) -> PropertyItem:
        index = self.sourceModel().index(source_row, 0, source_parent)
        return self.sourceModel().get_item(index)

    def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
        left_data: str = self.sourceModel().data(left, role=QtCore.Qt.UserRole)
        right_data: str = self.sourceModel().data(right, role=QtCore.Qt.UserRole)

        if left_data is None or right_data is None:
            return False

        if left_data.isnumeric():
            return int(left_data) < int(right_data)
        return left_data < right_data

    def iter_indexes(self):
        def recurse(parent_index: QtCore.QModelIndex):
            for row in range(self.rowCount(parent_index)):
                child_index = self.index(row, 0, parent_index)
                yield child_index
                if self.rowCount(child_index):
                    yield from recurse(child_index)

        yield from recurse(self.mapFromSource(self.sourceModel().root_index()))

    def ensure_proxy_index(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if index.model() and index.model() != self:
            return self.mapFromSource(index)
        return index

    def ensure_column_1(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        # Don't check different from 1 as for -1 column (root item) we don't want
        # to update the index's column
        if index.column() == 0:
            return self.index(index.row(), 1, index.parent())
        return index
