from PropertyEditor.editors.add_child import EditorChildrenManager


class EditorAddArrayChild(EditorChildrenManager):
    """Editor allowing user to add a new child property to an DataKind.array."""

    def _get_editor_value(self) -> None:
        return None

    def add_row(self) -> None:
        if self.model.add_child(self.source_index, None):
            self.updated()

    def remove_row(self) -> None:
        row = self.item.child_count() - 1
        if row is not None and self.model.remove_child(self.source_index, row):
            self.updated()
