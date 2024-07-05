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


class PlotViewer(QMainWindow):
    MAX_POINTS = 10000
    DOWNSAMPLED_PRESENT = False
    TOTAL_POINTS_THRESHOLD = 40000

    def __init__(self, data: Dict[str, np.ndarray], in_pa: bool = False, norm: bool = False):
        """
        Initializes the view window.

        Args:
            fig (str): Plotly figure as a HTML string.
            in_pa (bool, optional): Indicates whether the view window is in PA mode. Defaults to False.
        """
        super().__init__()

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        self.norm = norm
        self.in_pa = in_pa

        if self.check_for_total_points(data):
            warm_msg = "The total number of measurements in the data exceeds the recommended threshold. The plot will likely not be displayed properly. For more information refer to the <a href='https://github.com/dietvin/pod5Viewer?tab=readme-ov-file#limitations'>Documentation</a>."
            QMessageBox.warning(self, "Large amounts of measurements", warm_msg)

        self.data = self.normalize_and_resample(data)
        self.single = len(self.data.keys()) == 1

        fig_str = self.create_plot()

        self.initUI()
        self.web_view.setHtml(fig_str)

        QApplication.restoreOverrideCursor()


    def check_for_total_points(self, data: Dict[str, np.ndarray]) -> bool:
        """
        Check if the total number of points in the data is greater than the maximum recommended points.

        Args:
            data (Dict[str, np.ndarray]): A dictionary containing the data arrays for each read ID.

        Returns:
            bool: True if the total number of points in the data is greater than the maximum allowed points, False otherwise.
        """
        total_points = 0
        for arr in data.values():
            if len(arr) > self.MAX_POINTS:
                total_points += self.MAX_POINTS
            else:  
                total_points += len(arr)
        return total_points > self.TOTAL_POINTS_THRESHOLD


    def normalize_and_resample(self, data: Dict[str, np.ndarray]) -> Dict[str, Tuple[np.ndarray, np.ndarray, bool]]:
        """
        Normalize and resample the data arrays.

        Returns:
            A dictionary containing the processed data arrays for each read ID.
            Each value in the dictionary is a tuple containing:
            - resampled_x: The normalized x-values of the resampled array.
            - resampled_arr: The resampled array.
            - downsampled: A boolean indicating whether the array was downsampled.
        """
        # Find the length of the longest array
        max_array_len = max(len(arr) for arr in data.values())
        
        processed_data = {}
        
        for read_id, arr in data.items():
            n = len(arr)
            
            # Normalize x-values from 0 to the ratio of its length to max_array_len
            normalized_x = np.linspace(0, n / max_array_len, n)

            downsampled = n > self.MAX_POINTS
            if downsampled:
                self.DOWNSAMPLED_PRESENT = True
                # Calculate the ideal chunk size
                chunk_size = n / self.MAX_POINTS
                
                # Create indices for the start of each chunk
                indices = [int(i * chunk_size) for i in range(self.MAX_POINTS)]
                # Add the last index to capture any remaining elements
                indices.append(n)
                
                resampled_arr = []
                resampled_x = []
                for i in range(self.MAX_POINTS):
                    start_idx = indices[i]
                    end_idx = indices[i + 1]
                    chunk_mean = np.median(arr[start_idx:end_idx])
                    resampled_arr.append(chunk_mean)
                    resampled_x.append(normalized_x[start_idx])
                
                # Ensure the last x-value is exactly 1 for the longest array
                if n == max_array_len:
                    resampled_x[-1] = 1.0
            else:
                # Use the original array and x-values if it's short enough
                resampled_arr = arr
                resampled_x = normalized_x
            
            if self.norm:
                resampled_arr = (resampled_arr - np.mean(resampled_arr)) / np.std(resampled_arr)
            
            processed_data[read_id] = (resampled_x, resampled_arr, downsampled)
        
        return processed_data
    

    def initUI(self):
        """
        Initializes the user interface for the main window.

        Sets the window title based on the value of `self.in_pa`.
        Sets the window geometry to (100, 100, 800, 600).
        Sets up a shortcut to close the window when CTRL+Q is pressed.
        Creates a QWebEngineView widget and sets its HTML content to `self.fig`.
        Sets the central widget of the main window to the QWebEngineView widget.
        Shows the main window.
        """
        self.setWindowTitle(f"{'Signal [pA]' if self.in_pa else 'Signal'}")
        self.setGeometry(100, 100, 800, 600)
        
        shortcut = QShortcut(QKeySequence("CTRL+Q"), self)
        shortcut.activated.connect(self.close)


        self.web_view = QWebEngineView(self)
        if self.DOWNSAMPLED_PRESENT:
            label = QLabel(f"Reads with more than {self.MAX_POINTS} measurements are downsampled to that number of measurements for plotting. Downsampled signal(s) are shown as dashed lines.")
            layout = QVBoxLayout()
            self.web_view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            layout.addWidget(self.web_view)
            layout.addWidget(label)
            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)
        else:
            self.setCentralWidget(self.web_view)


    def create_plot(self) -> str:
        """
        Creates a plot of the signal data for the specified read(s).

        Returns:
            str: The HTML representation of the plot.
        """
        fig = self.style_plot(go.Figure())
        for read_id, (x, y, downsampled) in self.data.items():
            fig.add_trace(go.Scatter(x=x, y=y, 
                                     name=read_id, 
                                     hovertemplate="Signal: %{y:.2f}<br>Time point: %{x}",
                                     line=dict(dash="dot" if downsampled else "solid")))

        return fig.to_html(include_plotlyjs="cdn")
    

    def style_plot(self, fig: go.Figure):        
        title = list(self.data.keys())[0] if self.single else "Current signals of all opened reads"
        if self.norm:
            ylabel = "Normalized signal"
        elif self.in_pa:
            ylabel = "Signal [pA]"
        else:
            ylabel = "Signal"

        fig.update_layout(
            template="seaborn",
            title=title,
            xaxis_title="Relative time point",
            yaxis_title=ylabel,
            font=dict(family="Open sans, sans-serif", size=20),
            plot_bgcolor="white",
            margin=dict(l=50, r=50, t=50, b=50)
        )
        fig.update_xaxes(
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            showticklabels=True,
            ticks='outside',
            showgrid=False,
            tickwidth=2
        )
        fig.update_yaxes(
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            showticklabels=True,
            ticks='outside',
            showgrid=False,
            tickwidth=2
        )
        return fig