from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QHBoxLayout, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox, QTabWidget
from PySide6.QtGui import QStandardItemModel, QStandardItem, QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt
import sys, os, pathlib, yaml, traceback, platform
from typing import Dict, List, Any, Tuple
import numpy as np

try:
    from pod5Viewer.help_strings import HELP
    from pod5Viewer.__version__ import __version__
    from pod5Viewer.dataHandler import DataHandler
    from pod5Viewer.viewWindows import ArrayTableViewer, PlotViewer
except ModuleNotFoundError:
    from help_strings import HELP
    from __version__ import __version__
    from dataHandler import DataHandler
    from viewWindows import ArrayTableViewer, PlotViewer

# needed to work on Linux Mint...
if platform.system() == 'Linux':
    with open('/etc/os-release') as f:
        release_info = f.read()
        if 'Linux Mint' in release_info:
            os.environ['QT_QUICK_BACKEND'] = 'software'


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
                If provided, the files will be loaded automatically.

        Returns:
            None
        """
        super().__init__()
        self.init_ui()
        self.init_shortcuts()
        self.opened_read_data = {}

        if file_paths:
            self.load_files(file_paths)


    def init_ui(self) -> None:
        """
        Initializes the user interface elements of the Pod5Viewer.
        Sets up the window title, menu, layout, and widgets.
        """
        self.setWindowTitle("pod5Viewer")
        self.setGeometry(100, 100, 1200, 800)
        self.icon = QIcon(self.__resource_path("icon.ico"))
        self.setWindowIcon(self.icon)

        # set up the dropdown menu in the top
        menubar = self.menuBar()

        # set up the dropdown menu in the top
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False) # activate menu bar on MacOS

        main_menu = menubar.addMenu("&File")
        main_menu.addAction("Open file(s)...", self.select_files)
        main_menu.addAction("Open directory...", self.select_directory)
        main_menu.addSeparator()

        export_menu = main_menu.addMenu("Export")
        export_menu.addAction("Export current read...", self.export_current_read)
        export_menu.addAction("Export all opened reads...", self.export_all_opened_reads)
        main_menu.addSeparator()

        main_menu.addAction("Clear", self.clear_viewer)
        main_menu.addSeparator()  

        main_menu.addAction("Exit", self.close)

        view_menu = menubar.addMenu("&View")

        view_signal_menu = view_menu.addMenu("View signal...")
        view_signal_menu.addAction("View full signal data...", lambda: self.show_full_signal(in_pa=False))
        view_signal_menu.addAction("View full signal pA data...", lambda: self.show_full_signal(in_pa=True))
        view_menu.addSeparator()

        plot_signal_menu = view_menu.addMenu("Plot signal...")
        plot_signal_menu.addAction("Focussed read...", lambda: self.plot_signal(single=True))
        plot_signal_menu.addAction("All open reads...", lambda: self.plot_signal(single=False))

        plot_pa_signal_menu = view_menu.addMenu("Plot pA signal...")
        plot_pa_signal_menu.addAction("Focussed read...", lambda: self.plot_signal(in_pa=True, single=True))
        plot_pa_signal_menu.addAction("All open reads...", lambda: self.plot_signal(in_pa=True, single=False))

        plot_norm_signal_menu = view_menu.addMenu("Plot normalized signal...")
        plot_norm_signal_menu.addAction("Focussed read...", lambda: self.plot_signal(single=True, norm=True))
        plot_norm_signal_menu.addAction("All open reads...", lambda: self.plot_signal(single=False, norm=True))


        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Shortcuts", self.show_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)

        self.info_dialog = QMessageBox()
        self.info_dialog.setWindowIcon(self.icon)

        # create the layout
        layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # left column to choose file and id
        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)
        self.file_navigator.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.file_navigator.itemDoubleClicked.connect(self.add_proper_tab)
        self.file_navigator.itemActivated.connect(self.add_proper_tab)

        # right side shows tabs containing the data for each opened read
        self.data_tab_viewer = QTabWidget()
        self.data_tab_viewer.setTabsClosable(True)
        self.data_tab_viewer.tabCloseRequested.connect(self.remove_tab)

        self.preview_tab = None

        # keeps track of the currently opened plot window
        self.data_view_window = None
        self.plot_window = None

        layout.addWidget(self.file_navigator, 1)
        layout.addWidget(self.data_tab_viewer, 2)


    def closeEvent(self, event) -> None:
        """
        Overrides the closeEvent method of the QMainWindow class.
        Closes other windows before closing the main window.

        Args:
            event (QCloseEvent): The close event triggered by the user.

        Returns:
            None
        """
        if self.data_view_window:
            self.data_view_window.close()
        if self.plot_window:
            self.plot_window.close()    
        # Call the base class implementation
        super().closeEvent(event)


    def __resource_path(self, relative_path) -> str:
        """
        Get the absolute path to a resource, works for dev and for PyInstaller
        """
        if hasattr(sys, "_MEIPASS"):
            # When running in a PyInstaller bundle, the _MEIPASS attribute is set.
            base_path = getattr(sys, "_MEIPASS")
        else:
            base_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        return os.path.join(base_path, relative_path)

    def init_shortcuts(self) -> None:
        """
        Initializes keyboard shortcuts for the Pod5Viewer application.

        Shortcut List:
        - Ctrl+O: Open file(s)
        - Ctrl+D: Open directory
        - Ctrl+S: Export current read
        - Ctrl+A: Export all opened reads
        - Ctrl+Backspace: Clear viewer
        - Ctrl+Q: Exit application
        - Tab: Switch between file navigator and data viewer
        - Ctrl+Tab: Cycle through tabs in the data viewer
        - Ctrl+W: Close the current tab in the data viewer
        """
        # Ctrl+O: Open file(s)
        open_files_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_files_shortcut.activated.connect(self.select_files)
        # Ctrl+D: Open directory
        open_directory_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        open_directory_shortcut.activated.connect(self.select_directory)
        # Ctrl+S: Export current read
        export_current_read_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        export_current_read_shortcut.activated.connect(self.export_current_read)
        # Ctrl+A: Export all opened reads
        export_all_opened_reads_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        export_all_opened_reads_shortcut.activated.connect(self.export_all_opened_reads)
        # Ctrl+Backspace: Clear viewer
        clear_viewer_shortcut = QShortcut(QKeySequence("Ctrl+Backspace"), self)
        clear_viewer_shortcut.activated.connect(self.clear_viewer)
        # Ctrl+Q: Exit application
        exit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        exit_shortcut.activated.connect(self.close)
        # Tab to switch between file navigator and data viewer
        tab_shortcut = QShortcut(QKeySequence("Tab"), self)
        tab_shortcut.activated.connect(self.__shortcut_switch_focus)
        # Ctrl+Tab to cycle through tabs in the data viewer
        tab_cycle_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        tab_cycle_shortcut.activated.connect(self.__shortcut_cycle_reads)
        # Ctrl+W to close the current tab in the data viewer
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.__shortcut_close_tab)


    def __shortcut_switch_focus(self) -> None:
        """
        Switches the focus between the file navigator and the data viewer.
        """
        if self.file_navigator.hasFocus():
            if self.data_tab_viewer.currentWidget() is not None:
                self.data_tab_viewer.currentWidget().setFocus()
        else:
            self.file_navigator.setFocus()


    def __shortcut_cycle_reads(self) -> None:
        if self.data_tab_viewer.count() > 0:
            self.data_tab_viewer.setCurrentIndex((self.data_tab_viewer.currentIndex() + 1) % self.data_tab_viewer.count())
    

    def __shortcut_close_tab(self) -> None:
        if self.data_tab_viewer.count() > 0:
            self.remove_tab(self.data_tab_viewer.currentIndex())


    def show_about(self):
        """
        Displays a message box with information about the application.
        """
        about_text = f"""
                        <b>pod5Viewer</b>
                        <br>v{__version__}
                        <br>
                        <br>Author: Vincent Dietrich
                        <br>Github: <a href="https://github.com/dietvin/pod5Viewer">https://github.com/dietvin/pod5Viewer</a>
                        """
        self.info_dialog.setText(about_text)
        self.info_dialog.setWindowTitle("About pod5Viewer")
        self.info_dialog.exec()

    def show_shortcuts(self):
        """
        Displays a message box with information about the available shortcuts.
        """
        shortcuts_text = f"""<center>
                                <b>Shortcuts</b>
                            </center>
                            <b>File</b>
                                <br>Ctrl+O: Open file(s)
                                <br>Ctrl+D: Open directory
                                <br>Ctrl+S: Export current read
                                <br>Ctrl+A: Export all opened reads
                                <br>Ctrl+Backspace: Clear viewer
                                <br>Ctrl+Q: Exit application
                                <br>
                            <br><b>Navigation</b>
                                <br>Tab: Switch between file navigator and data viewer
                                <br>Ctrl+Tab: Cycle through tabs in the data viewer
                                <br>Ctrl+W: Close the current tab in the data viewer
                                <br>
                            <br><b>Menu navigation</b>
                                <br>Alt & F: Open the file menu
                                <br>Alt & V: Open the view menu
                                <br>Alt & H: Open the help menu
                                <br>
                            <br><b>View signal window</b>
                                <br>Pagedown: Scroll down (large steps)
                                <br>Pageup: Scroll up (large steps)
                                <br>Arrow down: Scroll down
                                <br>Arrow up: Scroll up
                            """
        self.info_dialog.setText(shortcuts_text)
        self.info_dialog.setWindowTitle("Shortcuts")
        self.info_dialog.exec()

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
        self.data_tab_viewer.clear()
        self.data_viewer_data = []

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


    def on_tree_selection_changed(self) -> None:
        """
        Callback method triggered when the selection in the tree view changes.

        This method updates the preview tab with the selected item.

        Returns:
            None
        """
        selected_items = self.file_navigator.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.update_preview_tab(item)


    def update_preview_tab(self, item: QTreeWidgetItem):
        """
        Updates the preview tab with the data corresponding to the selected item.

        Args:
            item (QTreeWidgetItem): The selected item in the tree widget.

        Returns:
            None
        """
        if item.childCount() == 0:
            read_id = item.text(0)

            if self.preview_tab:
                self.data_tab_viewer.removeTab(self.data_tab_viewer.indexOf(self.preview_tab))
            
            self.preview_tab, preview_data = self.prepare_tab_data(read_id)
            self.opened_read_data[read_id] = preview_data

            self.data_tab_viewer.addTab(self.preview_tab, read_id)
            self.data_tab_viewer.setCurrentWidget(self.preview_tab)


    def add_proper_tab(self, item):
        """
        Adds a proper tab to the data tab viewer.

        Parameters:
        - item: The item to be added as a tab.

        Returns:
        None

        Description:
        - If the item has no child items, it is added as a proper tab to the data tab viewer.
        - If a tab with the same item_id already exists, it is selected instead of adding a new tab.
        - After adding a proper tab, the next selection should be a preview tab.
        - The opened read data is stored in the opened_read_data dictionary.
        """
        if item.childCount() == 0:
            read_id = item.text(0)

            if self.preview_tab:
                self.data_tab_viewer.removeTab(self.data_tab_viewer.indexOf(self.preview_tab))
                self.preview_tab = None

            for i in range(self.data_tab_viewer.count()):
                if self.data_tab_viewer.tabText(i) == read_id:
                    self.data_tab_viewer.setCurrentIndex(i)
                    return

            proper_tab, proper_tab_data = self.prepare_tab_data(read_id)
            self.opened_read_data[read_id] = proper_tab_data

            self.data_tab_viewer.addTab(proper_tab, read_id)
            self.data_tab_viewer.setCurrentWidget(proper_tab)


    def prepare_tab_data(self, read_id: str) -> Tuple[QTreeView, Dict[str, Any]]:
        """
        Prepares the data for a tab in the pod5Viewer application.

        Args:
            read_id (str): The ID of the read data.

        Returns:
            Tuple[QTreeView, Dict[str, Any]]: A tuple containing the QTreeView widget and the loaded data.

        Raises:
            None

        Example usage:
            data_viewer, data_viewer_data = prepare_tab_data('read123')
        """
        data_viewer = QTreeView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Key', 'Value'])

        data_viewer_data = self.data_handler.load_read_data(read_id)
        self.populate_tree_model(model.invisibleRootItem(), self.transform_data(data_viewer_data))

        data_viewer.setModel(model)
        data_viewer.setColumnWidth(0, 230)

        return data_viewer, data_viewer_data


    def populate_tree_model(self, parent: QStandardItem, data: Dict[str, Any], parent_keys: List[str] = []):
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
                self.populate_tree_model(item, value, parent_keys if key.isdigit() else parent_keys + [key])
            else:
                key_item = QStandardItem(key)
                key_item.setEditable(False)
                key_item.setToolTip(help_str)

                if type(value) == np.ndarray:
                    value_item = QStandardItem(", ".join([str(i) for i in value]))
                else:
                    value_item = QStandardItem(str(value))

                parent.appendRow([key_item, value_item])


    def remove_tab(self, index: int) -> None:
        """
        Removes a tab from the data tab viewer and deletes the corresponding data from the opened_read_data dictionary.

        Args:
            index (int): The index of the tab to be removed.

        Returns:
            None
        """
        del(self.opened_read_data[self.data_tab_viewer.tabText(index)])
        self.data_tab_viewer.removeTab(index)

        if self.preview_tab and self.data_tab_viewer.indexOf(self.preview_tab) == -1:
            self.preview_tab = None


    def export_current_read(self) -> None:
        """
        Export the current read to a selected directory.

        This method prompts the user to select a directory and exports the current read
        to that directory. The current read is determined by the currently selected tab
        in the data_tab_viewer.

        Returns:
            None
        """
        if self.data_tab_viewer.count() > 0:
            # Prompt the user to select a directory
            dialog = QFileDialog(self, "Export current read")
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)

            if dialog.exec():
                read_id = self.data_tab_viewer.tabText(self.data_tab_viewer.currentIndex())
                directory_path = dialog.selectedFiles()[0]

                self.export_read(directory_path, read_id)


    def export_all_opened_reads(self) -> None:
        """
        Export all opened reads to the specified directory.

        This method prompts the user to select a directory and exports the data of
        all opened reads to that directory. Each read is exported using the 
        `export_read` method.

        Returns:
            None
        """
        if self.data_tab_viewer.count() > 0:
            # Prompt the user to select a directory
            dialog = QFileDialog(self, "Export all opened reads")
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)

            if dialog.exec():
                directory_path = dialog.selectedFiles()[0]
                for i in range(self.data_tab_viewer.count()):
                    read_id = self.data_tab_viewer.tabText(i)
                    self.export_read(directory_path, read_id)
        

    def export_read(self, directory: str, read_id: str) -> None:
        """
        Export the data of a specific read to a YAML file.

        Args:
            directory (str): The directory where the YAML file will be saved.
            read_id (str): The ID of the read to export.

        Returns:
            None
        """
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        file_path = os.path.join(directory, f"{read_id}.yaml")
        transformed_data = self.transform_data(self.opened_read_data[read_id], shorten=False)
        if read_id in self.opened_read_data.keys():
            with open(file_path, 'w') as file:
                yaml.dump(transformed_data, file)

        QApplication.restoreOverrideCursor()


    def transform_data(self, data: Dict[str, Any], shorten: bool = True) -> Dict[str, Any]:
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
                num_values = 100
                if shorten and (len(value) > num_values):
                    transformed_data[key] = ",".join(str(x) for x in value[:num_values]) + "..."
                else:
                    transformed_data[key] = ",".join(str(x) for x in value)
            else:
                transformed_data[key] = value
        return transformed_data

    def show_full_signal(self, in_pa: bool = False) -> None:
        """
        Displays the full signal data for the selected read(s) in a new window.

        Args:
            in_pa (bool, optional): Indicates whether the data is in pA (picoampere) units. Defaults to False.

        Returns:
            None
        """
        if self.data_tab_viewer.count() > 0:
            read_id = self.data_tab_viewer.tabText(self.data_tab_viewer.currentIndex())

            if self.data_view_window:
                self.data_view_window.close()

            data = self.opened_read_data[read_id]["signal" if not in_pa else "signal_pa"]
            self.data_view_window = ArrayTableViewer(data, read_id=read_id, in_pa=in_pa)
            self.data_view_window.setWindowIcon(self.icon)
            self.data_view_window.show()

    def plot_signal(self, in_pa: bool = False, single: bool = True, norm: bool = False) -> None:
        """
        Plots the signal data for the selected read(s) and opens a new window to display the plot.

        Args:
            in_pa (bool, optional): Indicates whether the data is in pA (picoampere) units. Defaults to False.
            single (bool, optional): Indicates whether to plot the signal for a single read or all opened reads. Defaults to True.

        Returns:
            None
        """
        if self.data_tab_viewer.count() > 0:
            if single:
                read_ids = [self.data_tab_viewer.tabText(self.data_tab_viewer.currentIndex())]
            else:
                read_ids = [self.data_tab_viewer.tabText(i) for i in range(self.data_tab_viewer.count())]

            plot_data = {}
            for read_id in read_ids:
                plot_data[read_id] = self.opened_read_data[read_id]["signal" if not in_pa else "signal_pa"]

            if self.plot_window:
                self.plot_window.close()
                
            self.plot_window = PlotViewer(plot_data, in_pa=in_pa, norm=norm)
            self.plot_window.setWindowIcon(self.icon)
            self.plot_window.show()

    def clear_viewer(self) -> None:
        """
        Clears the data viewer by setting the model to an empty QStandardItemModel.
        """
        self.model = QStandardItemModel()
        self.data_tab_viewer.clear()
        self.opened_read_data = {}
        self.plot_window = None
        self.file_navigator.clear()


def error_handler(exc_type, exc_value, exc_traceback) -> None:
    """
    Handle and display an error message dialog.

    Parameters:
    - exc_type (type): The type of the exception.
    - exc_value (Exception): The exception instance.
    - exc_traceback (traceback): The traceback object.

    Returns:
    None

    This function displays an error message dialog with the details of the exception.
    It takes the exception type, exception instance, and traceback as input parameters.
    The error message dialog shows the error message and provides a detailed text with the traceback information.
    """
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog = QMessageBox()
    error_dialog.setWindowTitle("An error occurred.")
    error_dialog.setText("An unexpected error occurred. For support, open an Issue on the pod5Viewer Github page with the error message.")
    error_dialog.setDetailedText(error_message)
    error_dialog.exec()
 

def main():
    app = QApplication(sys.argv)

    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None

    sys.excepthook = error_handler

    window = Pod5Viewer(file_paths)
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
