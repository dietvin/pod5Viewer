from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QHBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWebEngineWidgets import QWebEngineView
import sys, os, pod5, pathlib, datetime, uuid, yaml
from typing import Dict, List, Any
import numpy as np
import plotly.graph_objects as go

try:
    from help_strings import HELP
    from __version__ import __version__

except:
    from pod5Viewer.help_strings import HELP
    from pod5Viewer.__version__ import __version__

class DataHandler:
    """
    Handles data loading and processing from POD5 files.

    Attributes:
        pod5_paths (List[pathlib.Path]): A list of file paths to the POD5 files.
        pod5_ids_to_path (Dict[str, List[str]]): A dictionary mapping POD5 file IDs to their respective paths.

    Methods:
        ids_to_path() -> Dict[str, List[str]]:
            Constructs a dictionary mapping file paths to lists of read IDs contained in each file.

        load_read_data(read_id: str) -> Dict[str, Any]:
            Loads and processes data for a specific read ID.

        members_to_dict(obj: Any) -> Dict[str, Any]:
            Converts the attributes of an object to a dictionary, processing different types accordingly.

        process_signal_rows(sig_rows: list[pod5.reader.SignalRowInfo]) -> Dict[str, Any]:
            Processes signal row information into a dictionary format.
    """

    pod5_paths: List[pathlib.Path]
    pod5_ids_to_path: Dict[str, List[str]]

    def __init__(self, pod5_paths: List[pathlib.Path]) -> None:
        """
        Initializes the DataHandler with a list of POD5 file paths.

        Args:
            pod5_paths (List[pathlib.Path]): List of pathlib.Path objects representing POD5 file paths.
        """
        self.pod5_paths = pod5_paths
        self.dataset_reader = pod5.DatasetReader(pod5_paths)
    
    def ids_to_path(self) -> Dict[str, List[str]]:
        """
        Creates a dictionary mapping each file path to a list of read IDs it contains.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are file paths (as strings) and values are lists of read IDs.
        """
        file_paths = self.dataset_reader.paths
        id_path_dict = dict(zip([str(file) for file in file_paths],
                                 [self.dataset_reader.get_reader(file).read_ids for file in file_paths]))
        return id_path_dict
    
    def load_read_data(self, read_id: str) -> Dict[str, Any]:
        """
        Loads data for a specified read ID and converts it to a dictionary.

        Args:
            read_id (str): The read ID for which data needs to be loaded.

        Returns:
            Dict[str, Any]: A dictionary containing the read data.
        """
        read_record = self.dataset_reader.get_read(read_id)
        return self.members_to_dict(read_record)

    def members_to_dict(self, obj) -> Dict[str, Any]:
        """
        Converts an object's attributes to a dictionary, handling various types of attributes.

        Args:
            obj (Any): The object whose attributes need to be converted.

        Returns:
            Dict[str, Any]: A dictionary representation of the object's attributes.
        """
        obj_dict = {}

        members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]
        
        for member in members: 
            member_value = getattr(obj, member)

            if member == "signal_rows":
                obj_dict[member] = self.process_signal_rows(member_value)
            elif type(member_value) in [float, int, str, bool, dict, datetime.datetime, uuid.UUID, np.ndarray]:
                obj_dict[member] = member_value
            else:
                obj_dict[member] = self.members_to_dict(member_value)

        return obj_dict

    def process_signal_rows(self, sig_rows: list[pod5.reader.SignalRowInfo]) -> Dict[str, Any]:
        """
        Processes a list of signal rows into a dictionary format.

        Args:
            sig_rows (list[pod5.reader.SignalRowInfo]): A list of SignalRowInfo objects to be processed.

        Returns:
            Dict[str, Any]: A dictionary where each key is a row index (as a string) and the value is a dictionary 
                            representation of the row's attributes.
        """
        row_dict = {}
        for i, row in enumerate(sig_rows, start=1):
            row_dict[str(i)] = self.members_to_dict(row)
        return row_dict


