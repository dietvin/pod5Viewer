import numpy as np
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QGridLayout, QWidget, QPushButton, QScrollArea, 
                               QSizePolicy, QLabel, QLineEdit, QMessageBox, 
                               QCheckBox, QFileDialog)
from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtGui import (QCursor, QPainter, QPen, QMouseEvent, QColor, 
                           QPixmap, QKeySequence, QShortcut, QPaintEvent,
                           QResizeEvent)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.backends.backend_svg # import only needed so pyinstaller adds the module (needed for SVG export)
import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, Tuple
import itertools, math, copy
from datetime import datetime

try:
    from pod5Viewer.constants.figureWindow_constants import (OVERVIEW_BIN_COUNT, COLOR_CYCLE, SUBSAMPLE_BIN_COUNT, 
                                                             WINDOW_TITLE, WINDOW_GEOMETRY, LEGEND_CHECKBOX_SIZE, 
                                                             EXPORT_FIG_SIZE, LABEL_PA_SUFFIX, ZOOM_LABEL_TEXT, 
                                                             ERROR_INVALID_ZOOM_INPUT, MESSAGE_NO_SUBSETTING, 
                                                             HELP_TEXT)
except ModuleNotFoundError:
    from constants.figureWindow_constants import (OVERVIEW_BIN_COUNT, COLOR_CYCLE, SUBSAMPLE_BIN_COUNT, 
                                                  WINDOW_TITLE, WINDOW_GEOMETRY, LEGEND_CHECKBOX_SIZE, 
                                                  EXPORT_FIG_SIZE, LABEL_PA_SUFFIX, ZOOM_LABEL_TEXT, 
                                                  ERROR_INVALID_ZOOM_INPUT, MESSAGE_NO_SUBSETTING, 
                                                  HELP_TEXT)


