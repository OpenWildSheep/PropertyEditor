from PySide2 import QtCore, QtWidgets

from PropertyEditor.model.model import Model
from PropertyEditor.widgets.tab import Tab


class Tabs(QtWidgets.QTabWidget):
    def update_current_tab_name(self):
        self.setTabText(self.currentIndex(), self.currentWidget().label)

    def set_current_tab_edited_and_update_name(self, edited: bool = True) -> None:
        if not self.currentWidget():
            return
        if self.currentWidget().update_edited_value(edited):
            self.update_current_tab_name()

    def add_tab(self, model: Model) -> Tab:
        widget = Tab(model)
        self.addTab(widget, widget.label)
        self.setTabText(self.indexOf(widget), widget.label)
        return widget

    def add_tab_as_current(self, model: Model) -> None:
        widget = self.add_tab(model)
        self.setCurrentWidget(widget)

    def close_current_tab(self) -> None:
        self.removeTab(self.currentIndex())

    def removeTab(self, index: int) -> None:
        if not self.widget(index).valid_remove():
            return
        super().removeTab(index)

    def clear(self) -> None:
        for i in reversed(range(self.count())):
            self.removeTab(i)

    def tab_clicked(self, index: int):
        self.clicked_index = index

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == QtCore.Qt.MidButton:
            self.removeTab(self.clicked_index)
        super(Tabs, self).mouseReleaseEvent(event)