class Pod5Viewer(QMainWindow):
    """
    A Qt-based GUI application for viewing and navigating POD5 files.

    Attributes:
        file_navigator (QTreeWidget): Widget for displaying and selecting files and read IDs.
        data_viewer (QTreeView): Widget for displaying detailed data of the selected read.
        data_handler (DataHandler): Handles data operations for the loaded POD5 files.

    Methods:
        init_ui():
            Initializes the user interface.

        select_files():
            Opens a file dialog to select POD5 files.

        select_directory():
            Opens a directory dialog to select a directory containing POD5 files.

        load_files(file_paths: List[str]):
            Loads POD5 files and populates the file navigator.

        fill_file_navigator(id_path_dict: Dict[str, List[str]]):
            Populates the file navigator with file paths and read IDs.

        fill_data_viewer(read_id: QTreeWidgetItem):
            Populates the data viewer with detailed data for the selected read ID.

        populate_data_viewer(parent: QStandardItem, data: Dict[str, Any]):
            Recursively populates the data viewer with hierarchical data.
    """

    def __init__(self, file_paths: List[str]|None = None) -> None:
        """
        Initializes the Pod5Viewer application.

        Args:
            file_paths (List[str] | None): Optional list of file paths to be loaded at startup.
        """
        super().__init__()
        self.init_ui()

        if file_paths:
            self.load_files(file_paths)

    def init_ui(self) -> None:
        """
        Initializes the user interface elements of the Pod5Viewer.
        Sets up the window title, menu, layout, and widgets.
        """
        self.setWindowTitle("pod5Viewer")

        # set up the dropdown menu in the top
        menubar = self.menuBar()
        main_menu = menubar.addMenu("File")
        main_menu.addAction("Open file(s)...", self.select_files)
        main_menu.addAction("Open directory...", self.select_directory)
        main_menu.addSeparator()
        main_menu.addAction("Export current read...", self.export_current_read)
        main_menu.addSeparator()
        main_menu.addAction("Clear", self.clear_viewer)
        main_menu.addSeparator()        
        main_menu.addAction("Exit", self.close)

        view_menu = menubar.addMenu("View")
        view_menu.addAction("Plot signal...", self.plot_signal)
        view_menu.addAction("Plot pA signal...", self.plot_pa_signal)

        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About", self.show_about)

        self.about_dialog = QMessageBox()

        # create the layout
        layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # left column to choose file and id
        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)

        # right column to show data
        self.data_viewer = QTreeView()
        # keeps track of the currently loaded data
        self.data_viewer_data = None
        # keepts track of the currently opened plot window
        self.plot_window = None

        layout.addWidget(self.file_navigator, 1)
        layout.addWidget(self.data_viewer, 2)

    def show_about(self):
        """
        Displays a message box with information about the application.
        """
        about_text = f'<center><b>pod5view</b><br>v{__version__}</center><br><br>Author: Vincent Dietrich<br>Github: <a href="https://github.com/dietvin/pod5Viewer">https://github.com/dietvin/pod5Viewer</a></center>'
        self.about_dialog.setText(about_text)
        self.about_dialog.exec()

    def select_files(self) -> None:
        """
        Opens a file dialog to select one or more POD5 files.
        Loads the selected files into the application.
        """
        dialog = QFileDialog(self, "Select Files")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("POD5 files (*.pod5)")
        if dialog.exec():
            pod5_files = dialog.selectedFiles()
            self.load_files(pod5_files)

    def select_directory(self):
        """
        Opens a directory dialog to select a directory containing POD5 files.
        Loads the POD5 files from the selected directory into the application.
        """
        dialog = QFileDialog(self, "Select Directory")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if dialog.exec():
            pod5_dir = dialog.selectedFiles()[0]
            files_in_dir = [os.path.join(pod5_dir, file) for file in os.listdir(pod5_dir)]
            files_in_dir = [file for file in files_in_dir if os.path.isfile(file)]
            if len(files_in_dir) > 0:
                pod5_files = [file for file in files_in_dir if file.split(".")[1]=="pod5"]
                if len(pod5_files) > 0:
                    self.load_files(pod5_files)

    def load_files(self, file_paths: List[str]) -> None:
        """
        Loads the specified POD5 files and updates the file navigator with their read IDs.

        Args:
            file_paths (List[str]): A list of file paths to POD5 files to be loaded.
        """
        # clear the file navigator and data viewer
        self.file_navigator.clear()
        self.model = QStandardItemModel()
        self.data_viewer.setModel(self.model)

        paths_as_path = [pathlib.Path(i) for i in file_paths]
        self.data_handler = DataHandler(paths_as_path)

        file_navigator_data = self.data_handler.ids_to_path()
        self.fill_file_navigator(file_navigator_data)

    def fill_file_navigator(self, id_path_dict: Dict[str, List[str]]):
        """
        Populates the file navigator with file paths and their associated read IDs.

        Args:
            id_path_dict (Dict[str, List[str]]): A dictionary mapping file paths to lists of read IDs.
        """
        for path, items in id_path_dict.items():
            path_item = QTreeWidgetItem([path])
            path_item.setToolTip(0,path)
            self.file_navigator.addTopLevelItem(path_item)

            
            for id_item in items:
                id_tree_item = QTreeWidgetItem([id_item])
                path_item.addChild(id_tree_item)
        
        self.file_navigator.itemClicked.connect(self.fill_data_viewer)

    def fill_data_viewer(self, read_id) -> None:
        """
        Populates the data viewer with detailed data for the selected read ID.

        Args:
            read_id (QTreeWidgetItem): The selected read ID item from the file navigator.
        """
        if read_id.childCount() == 0:
            read_id_str = read_id.text(0)
            
            self.model = QStandardItemModel()
            self.model.setHorizontalHeaderLabels(['Key', 'Value'])
            self.data_viewer.setModel(self.model)

            self.data_viewer_data = self.data_handler.load_read_data(read_id_str)
            self.populate_data_viewer(self.model.invisibleRootItem(), self.data_viewer_data)
            self.data_viewer.setColumnWidth(0, 230)

    def populate_data_viewer(self, parent: QStandardItem, data: Dict[str, Any], parent_keys: List[str] = []):
        """
        Recursively populates the data viewer with hierarchical data.

        Args:
            parent (QStandardItem): The parent item in the data viewer.
            data (Dict[str, Any]): The data to be displayed, structured as a dictionary.
            parent_keys (List[str]): The list of parent keys leading to the current data.
        """
        for key, value in data.items():
            help_str = HELP.get(" ".join(parent_keys + [key]), None)
            if not help_str:
                help_str = "No docstring available"

            if isinstance(value, dict):
                item = QStandardItem(key)
                item.setEditable(False)
                item.setToolTip(help_str)
                parent.appendRow(item)
                # if statement to catch the individual signal_rows entries (need 'signal_rows <key>' without number)
                self.populate_data_viewer(item, value, parent_keys if key.isdigit() else parent_keys + [key])
            else:
                key_item = QStandardItem(key)
                key_item.setEditable(False)
                key_item.setToolTip(help_str)

                if type(value) == np.ndarray:
                    value_item = QStandardItem(", ".join([str(i) for i in value]))
                else:
                    value_item = QStandardItem(str(value))

                parent.appendRow([key_item, value_item])

    def export_current_read(self) -> None:
        """
        Exports the current read data to a YAML file.

        This method prompts the user to select a directory to save the exported data.
        It then constructs a file path using the selected directory and the current read ID.
        The signal data is transformed to comma-separated strings and written to the file in YAML format.

        Returns:
            None
        """
        if self.data_viewer_data:
            # Get the selected read ID
            read_id = self.data_viewer_data["read_id"]
            # Prompt the user to select a directory
            dialog = QFileDialog(self, "Export Current Read")
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)

            if dialog.exec():
                directory_path = dialog.selectedFiles()[0]
                # Construct the file path using the read ID
                file_path = os.path.join(directory_path, f"{read_id}.yaml")
                # Transform "signal" and "signal_pa" entries to comma separated strings
                transformed_data = self.transform_data(self.data_viewer_data)
                # Write the transformed data to the selected file in YAML format
                with open(file_path, 'w') as file:
                    yaml.dump(transformed_data, file)
        
    def transform_data(self, data) -> Dict[str, Any]:
        """
        Transforms the "signal" and "signal_pa" entries in the data to comma separated strings.

        Args:
            data (Dict[str, Any]): The data to be transformed.

        Returns:
            Dict[str, Any]: The transformed data.
        """
        transformed_data = {}
        for key, value in data.items():
            if key == "signal" or key == "signal_pa":
                transformed_data[key] = ",".join(str(x) for x in value)
            else:
                transformed_data[key] = value
        return transformed_data

    def plot_signal(self):
        """
        Plots the current signal in a new window.

        This method checks if there is data available in the `data_viewer_data` attribute.
        If data is available, it opens a new plot window with the signal corresponding to the current read ID.

        Parameters:
            None

        Returns:
            None
        """
        if self.data_viewer_data:  
            self.open_plot_window(str(self.data_viewer_data["read_id"]), self.data_viewer_data["signal"])

    def plot_pa_signal(self) -> None:
        """
        Plots the current PA signal in a new window.

        This method is responsible for plotting the current PA signal in a new window. 
        It checks if the data viewer data is available and then opens a plot window with the PA signal. 
        The plot window is identified by the read ID and the PA signal is passed as a parameter. 
        The `in_pa` parameter is set to True to indicate that the signal being plotted is the PA signal.

        Parameters:
            None

        Returns:
            None
        """
        if self.data_viewer_data:
            self.open_plot_window(str(self.data_viewer_data["read_id"]), self.data_viewer_data["signal_pa"], in_pa=True)

    def open_plot_window(self, id: str, data: np.ndarray, in_pa: bool = False):
        """
        Opens a new window to display a plot of the provided data.

        Args:
            id (str): The identifier for the plot window.
            data (np.ndarray): The data to be plotted.
            in_pa (bool, optional): Indicates whether the data is in pA (picoampere) units. 
                Defaults to False.

        Returns:
            None
        """

        if self.plot_window:
            self.plot_window.close()

        fig = go.Figure()
        fig.update_layout(
            template="seaborn",
            title=id,
            xaxis_title="Time point",
            yaxis_title="Signal" if not in_pa else "Signal [pA]",
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
        fig.add_trace(go.Scatter(y=data))

        # create a new window to display the plot
        self.plot_window = QMainWindow()
        self.plot_window.setWindowTitle(f"{'Signal [pA]' if in_pa else 'Signal'} - {id}")
        web_view = QWebEngineView(self.plot_window)
        web_view.setHtml(fig.to_html(include_plotlyjs='cdn'))
        self.plot_window.setCentralWidget(web_view)
        self.plot_window.show()

    def clear_viewer(self) -> None:
        """
        Clears the data viewer by setting the model to an empty QStandardItemModel.
        """
        self.model = QStandardItemModel()
        self.data_viewer.setModel(self.model)
        self.data_viewer_data = None
        self.plot_window = None
        self.file_navigator.clear()


def main():
    app = QApplication(sys.argv)

    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None

    window = Pod5Viewer(file_paths)
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()