import contextlib
import json
from pathlib import Path
from typing import Optional, Tuple

from PySide2 import QtCore, QtWidgets

from EntityLibPy import EntityLib, Property, Prop_PrefabInfo
from PySide2.QtCore import QModelIndex, Qt, QSettings, QDir
from PySide2.QtGui import QFontInfo, QFont, QColor, QPixmap
from PySide2.QtWidgets import QFileDialog

from PropertyEditor.model.model import Model
from PropertyEditor.properties._meta import (
    PropertyItem,
    ContainerPropertyItem,
    BaseItem,
)
from PropertyEditor.utils import timer
from PropertyEditor.widgets.tab import Tab
from PropertyEditor.widgets.tabs import Tabs
from PropertyEditor.widgets.treeview import TreeView
from PropertyEditor.widgets.widgets import FileTypeChooser
from PropertyEditor.widgets.window import EditorWindow
from PropertyEditor.config import Config
from PropertyEditor.editors.add_back import AddBackItem
from PropertyEditor.properties.other import InstanceOfItem

try:
    from PropertyEditor import user_callbacks
except ModuleNotFoundError:
    pass


class PropertyEditorApp:
    """Application class able to communicate with both EntityLib and PySide2.

    Used for nearly everything that needs both libraries.
    Also used for launch.
    """

    def __init__(self, entity_lib: EntityLib):
        self.config = Config()

        self.rawdata_path: Path = Path(str(entity_lib.rawdata_path))
        self.default_path: Path = Path(str(entity_lib.rawdata_path))

        self._set_sources_directories_for_qt()

        self.entity_lib = entity_lib
        self.window = EditorWindow(self)

    @staticmethod
    def get_style() -> str:
        """Get the style sheet for PropertyEditor"""
        style_path = QtCore.QDir.searchPaths("style")[0]
        style_file = Path(style_path, "style.qss")

        with open(style_file.as_posix()) as _style:
            style_data = _style.read()

        with open(Path(style_path, "style_vars.json").as_posix()) as sv:
            style_data_vars = json.load(sv)

        for key, value in style_data_vars.items():
            style_data = style_data.replace(key, value)

        return style_data

    @contextlib.contextmanager
    def save_context(self, file_path: str):
        try:
            user_callbacks.pre_save(file_path)
        except ModuleNotFoundError:
            pass

        yield

        try:
            user_callbacks.post_save(file_path)
        except ModuleNotFoundError:
            pass

    @contextlib.contextmanager
    def load_context(self, file_path: str):
        try:
            user_callbacks.pre_load(file_path)
        except ModuleNotFoundError:
            pass

        yield

        try:
            user_callbacks.post_load(file_path)
        except ModuleNotFoundError:
            pass

    def _set_sources_directories_for_qt(self):
        for search_key, path in [
            ("sources", None),
            ("icons", "icons"),
            ("style", "style"),
        ]:
            QtCore.QDir.addSearchPath(
                search_key,
                Path(self.config.src_path, path).as_posix()
                if path
                else self.config.src_path.as_posix(),
            )

    def _get_tabs(self) -> Tabs:
        return self.window.tabs

    def _get_tab(self) -> Tab:
        return self._get_tabs().currentWidget()

    def get_tree_view(self) -> TreeView:
        return self._get_tab().tree_view

    def get_rawdata_relative_path(self, path: Path) -> Path:
        if path.is_relative_to(str(self.rawdata_path)):
            return path.relative_to(self.rawdata_path)
        return path

    def _create_new_property(self) -> None:
        popup = FileTypeChooser(self.entity_lib, self.get_style())
        if not popup.exec_():
            return

        self.create_property(popup.combobox.currentText())

    def _create_new_tab(self, lib_prop: Property, loaded_file: Path = None):
        root_prop = ContainerPropertyItem(
            None,
            lib_prop,
            "Property",
            "Value",
        )
        root_prop.get_child_items()
        root_prop._config = self.config
        self.window.add_tab(Model(self, root_prop, loaded_file=loaded_file))
        print("Tab created!")

    def _get_decoration_color_for_prefab(self, prefab: Prop_PrefabInfo) -> QPixmap:
        if prefab.node.is_set:
            rgb = self.config.color.is_set
        elif prefab.node.is_default:
            rgb = self.config.color.default
        else:
            rgb = self.config.color.parent
        return self._get_decoration_pixmap(rgb)

    def _get_decoration_color(self, prop: PropertyItem, config: "Config") -> QPixmap:
        rgb = config.color.background
        if prop.is_set:
            rgb = config.color.is_set
        elif prop.is_default:
            if prop.data_kind not in config.container_types:
                rgb = config.color.default
        elif prop.has_prefab:
            if prop.is_local:
                rgb = config.color.local
            else:
                rgb = config.color.parent
        return self._get_decoration_pixmap(rgb)

    def _get_decoration_pixmap(self, rgb: Tuple[int, int, int]) -> QPixmap:
        color = QColor()
        color.setRgb(*rgb)
        pixmap = QPixmap(5, 20)
        pixmap.fill(color)
        return pixmap

    def _get_save_path(self, prop: PropertyItem) -> Optional[Path]:
        base_filter = "All (*.*)"

        dialog = QFileDialog()
        dialog.setDirectory(
            QSettings().value(self.config.default_dir_key)
            or self.rawdata_path.as_posix()
        )
        new_path = dialog.getSaveFileName(
            self.window,
            "Save file",
            QSettings().value(self.config.default_dir_key),
            base_filter,
        )

        if not new_path or not new_path[0]:
            return

        new_path = Path(new_path[0])

        QSettings().setValue(self.config.default_dir_key, new_path.parent.as_posix())

        return new_path

    def _already_loaded_file(self, file_path: Path) -> bool:
        for index in range(self._get_tabs().count()):
            widget = self._get_tabs().widget(index)
            if (
                widget.tree_view.source_model.loaded_file
                and widget.tree_view.source_model.loaded_file.as_posix()
                in file_path.as_posix()
            ):
                print("File already loaded")
                self._get_tabs().setCurrentWidget(widget)
                return True
        return False

    def _already_loaded_property(self, lib_property: Property) -> bool:
        for index in range(self._get_tabs().count()):
            widget = self.tabs.widget(index)
            if widget.tree_view.source_model.loaded_node == lib_property:
                print("Property already loaded")
                self._get_tabs().setCurrentWidget(widget)
                return True
        return False

    @timer
    def load_entity_from_ptr(self, lib_property: Property):
        """Load a Property from a Property point.

        Can be used to load a Property from a DCC for example instead of from a file.
        """
        if self._already_loaded_property(lib_property):
            return

        print(f"Loading Property, schema : {lib_property.schema.name}")
        self._create_new_tab(lib_property)

    @timer
    def load_file(self, file_path: Path):
        if self._already_loaded_file(file_path):
            return

        print(f"Loading {file_path}, schema : {file_path.suffix[1:]}")
        with self.load_context(file_path.as_posix()):
            lib_prop = self.entity_lib.load_property(file_path.as_posix())

        self._create_new_tab(lib_prop, loaded_file=file_path)

    @timer
    def reopen_file(self):
        loaded_file = self.get_tree_view().source_model.loaded_file
        self.save()
        self._get_tabs().close_current_tab()
        self.load_file(loaded_file)

    @timer
    def reload_file(self):
        loaded_file = self.get_tree_view().source_model.loaded_file
        self._get_tabs().close_current_tab()
        self.load_file(loaded_file)

    @timer
    def create_property(self, type_: str):
        print(f"Create property with schema : {type_}")
        lib_prop = Property.create(
            self.entity_lib,
            self.entity_lib.get_schema(type_),
        )
        self._create_new_tab(lib_prop)

    def save_to_prefab(self, prop: PropertyItem, path: str):
        prefab, file_path = prop.save_to_prefab(path)
        if prefab and file_path:
            with self.save_context(file_path.as_posix()):
                prefab.node.root_node.save(file_path.as_posix())

    def save_as(self) -> None:
        model = self.get_tree_view().source_model
        if model.loaded_file:
            base_path = model.loaded_file.parent
        else:
            base_path = Path(self.rawdata_path)

        file_types = "All (*.*)"

        dialog = QFileDialog()
        dialog.setDirectory(base_path.as_posix())
        new_path = dialog.getSaveFileName(
            self.window,
            "Save file",
            QSettings().value(self.config.default_dir_key),
            file_types,
        )

        if not new_path or not new_path[0]:
            return

        new_path = Path(new_path[0])

        QSettings().setValue(
            self.config.default_dir_key, QDir().absoluteFilePath(new_path.as_posix())
        )

        with self.save_context(new_path.as_posix()):
            model.loaded_item.lib_property.save(new_path.as_posix())

        model.loaded_file = new_path
        self._get_tab().set_file_name(new_path)
        self._get_tabs().update_current_tab_name()

    def save(self) -> None:
        current_tab = self._get_tab()

        if not current_tab:
            print("No property opened in the editor. Can't save.")
            return

        current_model: Model = self.get_tree_view().source_model
        loaded_property = current_model.loaded_item
        file_path = current_model.loaded_file

        if not loaded_property:
            raise Exception(
                "Current Tab's model has no root property. This should never happen."
            )

        if not file_path:
            file_path = self._get_save_path(loaded_property)
        else:
            if not current_tab.edited:
                print("Tab contains no edits. Don't save property.")
                return

            elif file_path.is_relative_to(str(self.rawdata_path)):
                file_path = Path(self.rawdata_path, file_path)

        if file_path:
            with self.save_context(file_path.as_posix()):
                loaded_property.lib_property.save(file_path.as_posix())

            current_model.loaded_file = file_path
            current_tab.set_file_name(file_path)
            self._get_tabs().set_current_tab_edited_and_update_name(False)

    def get_data(self, prop: PropertyItem, column: int, role: Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if column == 0:
                return prop.get_name()
            else:
                return prop.get_value()

        elif role == Qt.FontRole:
            font_size = 8
            font = QtWidgets.QApplication.font()
            font_family = QFontInfo(font).family()

            if prop.is_set:
                return QFont(font_family, font_size, QFont.Bold)
            elif not prop.has_prefab:
                font = QFont(font_family, font_size)
                font.setItalic(True)
                return font

            return QFont(font_family, font_size)

        elif role == Qt.ForegroundRole:
            color = QColor()
            color.setRgb(*prop.get_config_color(self.config))

            # Set alpha 0 to column 1 data
            # Avoid seeing text under custom widgets
            if column == 1:
                color.setAlpha(0)
            return color

        elif role == Qt.DecorationRole:
            if column != 0:
                return

            return self._get_decoration_color(prop, self.config)

        elif role == Qt.ToolTipRole:
            return prop.get_tooltip()

        # Used to sort proxy model items
        elif role == Qt.UserRole:
            return prop.sort_value

    def set_current_tab_edited(self) -> None:
        self._get_tabs().set_current_tab_edited_and_update_name()

    def update_row(self, source_index: QModelIndex, row: int) -> None:
        self.get_tree_view().update_row(source_index, row)
        self.set_current_tab_edited()

    @contextlib.contextmanager
    def keep_instance_of(self, prop: BaseItem, instance_of: Optional[str]):
        prop.instance_of = None
        yield
        if instance_of:
            prop.lib_property.instance_of = instance_of
            prop.add_instance_of()

    def revert_and_remove_child_rows(
        self, model: Model, prop: BaseItem, source_index: QModelIndex
    ):
        model.beginRemoveRows(source_index, 0, prop.child_count())
        prop.revert_to_prefab()
        prop.child_items = []
        model.endRemoveRows()

    def get_child_rows(self, model: Model, prop: BaseItem, source_index: QModelIndex):
        new_size = prop.lib_property.size - 1
        if prop.lib_property.instance_of:
            new_size += 1

        model.beginInsertRows(source_index, 0, new_size)
        prop.get_child_items()
        model.endInsertRows()

    def after_revert(self, prop: BaseItem, source_index: QModelIndex):
        prop.reset_editors()
        if hasattr(prop.editor, "updated"):
            prop.editor.updated()

        self.set_current_tab_edited()
        self.get_tree_view().set_index_editable(source_index)

    def revert_to_prefab(self, model: Model, prop: BaseItem, source_index: QModelIndex):
        # This is a dirty hack to add back deleted item
        # but this is due to PySide2 strange Model-Control system
        # that force us to launch control commands before and after updating the model
        # to make it work
        if prop.editor and isinstance(prop.editor, AddBackItem):
            prop.editor.add_back_item()
        elif isinstance(prop, InstanceOfItem):
            prop = prop.parent
            source_index = source_index.parent()

        with self.keep_instance_of(
            prop, prop.lib_property.instance_of if prop.lib_property else None
        ):
            self.revert_and_remove_child_rows(model, prop, source_index)

        self.get_child_rows(model, prop, source_index)
        self.after_revert(prop, source_index)

    def show_all_editors(self):
        self.get_tree_view().set_index_editable()

    def update_instance_of(self, source_index: QModelIndex, prop: BaseItem, value: str):
        if isinstance(value, str) and self.rawdata_path.as_posix() in value:
            value = value.replace(self.rawdata_path.as_posix() + "/", "")

        with self.window.keep_expanded_between_tabs():
            prop.lib_property.instance_of = value
            prop.value = value
            self.reopen_file()
            self.set_current_tab_edited()

    def allow_copy(self, prop: BaseItem) -> bool:
        return prop.allow_copy()

    def copy(self, prop: BaseItem) -> None:
        self.window.copy_data.set_copy_source(prop)

    def allow_paste(self, prop: BaseItem) -> bool:
        return prop.allow_paste(self.window.copy_data)

    def paste(self, prop: BaseItem, only_overrides=False) -> None:
        self.window.copy_data.paste_onto_property(prop, only_overrides=only_overrides)
        prop.reset_editors()
        self.set_current_tab_edited()
