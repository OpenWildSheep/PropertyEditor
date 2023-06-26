from __future__ import annotations

from typing import Any, TYPE_CHECKING

from PySide2 import QtCore, QtWidgets

from PropertyEditor.model.model import Model

if TYPE_CHECKING:
    from PropertyEditor.properties._meta import BaseItem


def lock_model_update(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        self.update_model = False
        func(*args, **kwargs)
        self.update_model = True

    return wrapper


def update_model(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.update_model:
            func(*args, **kwargs)

    return wrapper


class BaseEditor(QtWidgets.QWidget):
    """This class is meant to be used with a QWidget."""

    def __init__(
        self,
        item: BaseItem,
        source_index: QtCore.QModelIndex,
        parent: QtWidgets.QWidget = None,
    ):
        super().__init__(parent=parent)
        self.item = item
        self.source_index = source_index
        self.related = []

        # As set_editor_value() is automatically triggered by the Model() to
        # set the editor's data, but as we don't want to update the property's value
        # at that time, we need to deactivate the model's update.
        # This attribute is managed by update_model() and lock_model_update() decorators
        # to activate or deactivate model's update when we need
        self.update_model = False

    @property
    def model(self) -> Model:
        # # A bug sometimes happen, and we can't found why:
        # #  the source_index.model() is replaced by a Model instance
        # #  If this happens again, uncomment next lines
        # #  if you need a quick and dirty solution
        # if isinstance(self.source_index.model, Model):
        #     return self.source_index.model
        return self.source_index.model()

    @lock_model_update
    def set_editor_value(self, data: Any):
        self._set_editor_value(data)

    @update_model
    def set_model_value(self, *args):
        self._set_model_value()

    def get_editor_value(self):
        return self._get_editor_value()

    def _set_model_value(self):
        value = self.get_editor_value()
        self.model.set_item_value(self.item, value)
        for related in self.related:
            related.set_editor_value(value)

    def _get_editor_value(self):
        raise NotImplementedError

    def _set_editor_value(self, value):
        raise NotImplementedError

    def create_related_connection(
        self, child_property: BaseItem, child_index: QtCore.QModelIndex
    ):

        # Ensure child has his own editor before creating the MultiChild one
        if not child_property.editor:
            child_property.create_editor(child_index)

        editor = child_property.get_editor(child_index)
        editor.set_editor_value(child_property.value)

        child_property.editor.related.append(editor)
        editor.related.append(child_property.editor)
        return editor

    def update_parent_editor_size(self):
        self.item.parent.editor.prop_size.update()
        if hasattr(self.item.parent.editor, "set_remove_button_visibility"):
            self.item.parent.editor.set_remove_button_visibility()
