import numpy as np
from PySide6.QtCore import (Qt, QEvent, QAbstractTableModel, 
                            QModelIndex, QPersistentModelIndex)
from PySide6.QtWidgets import (QMainWindow, QTableView, QScrollBar, QVBoxLayout, 
                               QHBoxLayout, QWidget, QLabel, QHeaderView, 
                               QMessageBox, QFileDialog)
from PySide6.QtGui import QShortcut, QKeySequence
from typing import List
import math

try:
    from pod5Viewer.constants.viewWindow_constants import (NUM_DECIMALS, CELL_WIDTH, CELL_HEIGHT, 
                                                           WINDOW_GEOMETRY, HELP_TEXT)
except ModuleNotFoundError:
    from constants.viewWindow_constants import (NUM_DECIMALS, CELL_WIDTH, CELL_HEIGHT, 
                                                WINDOW_GEOMETRY, HELP_TEXT)


class NumpyTableModel(QAbstractTableModel):
    """
    A table model for displaying NumPy arrays in a Qt view.

    The `NumpyTableModel` class acts as a bridge between NumPy arrays and Qt's table view.
    It allows NumPy data to be displayed efficiently in a tabular format, with support
    for row and column headers. The model also supports rounding of displayed numerical
    data.

    Attributes:
        _data (np.ndarray): The NumPy array containing the table data.
        _rownames (List[int]): The list of row indices used as row headers.
        _columnnames (List[int]): The list of column indices used as column headers.

    Methods:
        __init__(data, rownames, columnnames, parent): Initializes the model with NumPy data and optional headers.
        __get_header(names, data_shape): Helper method to generate default headers or use provided ones.
        rowCount(parent): Returns the number of rows in the model (corresponding to the data's shape).
        columnCount(parent): Returns the number of columns in the model (corresponding to the data's shape).
        data(index, role): Returns the data to be displayed at a given index, rounded to a specified number of decimals.
        headerData(section, orientation, role): Returns the appropriate header for the given section (row or column).
    """
    def __init__(self, data: np.ndarray, rownames: List[int]|None = None, columnnames: List[int]|None = None, parent=None):
        """
        Initializes the NumpyTableModel with data and optional row and column headers.

        Args:
            data (np.ndarray): The data to display, stored as a NumPy array.
            rownames (List[int], optional): A list of integers for the row headers. Defaults to None.
            columnnames (List[int], optional): A list of integers for the column headers. Defaults to None.
            parent: The parent object, if any. Defaults to None.
        """
        super().__init__()
        self._data = data
        self._rownames = self.__get_header(rownames, self.rowCount())
        self._columnnames = self.__get_header(columnnames, self.rowCount())

    def __get_header(self, names: List[int]|None, data_shape: int):
        """
        Generates default headers or uses provided ones for rows/columns.

        If a list of header names is provided and its length matches the data shape, it is used.
        Otherwise, it defaults to using a range based on the number of rows/columns.

        Args:
            names (List[int] | None): A list of header names or None for default.
            data_shape (int): The length of the header (number of rows or columns).

        Returns:
            List[int]: The list of header names (either provided or default).
        """
        if names:
            if len(names) == data_shape:
                return names
        return [i for i in range(data_shape)]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        """
        Returns the number of rows in the data.

        Args:
            parent (QModelIndex, optional): The parent index. Defaults to None.

        Returns:
            int: The number of rows in the data (first dimension of the array).
        """
        return self._data.shape[0]

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        """
        Returns the number of columns in the data.

        Args:
            parent (QModelIndex, optional): The parent index. Defaults to None.

        Returns:
            int: The number of columns in the data (second dimension of the array).
        """
        return self._data.shape[1]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the data for a given cell, formatted as a string and rounded if needed.

        If the data is a float, it is rounded to a specified number of decimal places
        (defined by the global `NUM_DECIMALS`). For other types, the data is simply converted
        to a string.

        Args:
            index (QModelIndex): The index of the cell.
            role (int, optional): The role to determine how data should be displayed. Defaults to Qt.DisplayRole.

        Returns:
            str | None: The data as a string, rounded if necessary, or None if invalid.
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            value = self._data[index.row(), index.column()]
            # display only the rounded data
            if isinstance(value, (float, np.float64, np.float32)): # type: ignore issue seems to be because is numpy types
                return f"{round(value, NUM_DECIMALS)}"
            else:
                return str(value)
        return None

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the header data for a given row or column section.

        Args:
            section (int): The section (row/column number) for which to return the header.
            orientation (Qt.Orientation): The orientation (vertical for rows, horizontal for columns).
            role (int, optional): The role for header display. Defaults to Qt.DisplayRole.

        Returns:
            str | None: The header value or None if invalid.
        """
        # only the row indices are useful here, so the column names are
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Vertical and section < len(self._rownames):
                return self._rownames[section]  # Vertical header as row numbers
            if orientation == Qt.Orientation.Horizontal and section < len(self._columnnames):
                return self._columnnames[section]
        return None
    

class ArrayTableViewer(QMainWindow):
    """
    A window for viewing large 1D NumPy arrays in a paginated table view.

    The `ArrayTableViewer` displays a large dataset (signal) stored in a 1D NumPy array.
    The data is divided into scrollable bins, with each bin displayed as a 2D table of
    customizable size. The class handles resizing events, automatically adjusting the table
    size and binning accordingly. The table supports vertical scrolling to navigate through
    the data and provides export functionality for saving the data as either a `.npy` or `.txt` file.

    Attributes:
        read_id (str): Identifier for the data (e.g., a read ID).
        in_pa (bool): Whether the signal is measured in picoamperes.
        full_data (np.ndarray): The full 1D signal data to be visualized.
        full_data_len (int): Length of the full data array.
        num_rows (int): Number of rows currently visible in the table.
        num_cols (int): Number of columns currently visible in the table.
        bin_size (int): The number of elements in each bin.
        n_bins (int): Total number of bins in which the data is split.

    Methods:
        init_shortcuts(): Initializes keyboard shortcuts (e.g., closing window with CTRL+Q).
        init_menu(): Initializes the menu bar with export and help options.
        initUI(): Sets up the user interface (table, scroll bar, layouts).
        init_table(): Sets up the QTableView for displaying the data.
        init_scrollbar(): Configures the vertical scroll bar for navigating the data.
        init_layout(): Arranges the UI elements in a layout.
        update_table(bin_idx): Updates the table view to show the bin of data at the specified index.
        update_bin_attr(): Recalculates the number of rows, columns, and bins based on the window size.
        eventFilter(watched, event): Redirects mouse wheel and keypress events from the table to the scroll bar.
        resizeEvent(event): Handles window resizing, recalculating table size and updating the view.
        update_scrollbar(): Updates the scroll bar to reflect the current number of bins.
        export(to_npy): Exports the data to a file (either `.npy` or `.txt`).
        export_npy(path): Saves the data in NumPy format.
        export_text(path): Saves the data as a text file.
        show_help(): Displays a help dialog with information about shortcuts.
    """
    read_id: str
    in_pa: bool
    full_data: np.ndarray
    full_data_len: int

    num_rows: int
    num_cols: int
    bin_size: int
    n_bins: int

    def __init__(self, data: np.ndarray, read_id: str, in_pa: bool = False):
        """
        Initializes the ArrayTableViewer with the , the corresponding
        read ID and whether the signal is in pA.

        Args:
            data (np.ndarray): full signal that should be displayed
            read_id (str): read ID corresponding to the signal
            in_pa (bool): True if the data is in pA
        """
        super().__init__()
        self.init_shortcuts()
        self.init_menu()

        self.read_id = read_id
        self.in_pa = in_pa

        self.full_data = data
        self.full_data_len = len(data)

        if self.full_data_len < 1:
            QMessageBox.critical(self, "Invalid data", "Empty data was provided.")

        self.initUI()

    def init_shortcuts(self) -> None:
        """
        Initializes shortcuts. Currently only the one for closing the window.
        """
        shortcut = QShortcut(QKeySequence("CTRL+Q"), self)
        shortcut.activated.connect(self.close)

    def init_menu(self) -> None:
        """
        Initializes the menu with export and help options.
        """
        menu = self.menuBar()
        menu.addAction("&Help", self.show_help)


    def initUI(self):
        """
        Initializes UI elements, including the label showing the read ID, the table widget and the scroll bar.
        Elements are placed in layouts. After initializing the table widget, the dimensions are calculated 
        and the first bin is shown.
        """
        self.setWindowTitle(f"pod5Viewer - View signal{' [pA]' if self.in_pa else ''}")
        self.setGeometry(*WINDOW_GEOMETRY)
        self.read_id_label = QLabel(f"Read ID: {self.read_id}")

        self.init_table()
        self.init_scrollbar()
        self.init_layout()
        
    def init_table(self) -> None:
        """
        Initialize the table view widget.
        """
        self.table_widget = QTableView()
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.installEventFilter(self)
        self.update_bin_attr()
        self.update_table()

    def init_scrollbar(self) -> None:
        """
        Initialize the scroll bar.
        """        
        self.scroll_bar = QScrollBar(Qt.Orientation.Vertical)
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(self.n_bins-1)
        self.scroll_bar.setSingleStep(1)
        self.scroll_bar.valueChanged.connect(self.update_table)

    def init_layout(self) -> None:
        """
        Place widgets in layouts and display these in the window.
        """
        layout = QHBoxLayout()
        layout.addWidget(self.table_widget)
        layout.addWidget(self.scroll_bar)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.read_id_label)
        main_layout.addLayout(layout)
        main_container = QWidget()
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)


    def update_table(self, bin_idx: int = 0) -> None:
        """
        Updates the table to the bin at the given index. Calculates the start and end index
        in the full data array. If the given bin is the last one of the data, the number of
        elements in the bin likely do not fit perfectly in the bin. If that is the case, the
        given data is padded with NAs at the end to reach the wanted bin size. 
        The (padded) chunk of the full data corresponding to the wanted bin is reshaped to
        fit the current number of rows and columns, the reshaped array is implemented into
        the model and shown in the table widget.

        Args:
            bin_idx (int): index of the bin that should be shown 
        """
        if bin_idx > self.n_bins-1:
            bin_idx = self.n_bins-1

        start_idx = bin_idx*self.bin_size
        end_idx = min((bin_idx+1)*self.bin_size, self.full_data_len)

        data_subset = self.full_data[start_idx:end_idx].astype(float)

        if data_subset.size < self.bin_size:
            padded_size = self.bin_size - data_subset.size
            data_subset = np.pad(data_subset, (0, padded_size), constant_values=np.nan)

        data_subset = data_subset.reshape(self.num_rows, self.num_cols)
        row_indices = [start_idx+i*self.num_cols for i in range(self.num_rows)]

        model = NumpyTableModel(data_subset, rownames=row_indices)
        self.table_widget.setModel(model)

    def update_bin_attr(self) -> None:
        """
        Calculates the number of rows and columns and updates the bin size and the number
        of bins accordingly.
        """
        table_height = self.table_widget.height()
        self.num_rows = max((table_height - table_height//4) // CELL_HEIGHT, 1)
        self.num_cols = max(self.table_widget.width() // CELL_WIDTH, 1)

        self.bin_size = self.num_rows * self.num_cols
        self.n_bins = math.ceil(self.full_data_len / self.bin_size)

    def eventFilter(self, watched, event):
        """
        Redirect activation of the mouse wheen and keypresses captured on the table widget
        to the scroll bar. Enables the use of the scroll bar without the need to hover over
        it.
        """
        if watched == self.table_widget and event.type() in [QEvent.Type.Wheel, QEvent.Type.KeyPress]:
            self.scroll_bar.event(event)
            return True
        return super().eventFilter(watched, event)  # Call base class method for other events
    
    def resizeEvent(self, event) -> None:
        """
        After resizing the window, if the dimensions change, the table dimensions get 
        recalculated and the data gets rebinned according to the new number of cells 
        shown in the window. The table is filled again and the scrollbar is updated to
        handle the new number of bins.
        """
        old_rows, old_cols = self.num_rows, self.num_cols
        self.update_bin_attr()
        if old_rows != self.num_rows or old_cols != self.num_cols:
            self.update_table()
            self.update_scrollbar()

    def update_scrollbar(self) -> None:
        """
        Sets the maximum value of the scroll bar to the last bin of the data. Resets the shown
        bin to the first one.
        """
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.setMaximum(self.n_bins-1)
        self.scroll_bar.setValue(0)

    def show_help(self) -> None:
        """
        Displays a help message.
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowTitle("Help")
        help_dialog.setText(HELP_TEXT)
        help_dialog.setWindowTitle("Shortcuts")
        help_dialog.exec()
