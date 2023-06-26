from pathlib import Path

from PySide2 import QtCore, QtWidgets

from PropertyEditor.model.model import Model
from PropertyEditor.widgets.treeview import TreeView

DEFAULT_DIR_KEY = "default_dir"


class Tab(QtWidgets.QWidget):
    def __init__(self, model: Model):
        """Initialize."""
        super().__init__()

        self._label = None
        self._edited = False
        self.previous_search = ""
        self.previous_overrides_filter = "All"

        self._create_ui(model)
        self.set_file_name(model.relative_path)

    def update_edited_value(self, value: bool) -> bool:
        if value != self.edited:
            self.edited = value
            return True
        return False

    @property
    def edited(self):
        return self._edited

    @edited.setter
    def edited(self, value=True):
        self._edited = value

    @property
    def label(self) -> str:
        """Get tab label."""
        if self.edited:
            return self._label + "*"

        return self._label

    @label.setter
    def label(self, value):
        """Set tab label."""
        self._label = value

    def set_file_name(self, file_path: Path):
        if file_path:
            value_copy = Path(file_path)

            # Set file name widget to a shorter version
            # of the loaded file to keep it more readable.
            # To do so use 5 or less parents directories based on parents length
            x = 5 if len(value_copy.parents) - 1 > 4 else len(value_copy.parents) - 1
            short_path = value_copy.relative_to(value_copy.parents[x])

            self.file_name.setText(short_path.as_posix())
            self.file_name.setToolTip(file_path.as_posix())
            self.label = short_path.name
        else:
            self.file_name.setText("File not saved yet")
            self.file_name.setToolTip("")
            self.label = "No node"

    def _create_ui(self, model: Model):

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setMargin(0)
        main_layout.setSpacing(0)

        self.file_name = QtWidgets.QLabel("No node selected")
        self.file_name.setStyleSheet(
            "font-weight: bold; background-color: none; border: none;",
        )
        self.file_name.setFixedHeight(25)
        self.file_name.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.file_name)

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.setSpacing(5)
        main_layout.addLayout(search_layout)

        search_bar_label = QtWidgets.QLabel("Filter")
        search_bar_label.setStyleSheet("border: none; background-color: none;")
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Enter filter here")

        self.overrides_selector = QtWidgets.QComboBox()
        self.overrides_selector.addItem("All")
        self.overrides_selector.addItem("LocalOverrides")
        self.overrides_selector.addItem("Overrides")
        self.overrides_selector.setMinimumWidth(150)

        search_layout.addWidget(search_bar_label)
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.overrides_selector)

        self.tree_view = TreeView(model, parent=self)
        main_layout.addWidget(self.tree_view)

        self.overrides_selector.currentTextChanged.connect(
            lambda: self.tree_view.select_overrides_updated(
                self.overrides_selector.currentText()
            )
        )
        self.search_bar.returnPressed.connect(
            lambda: self.tree_view.set_search_filter(self.search_bar.text())
        )
        self.current_dir = QtCore.QDir()

    # def open_property_at_path(self, property_path: str) -> None:
    #     self.tree_view.open_property_at_path(property_path)

    def resizeEvent(self, event: QtCore.QEvent) -> None:
        """Resize and remove tree view maximum height limit."""
        self.tree_view.setMaximumHeight(10000)
        super().resizeEvent(event)

    def valid_remove(self):
        if self.edited:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setText("You made changes on this file.")
            message_box.setInformativeText(
                "Are you sure you want to close without saving it ?"
            )
            message_box.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
            )

            result = message_box.exec_()
            if result == QtWidgets.QMessageBox.Cancel:
                return False
        return True
