import numpy as np
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QScrollBar, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy, QApplication, QMessageBox
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWebEngineWidgets import QWebEngineView
from typing import Dict, Tuple
import plotly.graph_objects as go


class ArrayTableViewer(QMainWindow):
    def __init__(self, array: np.ndarray, read_id: str, in_pa: bool = False, chunk_size=100, rows=10, columns=10):
        """
        Initializes a ViewWindow object.

        Parameters:
        - array (np.ndarray): The input array to be displayed in the view window.
        - read_id (str): The ID of the read associated with the array.
        - in_pa (bool): Flag indicating whether the array is in PA (pixel array) format. Default is False.
        - chunk_size (int): The size of each chunk when displaying the array. Default is 100.
        - rows (int): The number of rows to display in the view window. Default is 10.
        - columns (int): The number of columns to display in the view window. Default is 10.
        """
        super().__init__()

        self.array = array
        self.read_id = read_id
        self.in_pa = in_pa
        self.chunk_size = chunk_size
        self.rows = rows
        self.columns = columns
        self.total_elements = len(self.array)
        self.total_chunks = (self.total_elements + self.chunk_size - 1) // self.chunk_size
        
        self.initUI()
    
    def initUI(self):
        """
        Initializes the user interface for the view window.

        This method sets up the window title, creates and configures the table widget,
        sets up the scroll bar, and defines the layout of the widgets.

        Parameters:
        None

        Returns:
        None
        """
        self.setWindowTitle(f"{'Signal [pA]' if self.in_pa else 'Signal'}")
        
        self.read_id_label = QLabel(f"Read ID: {self.read_id}")

        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(self.rows)
        self.table_widget.setColumnCount(self.columns)        
        
        # Resize columns and rows to fit contents
        cell_width = 75
        cell_height = 20
        
        self.table_widget.horizontalHeader().setDefaultSectionSize(cell_width)
        self.table_widget.verticalHeader().setDefaultSectionSize(cell_height)

        self.scroll_bar = QScrollBar(Qt.Vertical)

        # Setup scroll bar
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(self.total_chunks - 1)
        self.scroll_bar.setSingleStep(1)
        self.scroll_bar.valueChanged.connect(self.update_display)
        self.table_widget.installEventFilter(self)
       
        # Initial display
        self.update_display(0)
        
        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.scroll_bar)
        
        container = QWidget()
        container.setLayout(layout)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.read_id_label)
        main_layout.addWidget(container)

        main_container = QWidget()
        main_container.setLayout(main_layout)

        self.setCentralWidget(main_container)
        
        # Adjust the window size to fit the table perfectly
        self.adjust_window_size(cell_width, cell_height)

        shortcut = QShortcut(QKeySequence("CTRL+Q"), self)
        shortcut.activated.connect(self.close)

        shortcut_page_up = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        shortcut_page_up.activated.connect(lambda: self.scroll_bar.setValue(self.scroll_bar.value() - self.scroll_bar.pageStep()))

        shortcut_page_down = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        shortcut_page_down.activated.connect(lambda: self.scroll_bar.setValue(self.scroll_bar.value() + self.scroll_bar.pageStep()))

        shortcut_arrow_up = QShortcut(QKeySequence(Qt.Key_Up), self)
        shortcut_arrow_up.activated.connect(lambda: self.scroll_bar.setValue(self.scroll_bar.value() - self.scroll_bar.singleStep()))

        shortcut_arrow_down = QShortcut(QKeySequence(Qt.Key_Down), self)
        shortcut_arrow_down.activated.connect(lambda: self.scroll_bar.setValue(self.scroll_bar.value() + self.scroll_bar.singleStep()))
    
    def eventFilter(self, watched, event):
        if watched == self.table_widget and event.type() == QEvent.Wheel:
            self.scroll_bar.event(event)  # Redirect wheel event to the scroll bar
            return True  # Event handled    
        return super().eventFilter(watched, event)  # Call base class method for other events
    
    def adjust_window_size(self, cell_width, cell_height):
        """
        Adjusts the size of the main window based on the provided cell width and height.

        Args:
            cell_width (int): The width of each cell in the table.
            cell_height (int): The height of each cell in the table.
        """
        # Calculate the total width and height of the table
        table_width = cell_width * self.columns + self.table_widget.verticalHeader().width()
        table_height = cell_height * self.rows + self.table_widget.horizontalHeader().height()
        
        # Include scrollbar width if necessary
        scroll_bar_width = self.scroll_bar.sizeHint().width()
        id_height = self.read_id_label.sizeHint().height()

        # Calculate total window size
        total_width = table_width + scroll_bar_width + 60
        total_height = table_height + id_height + 95 
        
        # Adjust the size of the main window
        self.resize(total_width, total_height)
    
    def update_display(self, chunk_index):
        """
        Update the display of the table widget with data from the specified chunk.

        Args:
            chunk_index (int): The index of the chunk to display.

        Returns:
            None
        """
        # Clear the current table contents
        self.table_widget.clearContents()
        
        # Get the start and end indices for the chunk
        start_index = chunk_index * self.chunk_size
        end_index = min(start_index + self.chunk_size, self.total_elements)
        
        # Populate the table with the chunk's data
        for i in range(self.rows):
            for j in range(self.columns):
                array_index = start_index + (i * self.columns + j)
                if array_index < end_index:
                    value = self.array[array_index]
                    item = QTableWidgetItem(str(value))
                    self.table_widget.setItem(i, j, item)
                else:
                    # If we run out of data, stop filling the table
                    break