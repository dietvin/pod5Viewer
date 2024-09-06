import numpy as np
from PySide6.QtCore import (Qt, QEvent, QAbstractTableModel, 
                            QModelIndex, QPersistentModelIndex)
from PySide6.QtWidgets import (QMainWindow, QTableView, QScrollBar, QVBoxLayout, 
                               QHBoxLayout, QWidget, QLabel, QHeaderView, 
                               QMessageBox, QFileDialog)
from PySide6.QtGui import QShortcut, QKeySequence
from typing import List
import math

class NumpyTableModel(QAbstractTableModel):
    def __init__(self, data: np.ndarray, rownames: List[int]|None = None, columnnames: List[int]|None = None, parent=None):
        super().__init__()
        self._data = data
        self._rownames = self.__get_header(rownames, self.rowCount())
        self._columnnames = self.__get_header(columnnames, self.rowCount())

    def __get_header(self, names: List[int]|None, data_shape: int):
        if names:
            if len(names) == data_shape:
                return names
        return [i for i in range(data_shape)]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        return self._data.shape[0]

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        return self._data.shape[1]

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self._data[index.row(), index.column()]
            # display only the rounded data
            if isinstance(value, (float, np.float64, np.float32)):
                return f"{round(value, NUM_DECIMALS)}"
            else:
                return str(value)
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        # only the row indices are useful here, so the column names are
        if role == Qt.DisplayRole:
            if orientation == Qt.Vertical and section < len(self._rownames):
                return self._rownames[section]  # Vertical header as row numbers
            if orientation == Qt.Horizontal and section < len(self._columnnames):
                return self._columnnames[section]
        return None
    

class ArrayTableViewer(QMainWindow):
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

        export_menu = menu.addMenu("&Export")
        export_menu.addAction("To numpy...", self.export)
        export_menu.addAction("To text...", lambda: self.export(to_npy=False))

        menu.addAction("&Help", self.show_help)


    def initUI(self):
        """
        Initializes UI elements, including the label showing the read ID, the table widget and the scroll bar.
        Elements are placed in layouts. After initializing the table widget, the dimensions are calculated 
        and the first bin is shown.
        """
        self.setWindowTitle(f"{'Signal [pA]' if self.in_pa else 'Signal'}")
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
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.installEventFilter(self)
        self.update_bin_attr()
        self.update_table()

    def init_scrollbar(self) -> None:
        """
        Initialize the scroll bar.
        """        
        self.scroll_bar = QScrollBar(Qt.Vertical)
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
        if watched == self.table_widget and event.type() in [QEvent.Wheel, QEvent.KeyPress]:
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

    def export(self, to_npy: bool = True) -> None:
        """
        Exports the full signal to a specified format.

        Args:
            to (str): target format. Must be either of: 'numpy', 'text'
        """

        extension = "npy" if to_npy else "txt"
        pa_label = "_pA" if self.in_pa else ""
        filename = f"{self.read_id}{pa_label}_export.{extension}"

        dialog = QFileDialog(self, "Export current view")
        dialog.selectFile(filename)

        if dialog.exec():
            outpath = dialog.selectedFiles()[0]
            if to_npy:
                self.export_npy(outpath)
            else:
                self.export_text(outpath)
    def export_npy(self, path: str):
        try:
            np.save(path, self.full_data, allow_pickle=False)
        except PermissionError:
            QMessageBox.critical(self, "Permission error", 
                                    f"Figure could not be exported. You do not have permissions to write to path {outpath}")
    
    def export_text(self, path: str):
        try:
            with open(path, "w") as f:
                f.write("\n".join(self.full_data.astype(str)))
        except PermissionError:
            QMessageBox.critical(self, "Permission error", 
                                    f"Figure could not be exported. You do not have permissions to write to path {outpath}")

    def show_help(self) -> None:
        """
        Displays a help message.
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowTitle("Help")
        help_dialog.setText(HELP_TEXT)
        help_dialog.setWindowTitle("Shortcuts")
        help_dialog.exec()