class OverviewWidget(QWidget):
    """
    A widget that provides an overview of data samples with zooming capabilities.

    This widget displays multiple data samples in a single view, allowing for
    easy comparison and analysis. It supports zooming into specific regions
    of the data and provides hover information for data points.

    Attributes:
        data (Dict[str, Tuple[np.ndarray, np.ndarray, str]]): Provided data subset to 1000 values for each read (key)
        data_scaled (Dict[str, Tuple[np.ndarray, np.ndarray, str]]): Data scaled to the pixel coordinates
        x_vals (np.ndarray): array of x-values (the same for all lines) 
        x_lims(Tuple[int, int]): Min and max x-values
        y_lims(Tuple[int, int]): Min and max y-values
        zoom_start_pos (int | None): First selected x-coordinate stored in the process of selection. 
                                     None if currently no selection is performed.
        zoom_end_pos (int | None): Second selected x-coordinate stored in the process of selection. 
                                   None if currently no selection is performed.
        current_start_pos (int | None): Start x-coordinate from previous selection. Stored to keep track of current zoom. 
                                        None if data is not zoomed in. 
        current_end_pos (int | None): End x-coordinate from previous selection. Stored to keep track of current zoom. 
                                      None if data is not zoomed in. 

    Signals:
        zoom_range_changed (float, float): Signal emitted once the zoom selection changes. Communicates the data ranges 
                                           that should be shown in the figure.
    """

    data: Dict[str, Tuple[np.ndarray, np.ndarray, str]]
    data_scaled: Dict[str, Tuple[np.ndarray, np.ndarray, str]]

    x_vals: np.ndarray

    x_lims: Tuple[int, int]
    y_lims: Tuple[int, int]

    zoom_start_pos: int | None
    zoom_end_pos: int | None

    current_start_pos: int | None
    current_end_pos: int | None

    zoom_range_changed = Signal(float, float)

    def __init__(self, data: Dict[str, Tuple[np.ndarray, np.ndarray, str]] | None = None) -> None:
        """
        Initialize the OverviewWidget.

        Args:
            data (Dict[str, Tuple[np.ndarray, np.ndarray, str]] | None): Optional data to initialize the widget with.
                Each key corresponds to one read, and the values are a tuple of
                (x-values, y-values, color) for each sample.
        """
        super().__init__()

        if data: 
            self.set_data(data)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)

        self.zoom_start_pos = None
        self.zoom_end_pos = None

        self.current_start_pos = None
        self.current_end_pos = None
        
        self.hover_label = QLabel(self)
        self.hover_label.setStyleSheet("background-color: rgba(255, 255, 255, 128); padding: 2px;")
        self.hover_label.hide()
        self.setMouseTracking(True)


    def set_data(self, data: Dict[str, Tuple[np.ndarray, np.ndarray, str]]) -> None:
        """
        Loads the data into the object and performs subsetting into 1000 bins.

        Args:
            data (Dict[str, Tuple[np.ndarray, np.ndarray, str]]): Dictionary containing the x- and y-values 
                                                                  (values) for each read_id (key)
        """
        self.x_vals = list(data.values())[0][0]
        data_len = len(self.x_vals) # arrays from all reads have the same length, because they were filled with NAs

        bin_count = OVERVIEW_BIN_COUNT
        bin_size = max(1, int(data_len / bin_count))
        
        max_y_vals = []
        min_y_vals = []
        data_subset = {}

        for read_id, (x,y,c) in data.items():
            max_y_vals.append(y[~np.isnan(y)].max())
            min_y_vals.append(y[~np.isnan(y)].min())

            if len(x) > bin_count:
                x_subset = x[::bin_size]
                y_subset = np.array([np.median(y[i:i+bin_size]) for i in range(0, len(y), bin_size)])
                data_subset[read_id] = (x_subset,y_subset,c)
            else:
                data_subset[read_id] = (x,y,c)

        self.x_lims = (0, data_len) # (x_min, x_max)
        self.y_lims = (min(min_y_vals), max(max_y_vals)) # (y_min, y_max)
        self.data = data_subset
        self.scale_to_size()

    def scale_to_size(self) -> None:
        """
        Scale the data so it fits into the widget coordinate system which is depending on the 
        current window size. Scales it in the following way:
        - original x-values (i.e. [0,1,...,n]) are scaled so 0 in x corresponds to 0 in the coordinate system
            and n corresponds to the width value
        - original y-values are similarly scaled by the height of the widget. (Note that the scaled values get inverted 
            to show up properly in the coordinate system)
        """
        data_scaled = {}
        
        width = self.width()
        height = self.height()
        
        for read_id, (time, signal, color) in self.data.items():
            time_scaled = self.scale_between(time, 0, width)
            # *-1 + height to account for flipped coordinate system in Qt
            signal_scaled = -(self.scale_between(signal, 0, height)) + height
            data_scaled[read_id] = (time_scaled, signal_scaled, color)
        
        self.data_scaled = data_scaled

    def scale_between(self, data: np.ndarray, a: int, b: int) -> np.ndarray:
        """
        Scale a NumPy array to a range between a and b. This function applies 
        min-max scaling to the input array and then scales and shifts the 
        result to fit within the range [a, b]. If the input array has only 
        one unique value, the function will return an array filled with the 
        value (a + b) / 2.

        Args:
            data (numpy.ndarray): The input array to be scaled.
            a (float): The minimum value of the scaled array.
            b (float): The maximum value of the scaled array.

        Returns:
            numpy.ndarray: A new array with the same shape as the input, 
                but with values scaled to the range [a, b].

        Raises:
            ValueError: If the input array is empty or if a == b.

        """
        if data.size == 0:
            raise ValueError("Input array is empty")
        if a == b:
            raise ValueError("a and b must be different")

        min_val = np.nanmin(data)
        max_val = np.nanmax(data)

        if min_val == max_val:
            return np.full_like(data, (a + b) / 2)

        scaled = a + (b - a) * (data - min_val) / (max_val - min_val)
        return scaled
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paints the widget, including the signals and the zoom selection rectangles.

        Args:
            event (QPaintEvent): The paint event.
        """
        height = self.height()
        width = self.width()

        painter = QPainter(self)

        # Draw the border
        painter.setPen(QPen(Qt.GlobalColor.black, 1))  # Set pen to black with width 2
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))  # Draw rectangle around the widget

        self.paint_signals(painter)

        # paint the grey rectangles that indicates the outside of the currently zoomed in interval
        if self.current_start_pos and self.current_end_pos:
            # beginning unselected region
            top_left = QPoint(0,0)
            bottom_right = QPoint(self.current_start_pos, height)
            rect = QRect(top_left, bottom_right)
            painter.fillRect(rect, QColor(127, 127, 127, 100))
            # end unselected region
            top_left = QPoint(self.current_end_pos,0)
            bottom_right = QPoint(width, height)
            rect = QRect(top_left, bottom_right)
            painter.fillRect(rect, QColor(127, 127, 127, 100))

        # paint the rectacle that indicates the currently selected zoom
        if self.zoom_start_pos and self.zoom_end_pos:
            x_start = min(self.zoom_start_pos, self.zoom_end_pos)
            x_end = max(self.zoom_start_pos, self.zoom_end_pos)
            rect = QRect(QPoint(x_start,0), QPoint(x_end, self.height()))
            painter.setPen(QPen(Qt.GlobalColor.black, 3, Qt.PenStyle.DashLine))
            painter.drawRect(rect)

    def paint_signals(self, painter: QPainter) -> None:
        for _, (time, signal, color) in self.data_scaled.items():
            # pA signals are of type np.float32 which causes errors when drawing the line
            time = time.astype(np.float64)
            signal = signal.astype(np.float64)
            for i in range(len(time)-1):
                x1 = time[i]
                y1 = signal[i]
                x2 = time[i+1]
                y2 = signal[i+1]
                if not np.isnan([y1,y2]).any():
                    painter.setPen(QColor(color))
                    painter.drawLine(x1, y1, x2, y2)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handles the resize event by scaling the data and updating the widget.

        Args:
            event (QResizeEvent): The resize event.
        """
        self.scale_to_size()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handles the mouse press event to start a zoom selection.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.zoom_start_pos = event.pos().x()
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handles the mouse move event to update the zoom selection or show the hover label.

        Args:
            event (QMouseEvent): The mouse move event.
        """
        x = event.pos().x()
        # in case the user hovers the mouse over the widget border to the left
        if x < 0: idx = 0
        # in case the user hovers the mouse over the widget border to the right
        idx = min(int(x / self.width() * self.x_lims[1]), len(self.x_vals)-1)
        coords = event.pos()
        coords.setY(coords.y()+25)
        self.hover_label.setText(f"{self.x_vals[idx]:.2f}")
        self.hover_label.move(coords)
        self.hover_label.show()

        if self.zoom_start_pos:
            self.zoom_end_pos = event.pos().x()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Handles the mouse release event to finalize a zoom selection.

        Args:
            event (QMouseEvent): The mouse release event.
        """
        if self.zoom_start_pos and event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

            start_x = min(self.zoom_start_pos, event.pos().x())
            end_x = max(self.zoom_start_pos, event.pos().x())

            if end_x == start_x:
                start_x -= 1
                end_x += 1
            elif end_x - start_x < 10:
                middle = int((end_x-start_x)/2)
                start_x = middle-1
                end_x = middle+1

            # make sure the selection does not exceed the boundaries
            x_min, x_max = self.x_lims
            start_x = max(x_min, start_x)
            end_x = min(x_max, end_x)

            start_ratio = start_x / self.width()
            end_ratio = end_x / self.width()
            self.zoom_range_changed.emit(start_ratio, end_ratio)

            self.current_start_pos = start_x
            self.current_end_pos = end_x

            self.zoom_start_pos = None
            self.zoom_end_pos = None
            self.update()

    def reset_zoom(self) -> None:
        """
        Resets the zoom to show the initial state.
        """
        self.current_start_pos = None
        self.current_end_pos = None
        self.update()

    def set_zoom(self, x1: int, x2: int) -> None:
        """
        Zoom into a specific region based. Expected values are x-values from the original data (not pixel coordinates).
        X-values are transformed into pixel coordinates and zooming is performed accordingly.

        Args:
            x1 (int): First limit of the interval
            x2 (int): Second limit of the interval 
        """
        x_min, x_max = self.x_lims
        
        # select the smaller value for x1 and the larger for x2
        x1 = min(x1, x2) 
        x2 = max(x1, x2)
        # make sure the selection does not exceed the boundaries
        x1 = max(x_min, x1)
        x2 = min(x_max, x2)

        # calculate the ratio of x1 and x2 within the total range of x_vals
        start_ratio = (x1 - x_min) / (x_max - x_min)
        end_ratio = (x2 - x_min) / (x_max - x_min)

        # convert ratios to pixel coordinates
        width = self.width()
        start_x = int(start_ratio * width)
        end_x = int(end_ratio * width)

        # emit the zoom range changed signal
        self.zoom_range_changed.emit(start_ratio, end_ratio)

        # update the current start and end positions
        self.current_start_pos = start_x
        self.current_end_pos = end_x

        # trigger a repaint
        self.update()


