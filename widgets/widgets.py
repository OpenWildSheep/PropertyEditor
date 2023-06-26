from __future__ import annotations

import re
from typing import TYPE_CHECKING

from PySide2 import QtCore, QtGui, QtWidgets

from EntityLibPy import EntityLib

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import ContainerPropertyItem


class MenuButton(QtWidgets.QPushButton):
    """Menu button, mostly for style."""

    def __init__(
        self,
        text: str,
        icon: str = None,
        menu_icon: bool = True,
        parent: QtWidgets.QWidget = None,
        size: int = 50,
        icon_size: int = 25,
    ):
        """Initialize."""
        super().__init__("", parent=parent)

        self.menu_icon = menu_icon
        self.icon_size = icon_size
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedSize(size, size)
        self.setToolTip(text)
        self.set_icon(icon)

    def set_icon(self, icon):
        icons_path = QtCore.QDir.searchPaths("icons")
        if self.menu_icon:
            icon = f"menu_{icon}"
        icon = f"{icons_path[0]}/{icon}.png"
        self.setIcon(QtGui.QIcon(icon))
        self.setIconSize(QtCore.QSize(self.icon_size, self.icon_size))


class PropSize(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setEnabled(False)
        self.setFixedWidth(40)

    def update(self):
        self.setText(str(self.parent().item.not_deleted_child_count()))

    def get(self):
        return int(self.text())


class EditorHBoxLayout(QtWidgets.QHBoxLayout):
    """Horizontal layout for editors."""

    def __init__(self, spacing=2, margin=0, parent=None):

        super().__init__(parent)
        self.setSpacing(spacing)
        self.setMargin(margin)


class RemoveButton(MenuButton):
    """Menu button, mostly for style."""

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__(
            "Remove", icon="bin2", size=22, icon_size=14, menu_icon=False, parent=parent
        )


class DebugButton(MenuButton):
    """Menu button, mostly for style."""

    show_icon = "debug_show"
    hide_icon = "debug_hide"

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        self.show_state = False
        super().__init__(
            "View debug",
            icon=self.show_icon,
            size=22,
            icon_size=14,
            menu_icon=False,
            parent=parent,
        )

    def update_state(self, state):
        self.show_state = state
        self.set_icon(None)

    def switch(self):
        self.show_state = not self.show_state
        self.set_icon(None)

    def set_icon(self, icon):
        if self.show_state:
            icon = self.hide_icon
        else:
            icon = self.show_icon

        super().set_icon(icon)


class EditorButton(QtWidgets.QPushButton):
    """Editor button, mostly for style."""

    def __init__(self, text: str, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__(text, parent=parent)

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMaximumWidth(100)


class AddRemoveButton(EditorButton):
    def __init__(self, text: str, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__(text, parent=parent)
        self.setFixedWidth(30)


class StylizedLineEdit(QtWidgets.QLineEdit):
    """Editor line edit, mostly for style."""

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__("", parent=parent)

        self.setCursor(QtCore.Qt.IBeamCursor)
        self.setStyleSheet("QtWidgets.QLineEdit {padding-left: 2}")


class DoubleSlider(QtWidgets.QSlider):
    """Double slider for float."""

    def __init__(self, decimals: int = 3, *args, **kargs):
        """Initialize."""
        super(DoubleSlider, self).__init__(*args, **kargs)
        self._multi = 10**decimals

        self.valueChanged.connect(self.emitDoubleValueChanged)

    def emitDoubleValueChanged(self):
        """Emit double value changed."""
        return float(super(DoubleSlider, self).value()) / self._multi

    def value(self):
        """Get value."""
        return float(super(DoubleSlider, self).value()) / self._multi

    def setMinimum(self, value: int):
        """Set minimum value."""
        return super(DoubleSlider, self).setMinimum(value * self._multi)

    def setMaximum(self, value: int):
        """Set maximum value."""
        return super(DoubleSlider, self).setMaximum(value * self._multi)

    def setSingleStep(self, value: int):
        """Set single step value."""
        return super(DoubleSlider, self).setSingleStep(value * self._multi)

    def singleStep(self):
        """Get single step."""
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def setValue(self, value: int):
        """Set value."""
        super(DoubleSlider, self).setValue(int(value * self._multi))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Key pressed event."""
        if event.key() == QtCore.Qt.Key_Control:
            self.setTickInterval(0.01)
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        """Key release event."""
        if event.key() == QtCore.Qt.ControlModifier:
            return

        super().keyReleaseEvent(event)


class ChoiceDialog(QtWidgets.QDialog):
    def __init__(
        self,
        prop: ContainerPropertyItem,
        style: str,
        parent: QtWidgets.QWidget = None,
        add_mode: bool = True,
    ):

        super().__init__(parent=parent)
        self.prop = prop
        self.add_mode = add_mode
        self.setStyleSheet(style)

        self.setWindowTitle("Make your choice")
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

        self.label = QtWidgets.QLabel(
            f"Choose which {self.prop.name} to {'add' if add_mode else 'remove'}", self
        )
        main_layout.addWidget(self.label)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Enter filter here")
        main_layout.addWidget(self.search_bar)

        self.combobox = BetterScrollComboBox(self)
        self.set_combobox_items()
        main_layout.addWidget(self.combobox)

        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.ok_btn = QtWidgets.QPushButton("Ok", self)
        self.ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_btn)

        self.cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        self.search_bar.textChanged.connect(self.set_combobox_items)

    def set_combobox_items(self):

        filter = self.search_bar.text().lower()
        if not filter:
            filter = re.compile(".*")
        else:
            filter = re.compile(filter.replace("*", ".*").replace("?", "."))

        if self.add_mode:
            items = self.prop.get_possible_child_items()
        else:
            items = [c.name for c in self.prop.get_not_deleted_child_items()]

        self.combobox.clear()
        self.combobox.addItems(sorted([i for i in items if filter.search(i.lower())]))


class FileTypeChooser(QtWidgets.QDialog):
    def __init__(
        self, entity_lib: EntityLib, style: str, parent: QtWidgets.QWidget = None
    ):

        self.combo_items = ["Entity"] + [
            d[:35] for d in entity_lib.schema.schema.definitions if d != "Entity"
        ]

        super().__init__(parent=parent)
        self.setStyleSheet(style)

        self.setWindowTitle("Make your choice")
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

        self.label = QtWidgets.QLabel("Choose which property type:", self)
        main_layout.addWidget(self.label)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Enter filter here")
        main_layout.addWidget(self.search_bar)

        self.combobox = BetterScrollComboBox(self)
        main_layout.addWidget(self.combobox)

        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.ok_btn = QtWidgets.QPushButton("Ok", self)
        self.ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.ok_btn)

        self.cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        self.combobox.addItems(self.combo_items)

        self.search_bar.textChanged.connect(self.set_combobox_items)

    def set_combobox_items(self):

        self.combobox.clear()

        filter = self.search_bar.text().lower()
        if filter:
            compiled_filter = re.compile(filter.replace("*", ".*").replace("?", "."))
            self.combobox.addItems(
                sorted(
                    [i for i in self.combo_items if compiled_filter.search(i.lower())]
                )
            )
        else:
            self.combobox.addItems(self.combo_items)


class BetterScrollComboBox(QtWidgets.QComboBox):
    """Simple combobox with scroll only when previously selected."""

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Set strong focus policy to avoid non-wanted scrolls."""
        super().__init__(parent=parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Scroll on combobox only if it has focus."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            self.parent().wheelEvent(event)


class EditorSpinbox(QtWidgets.QSpinBox):
    """Editor for int using a SpinBox."""

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        super().__init__(parent=parent)

        self.infinite_scroll_margin = 250
        self.ctrl_modifier = False
        self.setMinimum(int(-2147483647 - 1))
        self.setMaximum(int(2147483647))

        self.single_step_value = 1
        self.detailed_single_step_value = 1

    def init_drag(self, event: QtCore.QEvent):
        """Initialize drag."""
        self.mouse_start_pos_y = event.pos().y()
        self.start_value = self.value()

    def mousePressEvent(self, event: QtCore.QEvent):
        """Mouse press event."""
        super().mousePressEvent(event)
        self.init_drag(event)

    def mouseMoveEvent(self, event: QtCore.QEvent):
        """Mouse move event."""

        self.setCursor(QtCore.Qt.SizeVerCursor)
        self.setSingleStep(0)  # prevent incrementing by holding button during drag

        pos = event.localPos()
        new_pos = None
        if pos.y() < -self.infinite_scroll_margin:
            new_pos = self.infinite_scroll_margin

        elif pos.y() > self.infinite_scroll_margin:
            new_pos = -self.infinite_scroll_margin

        if new_pos:
            pos = QtCore.QPoint(0, new_pos)
            pos = self.mapToGlobal(pos)
            QtGui.QCursor.setPos(event.globalX(), pos.y())
            self.mouse_start_pos_y = new_pos
            self.start_value = self.value()
            return

        multiplier = self.single_step_value
        if event.modifiers() == QtCore.Qt.ControlModifier:
            if not self.ctrl_modifier:
                self.init_drag(event)
            self.ctrl_modifier = True
            multiplier = self.detailed_single_step_value
        else:
            if self.ctrl_modifier:
                self.init_drag(event)
            self.ctrl_modifier = False

        self.setSingleStep(self.single_step_value)
        value_offset = (self.mouse_start_pos_y - event.pos().y()) * multiplier
        new_value = self.start_value + value_offset

        # Update both editor and model
        # as the model is not updated correctly when scrolling too fast
        self.parent().set_editor_value(new_value)
        self.parent().set_model_value()

    def wheelEvent(self, event: QtCore.QEvent):
        """Wheel event."""
        event.ignore()


class EditorDoubleSpinbox(QtWidgets.QDoubleSpinBox, EditorSpinbox):
    """Editor for float using a DoubleSpinBox."""

    def __init__(self, parent: QtWidgets.QWidget = None):
        """Initialize."""
        QtWidgets.QDoubleSpinBox.__init__(self, parent=parent)

        self.update_model = False

        self.mouse_start_pos_y = 0
        self.start_value = 0
        self.infinite_scroll_margin = 250
        self.setDecimals(3)
        self.ctrl_modifier = False
        self.deselected = False

        self.single_step_value = 0.01
        self.detailed_single_step_value = 0.001

        self.setMinimum(-9.0e40)
        self.setMaximum(9.0e40)

    def textFromValue(self, value: float):
        """Get spinbox text from value.

        Supercharge default behaviour to avoid trailing zero(s)
        to match the decimal() value,
        as the user can't edit easily with them.
        """
        if QtCore.QLocale().decimalPoint() == ",":
            return str(value).replace(".", ",")
        else:
            return str(value).replace(",", ".")

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Override paint method to deselect text."""
        super().paintEvent(event)

        if not self.deselected:
            self.lineEdit().deselect()
            self.deselected = True

    def init_drag(self, event: QtCore.QEvent):
        """Initialize drag."""
        EditorSpinbox.init_drag(self, event)

    def mousePressEvent(self, event: QtCore.QEvent):
        """Mouse press event."""
        EditorSpinbox.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QtCore.QEvent):
        """Mouse move event."""
        EditorSpinbox.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event: QtCore.QEvent):
        """Mouse release event."""
        super().mouseReleaseEvent(event)
        self.setSingleStep(self.single_step_value)
        self.unsetCursor()

    def wheelEvent(self, event: QtCore.QEvent):
        """Wheel event."""
        event.ignore()
