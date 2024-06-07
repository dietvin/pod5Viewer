import sys, pod5, datetime, uuid
from typing import Any
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget
from PySide6.QtGui import QStandardItemModel, QStandardItem

def process_signal_rows(sig_rows: list[pod5.reader.SignalRowInfo]):
    row_dict = {}
    for i, row in enumerate(sig_rows, start=1):
        row_dict[str(i)] = members_to_dict(row)
    return row_dict

def members_to_dict(obj) -> dict[Any, Any]:
    obj_dict = {}

    members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]
    
    for member in members: 
        member_value = getattr(obj, member)

        if member == "signal_rows":
            obj_dict[member] = process_signal_rows(member_value)
        elif type(member_value) in [float, int, str, bool, dict, datetime.datetime, uuid.UUID]:
            obj_dict[member] = member_value
        elif type(member_value) == np.ndarray:
            obj_dict[member] = ", ".join([str(i) for i in member_value])
        else:
            obj_dict[member] = members_to_dict(member_value)

    return obj_dict

pod5_path = "/home/vincent/projects/inosine_detection/data/pod5_imb_niehrs_2023_22_dA/PAU44140_pass_8b98bb7f_f9191d76_1.pod5"
d = pod5.DatasetReader(pod5_path)
x = d.get_read("2456dbc4-5a75-43c8-8daf-1dc850b740f8")
data_dict = members_to_dict(x)

def populate_model(parent, data):
    for key, value in data.items():
        if isinstance(value, dict):
            item = QStandardItem(key)
            parent.appendRow(item)
            populate_model(item, value)
        else:
            key_item = QStandardItem(key)
            value_item = QStandardItem(str(value))
            parent.appendRow([key_item, value_item])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Dictionary QTreeView Example')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Key', 'Value'])
        self.tree_view.setModel(self.model)

        populate_model(self.model.invisibleRootItem(), data_dict)
        self.tree_view.expandAll()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
