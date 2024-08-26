from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QHBoxLayout, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox, QTabWidget, QLineEdit, QComboBox, QMenuBar, QPushButton
from PySide6.QtGui import QStandardItemModel, QStandardItem, QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, Signal
import sys, pathlib
from typing import List, Dict

from pod5Viewer.dataHandler import DataHandler

class FileNavigator(QWidget):
    
    itemSelectionChanged = Signal()
    itemDoubleClicked = Signal(QTreeWidgetItem, int)
    itemActivated = Signal(QTreeWidgetItem, int)
    
    def __init__(self):
        super().__init__()
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.clear_search_button = QPushButton("X")
        self.sort_combo = QMenuBar()
        sort_menu = self.sort_combo.addMenu("Sort...")

        sort_menu_asc = sort_menu.addMenu("Ascending...")
        sort_menu_desc = sort_menu.addMenu("Descending...")

        sort_menu_asc.addAction("All", lambda: self.sort_items(level=3, order="a"))
        sort_menu_asc.addAction("Files", lambda: self.sort_items(level=1, order="a"))
        sort_menu_asc.addAction("Reads", lambda: self.sort_items(level=2, order="a"))
        sort_menu_desc.addAction("All", lambda: self.sort_items(level=3, order="d"))
        sort_menu_desc.addAction("Files", lambda: self.sort_items(level=1, order="d"))
        sort_menu_desc.addAction("Reads", lambda: self.sort_items(level=2, order="d"))

        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)

        hlayout.addWidget(self.search_input)
        hlayout.addWidget(self.clear_search_button)
        hlayout.addWidget(self.sort_combo)

        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.file_navigator)

        self.setLayout(vlayout)
        
        self.file_navigator.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.file_navigator.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.file_navigator.itemActivated.connect(self.itemActivated)

    def addTopLevelItem(self, item: QTreeWidgetItem):
        self.file_navigator.addTopLevelItem(item)

    def clear(self):
        self.file_navigator.clear()

    def fill(self, id_path_dict: Dict[str, List[str]]):
        for path, items in id_path_dict.items():
            path_item = QTreeWidgetItem([path])
            path_item.setToolTip(0,path)
            self.file_navigator.addTopLevelItem(path_item)

            for id_item in items:
                id_tree_item = QTreeWidgetItem([id_item])
                path_item.addChild(id_tree_item)


    def sort_items(self, level: int, order: str):
        sort_order = Qt.SortOrder.AscendingOrder if order == "a" else Qt.SortOrder.DescendingOrder

        # Sort first level
        if level == 1 or level == 3:
            is_expanded = [self.file_navigator.topLevelItem(i).isExpanded() for i in range(self.file_navigator.topLevelItemCount())]
            root_items = [self.file_navigator.takeTopLevelItem(0) for _ in range(self.file_navigator.topLevelItemCount())]
            items_comb = [(item, expanded) for item, expanded in zip(root_items, is_expanded)]

            sorted_items_comb = sorted(items_comb, key=lambda pair: pair[0].text(0), reverse=(sort_order == Qt.SortOrder.DescendingOrder))
            
            for i, (item, was_expanded) in enumerate(sorted_items_comb):
                self.file_navigator.addTopLevelItem(item)
                self.file_navigator.topLevelItem(i).setExpanded(was_expanded)

        # Sort second level
        if level == 2 or level == 3:
            for i in range(self.file_navigator.topLevelItemCount()):
                parent_item = self.file_navigator.topLevelItem(i)
                child_items = [parent_item.child(j) for j in range(parent_item.childCount())]
                sorted_child_items = sorted(child_items, key=lambda item: item.text(0), reverse=(sort_order == Qt.SortOrder.DescendingOrder))
                for j in range(len(child_items)):
                    parent_item.takeChild(0)
                for child in sorted_child_items:
                    parent_item.addChild(child)
        # sort read ids in each file while keeping the order of the overall files
 
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.file_navigator = FileNavigator()
        self.setCentralWidget(self.file_navigator)

        self.file_navigator.itemSelectionChanged.connect(self.handle_selection_change)
        self.file_navigator.itemDoubleClicked.connect(self.handle_item_double_click)
        self.file_navigator.itemActivated.connect(self.handle_item_activated)

        self.model = None

        self.load_files(["/home/vince/pod5Viewer/test_data/multi_fast5_zip_v0.pod5", "/home/vince/pod5Viewer/test_data/multi_fast5_zip_v2.pod5"])

    def handle_selection_change(self):
        print("Selection changed in TestWindow")

    def handle_item_double_click(self, item, column):
        print(f"Item double-clicked in TestWindow: {item.text(column)}")

    def handle_item_activated(self, item, column):
        print(f"Item activated in TestWindow: {item.text(column)}")


    def load_files(self, file_paths: List[str]) -> None:
        """
        Loads the specified POD5 files and updates the file navigator with their read IDs.

        Args:
            file_paths (List[str]): A list of file paths to POD5 files to be loaded.
        """
        # clear the file navigator and data viewer
        self.file_navigator.clear()
        self.model = QStandardItemModel()

        self.data_handler = DataHandler([pathlib.Path("/home/vince/pod5Viewer/test_data/multi_fast5_zip_v0.pod5"), pathlib.Path("/home/vince/pod5Viewer/test_data/multi_fast5_zip_v2.pod5")])
        file_navigator_data = self.data_handler.ids_to_path()
        self.file_navigator.fill(file_navigator_data)

def main():
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
