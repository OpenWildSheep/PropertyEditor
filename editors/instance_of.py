from __future__ import annotations

from pathlib import Path

from PropertyEditor.editors.path import EditorPath


class EditorInstanceOf(EditorPath):
    def _set_model_value(self):
        value = self.get_editor_value()
        if (not value and not self.item.value) or value == self.item.value:
            return

        if not Path(self.source_index.model().app.rawdata_path, value).is_file():
            return

        self.model.app.update_instance_of(self.source_index, self.item, value)