class FigureWindow(QMainWindow):
    """
    A window for visualizing multiple instances of time series data (i.e., plotting signals against time).
    Contains a figure, a legend, and an overview widget for data selection and zooming.

    Shown data is dynamically subsetted: the number of data points per signal shown never exceeds 10,000.
    If a signal interval contains more data points, the data is subset by binning into 10,000 bins and calculating the median for each bin.
    If an interval contains fewer data points, the signal is shown without subsetting.
    
    Attributes:
        data (Dict[str, Tuple[np.ndarray, np.ndarray, str]]): Full data (x-values, y-values, color) for each read.
        data_norm (Dict[str, Tuple[np.ndarray, np.ndarray, str]]): Full normalized data calculated from the full data.
        legend_selected (Dict[str, bool]): Dictionary storing whether a given read is currently visible or hidden.
        in_pa (bool): Indicates if data is in PA (used for labeling the y-axis in the plot).
        show_norm (bool): Determines if normalized data or raw data is shown in the plot and overview.
        current_start_ratio (float | None): Ratio corresponding to the relative position of the first data points shown in the current zoom.
                                            Stored to track the current zoom when redrawing the figure after toggling a legend item. 
                                            None if there is currently no zoom active. 
        current_end_ratio (float | None): Ratio corresponding to the relative position of the last data points shown in the current zoom.
                                          Stored to track the current zoom when redrawing the figure after toggling a legend item. 
                                          None if there is currently no zoom active. 
        fig (mpl.figure.Figure): Matplotlib figure showing the data.
        ax (mpl.axes._axes.Axes): Axes of the figure.
        canvas (FigureCanvas): Canvas containing the figure.
        overview_widget (OverviewWidget): Overview widget for zooming into specific regions.
        zoom_selection_x1_input (QLineEdit): Text input for the start of a zoom interval.
        zoom_selection_x2_input (QLineEdit): Text input for the end of a zoom interval.
        zoom_selection_enter_button (QPushButton): Button to trigger zooming based on input values.
        zoom_reset_button (QPushButton): Button to reset zoom.
        main_layout (QVBoxLayout): Layout containing all widgets.
    """
    data: Dict[str, Tuple[np.ndarray, np.ndarray, str]]
    data_norm: Dict[str, Tuple[np.ndarray, np.ndarray, str]]
    legend_selected: Dict[str, bool] # Dictionary storing the bool if a given read is currently visible or hidden

    in_pa: bool
    show_norm: bool # determines if data or data_norm (normalized) is shown in the plot and overview

    current_start_ratio: float | None # current ratio corresponding to the relative position of the first data points shown in the current zoom. 
                                    # Stored to track the current zoom when redrawing the figure after toggling a legend item 
    current_end_ratio: float | None 

    fig: mpl.figure.Figure
    ax: mpl.axes._axes.Axes

    canvas: FigureCanvas
    overview_widget: OverviewWidget
    zoom_selection_x1_input: QLineEdit
    zoom_selection_x2_input: QLineEdit
    zoom_selection_enter_button: QPushButton
    zoom_reset_button: QPushButton
    main_layout: QVBoxLayout

    def __init__(self, data: Dict[str, np.ndarray], in_pa: bool) -> None:
        """
        Initializes the FigureWindow with given data and configuration.

        Args:
            data (Dict[str, np.ndarray]): Dictionary containing time series data where the key is a read identifier
                                          and the value is an array of data points.
            in_pa (bool): Boolean indicating if data is in PA (used for labeling the y-axis in the plot).
        """
        super().__init__()

        self.in_pa = in_pa
        self.show_norm = False

        self.init_data(data)
        self.init_ui()

        # Ctrl+Q: Exit application
        exit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        exit_shortcut.activated.connect(self.close)

        # to keep track of the zoom in case the plot gets redrawn when a line gets disabled
        self.current_start_ratio = None
        self.current_end_ratio = None

        # initialize the plot
        self.update_plot()

    def init_data(self, data: Dict[str, np.ndarray]) -> None:
        """
        Initializes the data by sorting, normalizing, and preparing it for plotting.

        Args:
            data (Dict[str, np.ndarray]): Dictionary containing raw time series data.
        """
        if len(data.keys()) < 1:
            raise ValueError("Provided empty data dict.")
        
        data_sorted = dict(sorted(data.items(), key=lambda item: len(item[1]), reverse=True))

        colors = itertools.cycle(COLOR_CYCLE)
        
        max_len = max([len(s) for s in data_sorted.values()])

        data_full = {}
        data_norm = {}
        legend_selected = {}

        for read_id, signal in data_sorted.items():
            color = next(colors)
            # add NAs to fill all arrays to the same length (avoids indexing errors when zooming)
            if len(signal) < max_len:
                rest = np.empty(max_len-len(signal))
                rest[:] = np.nan
                signal = np.concatenate((signal, rest))
            x_vals = np.arange(max_len)

            data_full[read_id] = (x_vals, signal, color)
            data_norm[read_id] = (x_vals, self.normalize(signal), color)
            legend_selected[read_id] = True
            
        self.data = data_full
        self.data_norm = data_norm
        self.legend_selected = legend_selected

    def normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Normalizes the provided data by subtracting the mean and dividing by the standard deviation
        (z-score normalization).

        Args:
            data (np.ndarray): Array of data points to normalize.

        Returns:
            np.ndarray: Normalized data.
        """
        try:
            norm_data = (data - np.nanmean(data)) / np.nanstd(data)
        except:
            norm_data = np.zeros(len(data))
        return norm_data

    def init_ui(self) -> None:
        """
        Initializes the user interface components including menu bar, Matplotlib canvas, zoom controls, and layout.
        """
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(*WINDOW_GEOMETRY)

        # Set up the menu bar
        self.init_menubar()

        # Create the Matplotlib canvas
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # set up layout and checkboxes for the legend and fill the layout with them 
        legend_widget = self.init_legend()
        legend_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # set up and fill main layout 
        self.main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.canvas)
        top_layout.addWidget(legend_widget)

        bottom_layout = self.init_zoom_area()

        self.main_layout.addLayout(top_layout)
        self.main_layout.addLayout(bottom_layout)

        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)

        self.zoom_selection_x1_input.setFocus()

    def init_menubar(self) -> None:
        """
        Initialize the menu bar.
        """
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False) # activate menu bar on MacOS
        data_menu = menubar.addMenu("&Data")
        data_menu.addAction("Show normalized data", lambda: self.show_data(show_norm=True))
        data_menu.addAction("Show data", self.show_data)
        export_menu = menubar.addMenu("&Export")
        export_menu.addAction("Export current view...", self.export_current_view)
        menubar.addAction("&Help", self.show_help)

    def init_legend(self) -> QScrollArea:
        """
        Initialize the legend.
        """
        legend_widget = QScrollArea()
        legend_widget.setStyleSheet("""
            QScrollArea { 
                border: none; 
                }
            """)

        legend_widget.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        legend_contents = QWidget()
        legend_contents.setStyleSheet("""
            QWidget { border: 1px solid black; }
            QCheckBox { 
                border: none;
                margin: 5px;
                 }
            """)
        legend_layout = QVBoxLayout()

        legend_layout.setSpacing(1)  # Adjust this value as needed
        legend_layout.setContentsMargins(1,1,1,1)  # Adjust these values as needed

        for read_id, is_selected in self.legend_selected.items():
            legend_label = QCheckBox(text=read_id)
            legend_label.setChecked(is_selected)
            # add icon with the color from the plot as an idicator
            color = self.data[read_id][2]
            color_icon = QPixmap(*LEGEND_CHECKBOX_SIZE)
            color_icon.fill(QColor(color))
            legend_label.setIcon(color_icon)
            # connect signal when toggled
            legend_label.stateChanged.connect(self.toggle_signal)
            legend_layout.addWidget(legend_label)
        legend_contents.setLayout(legend_layout)
        legend_widget.setWidget(legend_contents)
        return legend_widget

    def init_zoom_area(self) -> QGridLayout:
        layout = QGridLayout()

        self.subset_label = QLabel()
        self.subset_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        zoom_label = QLabel(text=ZOOM_LABEL_TEXT)
        # set up input widgets and buttons for zooming
        self.zoom_selection_x1_input = QLineEdit()
        self.zoom_selection_x1_input.setPlaceholderText("From...")
        self.zoom_selection_x2_input = QLineEdit()
        self.zoom_selection_x2_input.setPlaceholderText("To...")
        zoom_selection_enter_button = QPushButton("Zoom")
        zoom_reset_button = QPushButton("Reset zoom")
        # initialize overview widget and fill it with fitting data
        self.overview_widget = OverviewWidget()
        if self.show_norm:
            self.overview_widget.set_data(self.data_norm)
        else:
            self.overview_widget.set_data(self.data)

        layout.addWidget(zoom_label, 0, 0)
        layout.addWidget(self.subset_label, 0, 2, 1, 2)
        layout.addWidget(self.overview_widget, 1, 0, 1,-1)
        layout.addWidget(self.zoom_selection_x1_input, 2, 0)
        layout.addWidget(self.zoom_selection_x2_input, 2, 1)
        layout.addWidget(zoom_selection_enter_button, 2, 2)
        layout.addWidget(zoom_reset_button, 2, 3)

        layout.setColumnStretch(0, 10)
        layout.setColumnStretch(1, 10)
        layout.setColumnStretch(2, 5)
        layout.setColumnStretch(3, 5)

        # connect signals
        self.overview_widget.zoom_range_changed.connect(self.update_plot)
        zoom_selection_enter_button.pressed.connect(self.zoom_in)
        zoom_reset_button.pressed.connect(self.reset_zoom)

        return layout

    def show_help(self) -> None:
        """
        Displays a help message.
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowTitle("Help")
        help_dialog.setText(HELP_TEXT)
        help_dialog.setWindowTitle("Shortcuts")
        help_dialog.exec()


    def update_plot(self, start_ratio=0.0, end_ratio=1.0) -> None:
        """
        Updates the plot based on the current zoom level and visibility of signals.

        Args:
            start_ratio (float, optional): The ratio of the start position of the zoomed-in data. Defaults to 0.0.
            end_ratio (float, optional): The ratio of the end position of the zoomed-in data. Defaults to 1.0.
        """
        self.ax.clear()

        def subsample_data(x, y) -> Tuple[np.ndarray, np.ndarray]:
            bin_size = max(1, int(len(x) / SUBSAMPLE_BIN_COUNT))
            
            self.update_subset_label(bin_size)

            x_subsampled = x[::bin_size]
            y_subsampled = np.array([np.median(y[i:i+bin_size]) for i in range(0, len(y), bin_size)])
            return x_subsampled, y_subsampled

        for read_id, (x, y, c) in self.get_current_data().items():
            if self.legend_selected[read_id]:
                start_idx = math.floor(len(x) * start_ratio)
                end_idx = math.ceil(len(x) * end_ratio)
                visible_x, visible_y = subsample_data(x[start_idx:end_idx], y[start_idx:end_idx])
                self.ax.plot(visible_x, visible_y, c=c, label=read_id)

        pa_suffix = LABEL_PA_SUFFIX if self.in_pa else ""
        y_label = f"{'Norm. ' if self.show_norm else ''}Signal intensity {pa_suffix}"
        self.ax.set_ylabel(y_label)
        self.fig.tight_layout()

        self.canvas.draw()

        self.current_start_ratio = start_ratio
        self.current_end_ratio = end_ratio

    def toggle_signal(self) -> None:
        """
        Toggles the visibility of a signal in the plot based on the checkbox state.

        Connects to the stateChanged signal of checkboxes in the legend.
        """
        sender = self.sender()
        is_checked = sender.isChecked()
        text = sender.text()

        self.legend_selected[text] = is_checked
        if self.current_start_ratio and self.current_end_ratio:
            self.update_plot(self.current_start_ratio, self.current_end_ratio)
        else:
            self.update_plot()

    def zoom_in(self) -> None: 
        """
        Zooms into the region specified by the input fields.

        Reads the start and end values from the input fields, validates them, and applies the zoom.
        If the inputs are invalid, displays an error message.
        """
        x1 = self.zoom_selection_x1_input.text()
        x2 = self.zoom_selection_x2_input.text()
        if len(x1)>0 and len(x1)>0:
            try:
                x1 = int(x1)
                x2 = int(x2)
            except ValueError:
                QMessageBox.critical(self, "Error", ERROR_INVALID_ZOOM_INPUT)
            else:
                self.overview_widget.set_zoom(x1, x2)

    def reset_zoom(self) -> None:
        """
        Resets the zoom level to show the entire data range and updates the overview widget.
        """
        self.update_plot()
        self.overview_widget.reset_zoom()

    def update_subset_label(self, bin_size: int):
        if bin_size <= 1:
            message = MESSAGE_NO_SUBSETTING
        else:
            message = f"Subsetting active - one point corresponds to {bin_size} measurements."
        self.subset_label.setText(message)

    def show_data(self, show_norm: bool = False) -> None:
        """
        Shows either the normalized data or the raw data in the plot and overview widget.

        Args:
            show_norm (bool, optional): If True, displays normalized data. If False, displays raw data. Defaults to False.
        """
        self.show_norm = show_norm
        self.overview_widget.set_data(self.get_current_data())

        if self.current_start_ratio and self.current_end_ratio:
            self.update_plot(self.current_start_ratio, self.current_end_ratio)
        else:
            self.update_plot()

    def get_current_data(self) -> Dict[str, Tuple[np.ndarray, np.ndarray, str]]:
        """
        Helper function that selects the data attribute that is currently selected to be shown
        (Normalized or unnormalized).

        Returns:
            Dict[str, Tuple[np.ndarray, np.ndarray, str]]: Dict containing the x-values, y-values 
                                                           and the color for each signal. 
        """
        if self.show_norm:
            current_data = self.data_norm
        else:
            current_data = self.data
        return current_data

    def export_current_view(self) -> None:
        """
        Exports the current view of the plot to an SVG file.

        Opens a file dialog to select the export location and filename.
        The figure is saved with the size of 10x6 inches and includes the legend.
        """
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_export.svg"

        dialog = QFileDialog(self, "Export current view")
        dialog.selectFile(filename)

        if dialog.exec():
            outpath = dialog.selectedFiles()[0]
            try:

                fig = copy.deepcopy(self.fig)
                fig.set_size_inches(*EXPORT_FIG_SIZE)
                ax = fig.get_axes()[0]
                ax.legend(bbox_to_anchor=(1,1))

                fig.tight_layout()
                fig.savefig(outpath)
            except PermissionError:
                QMessageBox.critical(self, "Permission error", 
                                     f"Figure could not be exported. You do not have permissions to write to path {outpath}")