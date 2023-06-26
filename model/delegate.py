from typing import Any, Union, Optional

from PySide2 import QtCore, QtWidgets


class Delegate(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        """Initialize."""
        super().__init__()
        self.scroll_area = None
        self.option = None

    def displayText(self, value: Any, locale: QtCore.QLocale) -> str:
        """Get display text.

        This function was enhanced to not display
        the result for the checkboxes (true, false)
        """
        result = super().displayText(value, locale)

        if result in ["true", "false"]:
            return ""

        return result

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> Optional[Union[QtWidgets.QWidget, None]]:
        """Create editor."""
        if not self.scroll_area:
            self.scroll_area = parent

        if not self.option:
            self.option = option

        if index.row() == -1:
            return None

        source_index = index.model().mapToSource(index)
        if source_index and source_index.row() != -1:
            return (
                source_index.model()
                .get_item(source_index)
                .create_editor(source_index, parent=parent)
            )

    def setEditorData(
        self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex
    ) -> None:
        editor.set_editor_value(index.data())

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.set_model_value()

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)
