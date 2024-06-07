from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QHBoxLayout, QWidget, QTreeWidget, QFileDialog
from PySide6.QtGui import QStandardItemModel, QStandardItem
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("pod5view")

        menubar = self.menuBar()
        main_menu = menubar.addMenu("File")
        main_menu.addAction("Open file(s)...", self.load_files)
        main_menu.addAction("Open directory...", self.load_directory)
        main_menu.addSeparator()
        main_menu.addAction("Exit", self.close)

        layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # left column to choose file and id
        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)

        # right column to show data
        self.data_viewer = QTreeView()

        layout.addWidget(self.file_navigator)
        layout.addWidget(self.data_viewer)

    def load_files(self):
        dialog = QFileDialog(self, "Select Files")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        if dialog.exec_():
            selected_files = dialog.selectedFiles()
            print("Selected files:", selected_files)
    
    def load_directory(self):
        dialog = QFileDialog(self, "Select Directory")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if dialog.exec_():
            selected_directory = dialog.selectedFiles()
            print("Selected directory:", selected_directory)
            
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
