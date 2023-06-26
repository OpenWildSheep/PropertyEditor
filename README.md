# PropertyEditor
Open source PySide2 GUI to manipulate EntityLib's properties.  

Get EntityLib from [here]().  
Can be used with the [PropertyGrapher]().

## Install

### Get repository

### Create virtual environment

Create a virtual environment using `venv`.  
Add requirements using `pip install -r requirements.txt`.  

You need to have built `EntityLib` and have `..\EntityLib\build\release` to your `PYTHONPATH`.  
You also need to have your `PropertyEditor` parent's folder to your `PYTHONPATH`.

To use the PropertyGrapher from the PropertyEditor, you need to have your `PropertyGrapher` parent's folder in your `PYTHONPATH`.

## Launch

Example (Windows):
```python
> cd path\to\PropertyEditor
> path\to\env\Scripts\activate
> python __main__.py path\to\your\rawdata path\to\your\schemas
```


## User callbacks

You can add custom callbacks for pre/post load/save.  
This way you can manage the files according to your pipeline or version control system.  

You need to have an available `user_callbacks` module that can contains any of the following functions:
```python
def pre_load(file_path: str) -> None:
    return


def post_load(file_path: str) -> None:
    return


def pre_save(file_path: str) -> None:
    return


def post_save(file_path: str) -> None:
    return
```
