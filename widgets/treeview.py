from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import List, TYPE_CHECKING

from PySide2 import QtCore, QtGui, QtWidgets

from PropertyEditor.model.delegate import Delegate
from PropertyEditor.model.model import Model
from PropertyEditor.model.proxy import Proxy

if TYPE_CHECKING:
    from PropertyEditor.app import PropertyEditorApp


class TreeView(QtWidgets.QTreeView):
    def __init__(self, model: Model, parent=None):
        """Initialize."""
        QtWidgets.QTreeView.__init__(self, parent=parent)

        self.proxy_model = Proxy(self)
        self.setModel(self.proxy_model)
        self.proxy_model.setSourceModel(model)

        self.setItemDelegate(Delegate())
        self.set_index_editable()
        self.adjust_columns()
        self.proxy_model.sort(0)

        self.setUniformRowHeights(False)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)
        self.viewport().setAttribute(QtCore.Qt.WA_Hover)

        self.setExpandsOnDoubleClick(True)
        self.setAcceptDrops(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setViewportMargins(5, 5, 5, 5)
        self.setAlternatingRowColors(True)

        self.last_column_width = None

        self.expanded.connect(self.set_index_editable)
        self.collapsed.connect(self.set_not_editable)

    @property
    def source_model(self) -> Model:
        return self.proxy_model.sourceModel()

    @property
    def app(self) -> PropertyEditorApp:
        return self.source_model.app

    def get_window(self):
        widget = self.parent()
        while widget.parent():
            widget = widget.parent()
        return widget

    def rowsRemoved(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        super().rowsRemoved(parent, first, last)

    def adjust_columns(self) -> None:
        """Adjust column 0 to minimum size."""

        self.resizeColumnToContents(0)

        # Add a padding to the first column by increasing its size
        self.setColumnWidth(0, 15 + self.columnWidth(0))

        width = self.columnWidth(0)
        if width < 150:
            self.setColumnWidth(0, 150)

    def get_source_index(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Get source index."""
        return self.model().mapToSource(index)

    def set_index_editable(
        self, index: QtCore.QModelIndex = None, edit: bool = True
    ) -> None:

        if not index:
            index = QtCore.QModelIndex()
        else:
            index = self.model().ensure_proxy_index(index)

        # parent_index.column() can be -1 or 0 in this method
        # When it's 0 we want to ensure that the persistent editor is opened
        # for that we need to get related column 1 index
        # When it's -1 that means we work with the root model item that have no editor
        index_col_1 = self.proxy_model.ensure_column_1(index)
        if not self.isPersistentEditorOpen(index_col_1):
            self.openPersistentEditor(index_col_1)

        # Here the index needs to have a column() == 0
        # otherwise rowCount() returns 0 for whatever reason...
        for row in range(self.model().rowCount(index)):
            child_index = self.model().index(row, 1, index)
            if edit:
                self.openPersistentEditor(child_index)
            else:
                self.closePersistentEditor(child_index)
        self.adjust_columns()

    def set_not_editable(self, index: QtCore.QModelIndex = None) -> None:
        """Set an index as not editable."""
        if self.isPersistentEditorOpen(index):
            self.set_index_editable(index, edit=False)

    def update_row(self, parent_index: QtCore.QModelIndex, row: int) -> None:
        source_index = self.source_model.index(row, 0, parent_index)
        proxy_index = self.model().mapFromSource(source_index)

        # First expand from column 0 as expand doesn't work from column 1
        self.expand(proxy_index.parent())
        self.expand(proxy_index)

        # Then open persistent editor from column 1 as we want the editor in... column 1
        proxy_index = proxy_index.model().index(
            proxy_index.row(), 1, proxy_index.parent()
        )

        self.openPersistentEditor(proxy_index)

    def expand_current_cell(self) -> None:
        index = self.currentIndex()
        self.expand(index)

        # Need to expand two times to make it work
        # Otherwise only the first child element is expanded
        self.expand(index)

    def expand_cell_and_children(self) -> None:
        self.expandRecursively(self.currentIndex(), depth=3)

        # Need to expand two times to make it work
        # Otherwise only the first child element is expanded
        self.expandRecursively(self.currentIndex(), depth=3)
        self.adjust_columns()

    def expand_filtered_and_parents(self, filtered: List[QtCore.QModelIndex]) -> None:
        if filtered:
            for index in filtered:
                proxy_index = self.model().mapFromSource(index)

                parents = []
                while proxy_index.row() != -1:
                    if not self.isExpanded(proxy_index):
                        parents.append(proxy_index)
                    proxy_index = proxy_index.parent()

                for proxy_index in reversed(parents):
                    self.expand(proxy_index)
        # Force all expanded items and their children to be editable
        # otherwise when text filter is removed, some items are not.
        else:
            for index in self.proxy_model.iter_indexes():
                if self.isExpanded(index):
                    self.set_index_editable(index)

    @contextlib.contextmanager
    def filter_update_context(self):

        yield
        self.expand_filtered_and_parents(self.model().filtered)
        self.set_index_editable()
        self.adjust_columns()

    def collapse_cell(self) -> None:
        current_index = self.currentIndex()
        self.collapse(current_index)

    def save_to_prefab(self, path: str) -> None:
        self.app.save_to_prefab(
            self.source_model.get_item(
                self.proxy_model.mapToSource(self.currentIndex())
            ),
            path,
        )

    def debug_data(self, prop) -> str:
        data = prop.debug_data()
        print(data)
        return data

    def openMenu(self, position: QtCore.QPoint) -> None:

        source_index = self.model().mapToSource(self.indexAt(position))
        if not source_index.model():
            item = self.model().sourceModel().loaded_item
        else:
            item = source_index.model().get_item(source_index)

        menu = QtWidgets.QMenu(self)
        node = item.lib_property

        if node.size:
            expand = QtWidgets.QAction("Expand")
            expand.triggered.connect(self.expand_current_cell)
            menu.addAction(expand)

            expand_all = QtWidgets.QAction("Expand all")
            expand_all.triggered.connect(self.expand_cell_and_children)
            menu.addAction(expand_all)

            collapse = QtWidgets.QAction("Collapse")
            collapse.triggered.connect(self.collapse_cell)
            menu.addAction(collapse)

        if item.is_path:
            menu.addSeparator()
            copy_path = QtWidgets.QAction("Copy path")
            copy_path.triggered.connect(lambda: self.copy_path(item.value))
            menu.addAction(copy_path)

            open_folder = QtWidgets.QAction("Open folder")
            open_folder.triggered.connect(lambda: self.open_folder(item.value))
            menu.addAction(open_folder)

        if source_index.row() == -1:
            menu.addSeparator()
            reload_file = QtWidgets.QAction("Reload file")
            reload_file.triggered.connect(self.confirm_reload_file)
            menu.addAction(reload_file)

        if item.has_prefab:

            menu.addSeparator()
            if node and node.is_set:
                unset = QtWidgets.QAction("Revert to prefab")
                unset.triggered.connect(
                    lambda: self.app.revert_to_prefab(
                        self.source_model, item, source_index
                    )
                )
                menu.addAction(unset)

            prefab_history = item.get_prefab_history()
            prefab_history.reverse()

            open_prefab = QtWidgets.QMenu("Open prefab", menu)
            save_to_prefab = QtWidgets.QMenu("Save to prefab", menu)

            for prefab in prefab_history[1:]:
                prefab_icon = QtGui.QIcon(
                    self.app._get_decoration_color_for_prefab(prefab)
                )

                save_to_prefab_action = save_to_prefab.addAction(prefab.prefab_path)
                save_to_prefab_action.setIcon(prefab_icon)
                save_to_prefab_action.triggered.connect(
                    lambda *args, prefab=prefab: self.save_to_prefab(prefab.prefab_path)
                )

                open_prefab_action = open_prefab.addAction(prefab.prefab_path)
                open_prefab_action.setIcon(prefab_icon)
                open_prefab_action.triggered.connect(
                    lambda *args, prefab=prefab: self.open_file_from_path(
                        prefab.prefab_path
                    )
                )

            menu.addMenu(open_prefab)
            menu.addMenu(save_to_prefab)

        menu.addSeparator()

        if node and item.is_removable:
            remove = QtWidgets.QAction("Remove")
            remove.triggered.connect(lambda: self.remove_row(item))
            menu.addAction(remove)

        menu.addSeparator()

        if item.instance_of or item.name == "InstanceOf":

            if item.instance_of:
                value = item.instance_of.value
            else:
                value = item.value

            if value:
                open_instance_of = QtWidgets.QAction("Open Instance Of file")
                open_instance_of.triggered.connect(
                    lambda: self.open_file_from_path(value)
                )
                menu.addAction(open_instance_of)

                reload_instance_of = QtWidgets.QAction("Reload instanceOf")
                reload_instance_of.triggered.connect(self.confirm_reload_file)
                menu.addAction(reload_instance_of)

        menu.addSeparator()

        if self.app.allow_copy(item):
            copy_value = QtWidgets.QAction("Copy value")
            copy_value.triggered.connect(lambda: self.app.copy(item))
            menu.addAction(copy_value)

        if self.app.allow_paste(item):
            paste_value = QtWidgets.QAction("Paste value")
            paste_value.triggered.connect(lambda: self.app.paste(item))
            menu.addAction(paste_value)

            paste_override_value = QtWidgets.QAction("Paste only override")
            paste_override_value.triggered.connect(
                lambda only_override: self.app.paste(item, only_overrides=True)
            )
            menu.addAction(paste_override_value)

        menu.addSeparator()

        debug_item = QtWidgets.QAction("Property debug data")
        debug_item.triggered.connect(lambda: self.debug_data(item))
        menu.addAction(debug_item)

        menu.exec_(self.viewport().mapToGlobal(position))

    def copy_path(self, value: str) -> None:
        full_path = Path(str(self.app.rawdata_path), value)

        app = QtWidgets.QApplication.instance()
        clipboard = app.clipboard()
        clipboard.clear(mode=clipboard.Clipboard)
        clipboard.setText(full_path.as_posix(), mode=clipboard.Clipboard)

    def open_folder(self, value: str) -> None:
        path = Path(str(self.app.rawdata_path), value)
        if path.is_file():
            path = path.parent
        os.startfile(path.as_posix())

    def open_file_from_path(self, path: str) -> None:
        file_path = Path(path)
        if not file_path:
            print("Can't find a prefab related to {}".format(self.name))
            return

        if ":" not in path:
            file_path = Path(str(self.app.rawdata_path), path)

        if not file_path.is_file:
            print(f"{file_path} is not an existing file. Can't save to prefab.")
            return

        self.app.load_file(file_path)

    def confirm_reload_file(self):
        text = "You'll loose all your changes."
        info = "Are your sure you want to reload?"

        if self.confirm_reload(text, info):
            with self.keep_expanded():
                self.app.reload_file()

    def confirm_reload(self, text: str, info: str) -> bool:

        message = QtWidgets.QMessageBox(self)
        message.setText(text)
        message.setInformativeText(info)
        message.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )
        message.setDefaultButton(QtWidgets.QMessageBox.Save)
        result = message.exec_()

        if result == QtWidgets.QMessageBox.Yes:
            return True
        return False

    def get_current_item(self):

        source_index = self.model().mapToSource(self.currentIndex())
        return self.source_model.get_item(source_index)

    def get_expanded(self):
        expanded = []
        for index in self.model().persistentIndexList():
            if self.isExpanded(index):
                source_index = self.model().mapToSource(index)
                prop = self.source_model.get_item(source_index)
                expanded.append(prop.lib_property.absolute_noderef)

        # As persistentIndexList is not sorted by hierarchy
        # applying a sort on our expanded list ensure it
        expanded.sort()

        return expanded

    def set_expanded(self, expanded_data: list):
        root_index = self.source_model.root_index()
        for item in expanded_data:
            current_index = root_index
            for prop_part in item.split("/"):

                # Reset index when expanded item has no parent
                current_level = len(item.split("/"))
                if current_level == 1:
                    current_index = root_index

                for i in range(self.source_model.rowCount(current_index)):
                    index = self.source_model.index(i, 0, current_index)
                    prop = self.source_model.get_item(index)
                    if prop.name == prop_part:
                        current_index = index
                        model_index = self.model().mapFromSource(index)
                        self.expand(model_index)
                        break

    @contextlib.contextmanager
    def keep_expanded(self) -> None:
        """Keep expanded elements and vertical scroll."""
        expanded = self.get_expanded()
        current_scroll = self.verticalScrollBar().value()

        yield

        self.set_expanded(expanded)
        self.verticalScrollBar().setValue(current_scroll)

    def get_parent_tab_name(self) -> str:
        return self.parent().label

    def remove_row(self, item):
        editor = self.source_model.get_item(
            self.model().mapToSource(self.currentIndex())
        ).editor
        if hasattr(editor, "remove_row"):
            editor.remove_row()

    def open_property_at_path(self, property_path: str) -> None:
        """Find property using its path and open it."""

        model = self.model()
        source_model = model.sourceModel()
        root_property = source_model.loaded_item

        # Scroll from root property to awaited one
        # expanding each property in the property's path
        current_prop = root_property
        source_index = source_model.index(-1, 0)
        for i, prop in enumerate(property_path.split("/")):

            child_prop = current_prop.get_child_by_name(prop)
            if not child_prop:
                break

            # Ensure child items have been created
            child_prop._get_child_items(child_level=1)

            # Get model index of the child property
            row = current_prop.get_child_index(child_prop)
            source_index = source_model.index(row, 0, source_index)
            index = model.mapFromSource(source_index)

            self.expand(index)
            self.scrollTo(index, hint=QtWidgets.QAbstractItemView.PositionAtTop)

            current_prop = child_prop

    def mousePressEvent(self, event: QtGui.QMouseEvent, *args) -> None:
        if event.modifiers() == QtCore.Qt.AltModifier:
            index = self.indexAt(event.pos())
            self.setCurrentIndex(index)
            if self.isExpanded(index):
                self.collapse_cell()
            else:
                self.expand_cell_and_children()
        else:
            super().mousePressEvent(event)

    def set_search_filter(self, filter_: str) -> None:
        with self.filter_update_context():
            self.proxy_model.search_filter_updated(filter_)

    def select_overrides_updated(self, override: str) -> None:
        with self.filter_update_context():
            self.proxy_model.select_overrides_updated(override)
