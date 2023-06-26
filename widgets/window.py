from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide2.QtGui import QIcon

from EntityLibPy import CopyMode, OverrideValueSource

from PySide2 import QtCore, QtWidgets

from PropertyEditor.model.model import Model
from PropertyEditor.widgets.tabs import Tabs
from PropertyEditor.widgets.widgets import MenuButton

if TYPE_CHECKING:
    from PropertyEditor.app import PropertyEditorApp


class EditorWindow(QtWidgets.QMainWindow):
    def __init__(self, app: PropertyEditorApp):
        """Initialize."""
        super().__init__()
        self.app = app

        self.copy_data = CopyData()

        self.create_ui()
        self.setAcceptDrops(True)
        self.setMinimumSize(700, 700)
        self.setStyleSheet(app.get_style())
        self.default_folder: Optional[Path] = None
        self.graph_viewer_window = None

        self.setWindowIcon(QIcon(f"{QtCore.QDir.searchPaths('icons')[0]}/app3.png"))
        self.setWindowTitle("Property Editor")

    def create_ui(self) -> None:
        """Create UI."""
        main_frame = QtWidgets.QFrame(self)

        main_layout = QtWidgets.QHBoxLayout(main_frame)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setAlignment(QtCore.Qt.AlignLeft)

        left_frame = QtWidgets.QFrame()
        left_frame.setFixedWidth(60)
        main_layout.addWidget(left_frame)

        right_frame = QtWidgets.QFrame(main_frame)
        main_layout.addWidget(right_frame)

        left_frame_layout = QtWidgets.QVBoxLayout(left_frame)
        left_frame_layout.setSpacing(10)
        left_frame_layout.setMargin(5)
        left_frame_layout.setAlignment(QtCore.Qt.AlignLeft)
        left_frame_layout.setAlignment(QtCore.Qt.AlignTop)
        self.new_btn = MenuButton("Create new property", icon="new")
        self.open_btn = MenuButton("Open file", icon="open")
        self.save_btn = MenuButton("Save property", icon="save")
        self.close_btn = MenuButton("Close property", icon="close")
        self.open_graph_btn = MenuButton("Open dependencies graph", icon="graph")

        # Property grapher is another tool,
        # optional for the use of the Property editor
        # Load module here to avoid circular imports
        try:
            from PropertyGrapher.__main__ import create_gui_grapher
        except ModuleNotFoundError:
            self.open_graph_btn.setVisible(False)

        left_frame_layout.addWidget(self.new_btn)
        left_frame_layout.addWidget(self.open_btn)
        left_frame_layout.addWidget(self.save_btn)
        left_frame_layout.addWidget(self.close_btn)
        left_frame_layout.addWidget(self.open_graph_btn)

        right_frame_layout = QtWidgets.QVBoxLayout(right_frame)
        right_frame_layout.setAlignment(QtCore.Qt.AlignLeft)
        right_frame_layout.setAlignment(QtCore.Qt.AlignTop)

        self.tabs = Tabs(right_frame)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.tabs.tabBarClicked.connect(self.tabs.tab_clicked)

        right_frame_layout.addWidget(self.tabs)

        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.save_btn.customContextMenuRequested.connect(self.context_menu_save)
        self.close_btn.clicked.connect(self.tabs.close_current_tab)
        self.new_btn.clicked.connect(self.app._create_new_property)
        self.open_graph_btn.clicked.connect(self.open_graph)

        self.current_dir = QtCore.QDir()
        self.setCentralWidget(main_frame)

    def clear(self) -> None:
        """Clear all tabs."""
        self.tabs.clear()

    @contextlib.contextmanager
    def keep_expanded_between_tabs(self):

        expanded = []
        current_tab = self.tabs.currentWidget()
        if current_tab:
            expanded = current_tab.tree_view.get_expanded()

        yield

        current_tab = self.tabs.currentWidget()
        if current_tab and expanded:
            current_tab.tree_view.set_expanded(expanded)

    def add_tab_with_expand(self, model: Model) -> None:
        with self.keep_expanded_between_tabs():
            self.add_tab(model)

    def add_tab(self, model: Model) -> None:
        self.tabs.add_tab_as_current(model)

    def open_file(self) -> None:
        dialog = QtWidgets.QFileDialog()

        dialog.setDirectory(
            self.default_folder.as_posix()
            if self.default_folder
            else str(self.app.rawdata_path)
        )

        file_types = ""
        for file_type in self.app.config.file_types:
            file_types += "*" + file_type + " "

        file_name = dialog.getOpenFileName(
            self,
            "Open File",
            QtCore.QSettings().value(self.app.config.default_dir_key),
            f"Property file ({file_types})",
        )
        file_name = file_name[0]
        if not file_name:
            return
        QtCore.QSettings().setValue(
            self.app.config.default_dir_key,
            self.current_dir.absoluteFilePath(file_name),
        )
        self.app.load_file(Path(file_name))

    def open_property_at_path(self, property_path: str) -> None:
        self.tabs.currentWidget().open_property_at_path(property_path)

    def save_file(self) -> None:
        self.app.save()

    def select_save_as(self) -> None:
        self.app.save_as()

    def dropEvent(self, event: QtCore.QEvent) -> None:
        path = event.mimeData().urls()[0].path()

        # Need to clean path
        # as it may start with a /
        if path.startswith("/"):
            path = path[1:]

        self.app.load_file(Path(path))

    def dragEnterEvent(self, event: QtCore.QEvent) -> None:
        urls = event.mimeData().urls()

        if (
            urls
            and len(urls) == 1
        ):
            if not self.app.config.file_types or any(urls[0].path().endswith(i) for i in self.app.config.file_types):
                event.accept()
                return

        event.ignore()

    def context_menu_save(self, point: QtCore.QPoint) -> None:
        save_menu = QtWidgets.QMenu(self)

        save_as = QtWidgets.QAction("Save as", self)
        save_as.triggered.connect(self.select_save_as)
        save_menu.addAction(save_as)

        save_menu.exec_(self.save_btn.mapToGlobal(point))

    def open_graph(self) -> None:
        current_file = self.tabs.currentWidget().tree_view.source_model.loaded_file
        if not current_file:
            print(
                "No current file opened. Can't open graph."
            )
            return

        from PropertyGrapher.__main__ import create_gui_grapher

        self.graph_viewer_window = create_gui_grapher(
            self.app.entity_lib,
            tempfile.tempdir,
            file_path=current_file
        )


class CopyValue:
    """used to store data for copy-paste."""

    def __init__(self, item):
        self.kind = item.lib_property.schema.data_kind
        self.value = item.lib_property.value
        self.is_set = item.is_set


class CopyData:
    """Used to copy-paste data between nodes."""

    def __init__(self):
        self.reset()
        self.source = None

    @property
    def data_kind(self):

        if not self.source:
            return None

        return self.source.lib_property.schema.data_kind

    @property
    def enum_values(self):

        if not self.source:
            return None

        return self.source.lib_property.schema.enum_values

    @property
    def value(self):

        if not self.source:
            return None

        return self.source.lib_property.value

    def reset(self):
        self.kind = None
        self.data = []

    def set_copy_source(self, source):
        self.reset()
        self.source = source

    def paste_onto_property(self, destination, only_overrides=False):

        source_value = (
            OverrideValueSource.Any
            if not only_overrides
            else OverrideValueSource.Override
        )
        self.source.lib_property.copy_into(
            dest=destination.lib_property,
            copy_mode=CopyMode.CopyOverride,
            override_value_source=source_value,
        )
