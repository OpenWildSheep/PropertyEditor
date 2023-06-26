import sys
from pathlib import Path

from EntityLibPy import EntityLib
from PySide2 import QtWidgets

from PropertyEditor.app import PropertyEditorApp
from PropertyEditor.widgets.window import EditorWindow


def main(entity_lib: EntityLib, file_to_open: str = None) -> int:
    q_app = QtWidgets.QApplication.instance()
    existing_app = bool(q_app)
    if not q_app:
        q_app = QtWidgets.QApplication(sys.argv)
        existing_app = False

    if file_to_open:
        # Check if Property Editor window already exists in the QApplication
        # Open the file and set the window as active
        for window in q_app.topLevelWidgets():
            if isinstance(window, EditorWindow):
                editor = window.app
                editor.load_file(Path(file_to_open))
                q_app.setActiveWindow(window)
                window.show()
                return 1

    editor = PropertyEditorApp(entity_lib)
    if file_to_open:
        editor.load_file(Path(file_to_open))

    editor.window.show()
    if not existing_app:
        return q_app.exec_()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("rawdata_path", help="Entity library rawdata_path")
    parser.add_argument("schema_path", help="Entity library schema path")
    parser.add_argument("-f", "--file", help="Specify file to open", type=str)
    args = parser.parse_args()

    main(EntityLib(args.rawdata_path, args.schema_path), file_to_open=args.file)
