from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem
import sys

# Sample dictionary
data = {
    "path1": ["wdawd", "dawfawf", "dfagesg"],
    "path2": ["hthhf", "gth", "hrdgesf"],
    "path3": ["htdrgerd", "öokjöl", "opijl"]
}

# Function to handle clicking on an ID item
def handle_item_click(item):
    item_id = item.text(0)
    print(f"Clicked item: {item_id}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Dynamic Tree View Example")
        self.setGeometry(100, 100, 400, 300)
        
        # Create a QTreeWidget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.setCentralWidget(self.tree_widget)
        
        # Populate the tree widget
        for path, items in data.items():
            path_item = QTreeWidgetItem([path])
            self.tree_widget.addTopLevelItem(path_item)
            
            for id_item in items:
                id_tree_item = QTreeWidgetItem([id_item])
                path_item.addChild(id_tree_item)
        
        # Connect item click event to the handle_item_click function
        self.tree_widget.itemClicked.connect(self.on_item_click)

    def on_item_click(self, item, column):
        if item.childCount() == 0:  # Check if the item is a leaf node (ID item)
            handle_item_click(item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
