from PySide2 import QtCore, QtWidgets

from PropertyEditor.editors._meta import BaseEditor
from PropertyEditor.properties._meta import ContainerPropertyItem


class EditorCheckbox(QtWidgets.QCheckBox, BaseEditor):
    def __init__(
        self,
        prop: ContainerPropertyItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        """Initialize."""
        QtWidgets.QCheckBox.__init__(self, parent=parent)
        self.source_index = source_index
        self.item = prop
        self.related = []

        self._set_options()

    def _set_model_value(self):
        BaseEditor._set_model_value(self)

    def _set_options(self) -> None:
        self.stateChanged.connect(self.set_model_value)

    def _get_editor_value(self) -> bool:
        return True if self.checkState() == QtCore.Qt.Checked else False

    def _set_editor_value(self, value: bool) -> None:
        self.setChecked(value)
