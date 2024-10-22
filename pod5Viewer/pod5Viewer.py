from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeView, 
                               QHBoxLayout, QWidget, QTreeWidgetItem, 
                               QFileDialog, QMessageBox, QTabWidget)
from PySide6.QtGui import (QStandardItemModel, QStandardItem, QKeySequence, 
                           QShortcut, QIcon, QCloseEvent)
import sys, os, pathlib, json, platform, uuid
from datetime import datetime, date
from typing import Dict, List, Any, Tuple
import numpy as np

try:
    from pod5Viewer.constants.pod5Viewer_constants import (HELP_STRINGS, WINDOW_TITLE,
                                                           WINDOW_GEOMETRY, SHORTCUT_HELP_TEXT)
    from pod5Viewer.__version__ import __version__
    from pod5Viewer.dataHandler import DataHandler
    from pod5Viewer.viewWindow import ArrayTableViewer
    from pod5Viewer.fileNavigator import FileNavigator
    from pod5Viewer.figureWindow import FigureWindow
    from pod5Viewer.idInputWindow import IDInputWindow
except ModuleNotFoundError:
    from constants.pod5Viewer_constants import (HELP_STRINGS, WINDOW_TITLE,
                                                WINDOW_GEOMETRY, SHORTCUT_HELP_TEXT)
    from __version__ import __version__
    from dataHandler import DataHandler
    from viewWindow import ArrayTableViewer
    from fileNavigator import FileNavigator
    from figureWindow import FigureWindow
    from idInputWindow import IDInputWindow

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
        file_navigator (FileNavigator): Custom Widget that displays the hierarchy of loaded POD5 files and their
            read IDs. Allows the user to select specific reads for viewing and analysis.Crucial for navigating 
            through the loaded data files.
        data_tab_viewer (QTabWidget): This widget manages and displays tabs, where each tab represents an opened 
            read. It allows users to view multiple reads simultaneously and switch between them. Central to the 
            user interface for data visualization.
        data_handler (DataHandler): This object manages the loading and processing of POD5 files. It provides 
            methods to access read data and metadata. Essential for all data operations in the application.
        opened_read_data (Dict[str, np.ndarray]): This dictionary stores the data of all currently opened reads.
            The keys are read IDs, and the values are the corresponding read data. Important for quick access 
            to read data without reloading from files.
        preview_tab (QTreeView | None): This represents the current preview tab in the data_tab_viewer. It shows 
            a quick view of a selected read without fully opening it. Enhances user experience by providing quick
            data previews.
        plot_window (FigureWindow | None): This keeps track of the currently opened plot window. It's used for 
            displaying graphical representations of read data. Critical for data visualization functionality.
            None until the window is first called.
        reads_of_interest (List[str] | None): List of read IDs given for filtering loaded data. If loaded, only
            reads with fitting IDs get shown in the file navigator. None if no filtering is active. 
    """
    file_navigator: FileNavigator
    data_tab_viewer: QTabWidget
    data_handler: DataHandler
    opened_read_data: Dict[str, Any]
    preview_tab: QTreeView | None
    plot_window: FigureWindow | None
    reads_of_interest: List[str] | None

    def __init__(self, file_paths: List[str]|None = None) -> None:
        """
        Initializes the Pod5Viewer application. Initializes UI, attributes, shortcuts, 
        and loads files if provided.
        
        Args:
            file_paths (List[str] | None): Optional list of file paths to be loaded at startup.
        """
        super().__init__()
        self.init_ui()
        self.init_attrs()
        self.init_shortcuts()

        if file_paths:
            self.load_files(file_paths)

    def init_ui(self) -> None:
        """
        Initializes the user interface elements of the Pod5Viewer.
        Sets up the window title, menu bar, layout, and widgets.
        Creates file navigator, data tab viewer, and other UI components.
        """
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(*WINDOW_GEOMETRY)
        self.icon = QIcon(self.__resource_path("icon.ico"))
        self.setWindowIcon(self.icon)

        self.init_menu()
        self.init_id_input_window()
        self.init_info_dialog()
        self.init_file_navigator()
        self.init_data_tab_viewer()
        self.init_layout()

    def init_menu(self) -> None:
        """
        Initializes the menu and connects actions to corresponding methods.
        """
        # set up the dropdown menu in the top
        menubar = self.menuBar()

        # set up the dropdown menu in the top
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False) # activate menu bar on MacOS

        main_menu = menubar.addMenu("&File")
        main_menu.addAction("Open file(s)...", self.select_files)
        main_menu.addAction("Open directory...", self.select_directory)
        main_menu.addSeparator()

        main_menu.addAction("Filter reads...", self.open_id_input_window)
        main_menu.addSeparator()

        export_all_menu = main_menu.addMenu("Export all info")
        export_all_menu.addAction("Current read...", self.export_focussed_read)
        export_all_menu.addAction("All opened reads...", self.export_opened_reads)
        
        export_signal_menu = main_menu.addMenu("Export signal")
        export_signal_nonpa_menu = export_signal_menu.addMenu("Signal")
        export_signal_nonpa_menu.addAction("Current read (.npy/.txt)...", lambda: self.export_focussed_signal(in_pa=False))
        export_signal_nonpa_menu.addAction("All opened reads (.npy)...", lambda: self.export_opened_signals(in_pa=False, suffix=".npy"))
        export_signal_nonpa_menu.addAction("All opened reads (.txt)...", lambda: self.export_opened_signals(in_pa=False, suffix=".txt"))

        export_signal_pa_menu = export_signal_menu.addMenu("pA signal")
        export_signal_pa_menu.addAction("Current read (.npy/.txt)...", lambda: self.export_focussed_signal(in_pa=True))
        export_signal_pa_menu.addAction("All opened reads (.npy)...", lambda: self.export_opened_signals(in_pa=True, suffix=".npy"))
        export_signal_pa_menu.addAction("All opened reads (.txt)...", lambda: self.export_opened_signals(in_pa=True, suffix=".txt"))

        main_menu.addSeparator()

        main_menu.addAction("Clear", self.clear_viewer)
        main_menu.addSeparator()  

        main_menu.addAction("Exit", self.close)

        view_menu = menubar.addMenu("&View")

        view_signal_menu = view_menu.addMenu("View signal")
        view_signal_menu.addAction("View full signal data...", lambda: self.show_full_signal(in_pa=False))
        view_signal_menu.addAction("View full signal pA data...", lambda: self.show_full_signal(in_pa=True))
        view_menu.addSeparator()

        plot_signal_menu = view_menu.addMenu("Plot signal")
        plot_signal_menu.addAction("Focussed read...", lambda: self.plot_signal(single=True))
        plot_signal_menu.addAction("All open reads...", lambda: self.plot_signal(single=False))

        plot_pa_signal_menu = view_menu.addMenu("Plot pA signal")
        plot_pa_signal_menu.addAction("Focussed read...", lambda: self.plot_signal(in_pa=True, single=True))
        plot_pa_signal_menu.addAction("All open reads...", lambda: self.plot_signal(in_pa=True, single=False))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Shortcuts", self.show_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction("About", self.show_about)

    def init_id_input_window(self) -> None:
        """
        Initialize the window ID input for filtering.
        """
        self.id_input_window = IDInputWindow()
        self.id_input_window.setWindowIcon(self.icon)
        self.id_input_window.submitted.connect(self.update_reads_of_interest)

    def init_info_dialog(self) -> None:
        """
        Initializes the help dialog (for general help & shortcuts). 
        """
        self.info_dialog = QMessageBox()
        self.info_dialog.setWindowIcon(self.icon)

    def init_file_navigator(self) -> None:
        """
        Initializes the file navigator and connects functionalities.
        """
        self.file_navigator = FileNavigator()
        self.file_navigator.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.file_navigator.itemDoubleClicked.connect(self.add_proper_tab)
        self.file_navigator.itemActivated.connect(self.add_proper_tab)

    def init_data_tab_viewer(self) -> None:
        """
        Initializes the data tab view widget. 
        """
        self.data_tab_viewer = QTabWidget()
        self.data_tab_viewer.setTabsClosable(True)
        self.data_tab_viewer.tabCloseRequested.connect(self.remove_tab)

    def init_layout(self) -> None:
        """
        Initializes the main layout and fills it with the file navigator and data tab
        viewer widgets.
        """ 
        layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(layout)

        layout.addWidget(self.file_navigator, 1)
        layout.addWidget(self.data_tab_viewer, 2)

        self.setCentralWidget(container)

    def init_attrs(self) -> None:
        """
        Initializes attributes. Directly after initialization:
        - no filtering
        - no preview tab
        - no data view window opened
        - no plot window opened
        - no reads opened (empty Dict)
        """
        self.reads_of_interest = None
        self.preview_tab = None
        self.data_view_window = None
        self.plot_window = None
        self.opened_read_data = {}

    def __resource_path(self, relative_path: str) -> str:
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
        export_current_read_shortcut.activated.connect(self.export_focussed_read)
        # Ctrl+A: Export all opened reads
        export_all_opened_reads_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        export_all_opened_reads_shortcut.activated.connect(self.export_opened_reads)
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
        if self.file_navigator.file_navigator.hasFocus():
            if self.data_tab_viewer.currentWidget() is not None:
                self.data_tab_viewer.currentWidget().setFocus()
        else:
            self.file_navigator.file_navigator.setFocus()


    def __shortcut_cycle_reads(self) -> None:
        """
        Increases the current index. If the last index is reached, cycle back to index 0. 
        Used when cycling via shortcut.
        """
        if self.data_tab_viewer.count() > 0:
            self.data_tab_viewer.setCurrentIndex((self.data_tab_viewer.currentIndex() + 1) % self.data_tab_viewer.count())
    

    def __shortcut_close_tab(self) -> None:
        """
        Closes the current tab when executed via shortcut.
        """
        if self.data_tab_viewer.count() > 0:
            self.remove_tab(self.data_tab_viewer.currentIndex())

    def closeEvent(self, event: QCloseEvent) -> None:
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
        self.info_dialog.setText(SHORTCUT_HELP_TEXT)
        self.info_dialog.setWindowTitle("Shortcuts")
        self.info_dialog.exec()

    def select_files(self) -> None:
        """
        Opens a file dialog to select one or more POD5 files.
        Loads the selected files into the application.
        """
        dialog = QFileDialog(self, "Select Files")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
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
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

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
        Loads the specified POD5 files using the DataHandler.
        Updates the file navigator with read IDs from loaded files.

        Args:
            file_paths (List[str]): A list of file paths to POD5 files to be loaded.
        """
        paths_as_path = [pathlib.Path(i) for i in file_paths]
        self.data_handler = DataHandler(paths_as_path)
        file_navigator_data = self.data_handler.ids_to_path()

        self.file_navigator.load_data(file_navigator_data)

    def open_id_input_window(self) -> None:
        """
        Opens the IDInputWindow window for read filtering. If no data was loaded it shows 
        a warning message instead of opening it. This ensures that no filtering can be started
        before loading data.
        """
        if self.file_navigator.contains_data():
            self.id_input_window.show()
        else:
            QMessageBox.warning(self, 
                                "No data loaded", 
                                "Read ID filtering works only after loading data.")
    
    def update_reads_of_interest(self) -> None:
        """
        Update the reads_of_interest attribute based on the input given in the read ID filtering window. 
        Redirects the given selection to the file navigator to update the shown read ID.
        """
        self.reads_of_interest = self.id_input_window.get_ids()
        self.file_navigator.update_reads_of_interest(self.reads_of_interest)

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
        Updates the preview tab with data corresponding to the selected item.
        Creates or updates a tab in the data_tab_viewer for quick preview.
        
        Args:
            item (QTreeWidgetItem): The selected item in the tree widget.        
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
        Adds a full data tab to the data tab viewer for the selected item.
        If a tab for the item already exists, it's selected instead of creating a new one.

        Args:
            item: The item to be added as a tab.
        """
        # If the item has no child items, it is added as a proper tab to the data tab viewer.
        if item.childCount() == 0:
            read_id = item.text(0)

            if self.preview_tab:
                self.data_tab_viewer.removeTab(self.data_tab_viewer.indexOf(self.preview_tab))
                # After adding a proper tab, the next selection should be a preview tab.
                self.preview_tab = None

            for i in range(self.data_tab_viewer.count()):
                # If a tab with the same item_id already exists, it is selected instead of adding a new tab.
                if self.data_tab_viewer.tabText(i) == read_id:
                    self.data_tab_viewer.setCurrentIndex(i)
                    return

            # The opened read data is stored in the opened_read_data dictionary.
            proper_tab, proper_tab_data = self.prepare_tab_data(read_id)
            self.opened_read_data[read_id] = proper_tab_data

            self.data_tab_viewer.addTab(proper_tab, read_id)
            self.data_tab_viewer.setCurrentWidget(proper_tab)


    def prepare_tab_data(self, read_id: str) -> Tuple[QTreeView, Dict[str, Any]]:
        """
        Prepares the data for a tab in the pod5Viewer application.
        Creates a QTreeView with the read data and sets up tooltips using HELP_STRINGS.

        Args:
            read_id (str): The ID of the read data.

        Returns: 
            Tuple[QTreeView, Dict[str, Any]]: A tuple containing the QTreeView widget and the loaded data.
        """
        data_viewer = QTreeView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Key', 'Value'])

        data_viewer_data = self.data_handler.load_read_data(read_id)
        self.populate_tree_model(model.invisibleRootItem(), self.transform_data(data_viewer_data))

        data_viewer.setModel(model)
        data_viewer.setColumnWidth(0, 230)

        return data_viewer, data_viewer_data


    def populate_tree_model(self, parent: QStandardItem, data: Dict[str, Any], parent_keys: List[str] = []) -> None:
        """
        Recursively populates the data viewer with hierarchical data.

        Args:
            parent (QStandardItem): The parent item in the data viewer.
            data (Dict[str, Any]): The data to be displayed, structured as a dictionary.
            parent_keys (List[str]): The list of parent keys leading to the current data.
        """
        for key, value in data.items():
            help_str = HELP_STRINGS.get(" ".join(parent_keys + [key]), None)
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


    def export_focussed_read(self) -> None:
        """
        Export all information of the currently focussed read to a selected path in JSON format.
        """
        if self.data_tab_viewer.count() > 0:
            read_id = self.data_tab_viewer.tabText(self.data_tab_viewer.currentIndex())
            filepath = self.filepath_dialog(
                caption = "Export current read",
                dir = read_id+"_export.json",
                filter="JSON Files (*.json);;All Files (*)"
            )
            if filepath:                
                self.write_json(read_id, filepath)
        else:
            self.show_no_data_opened_message()


    def export_focussed_signal(self, in_pa: bool) -> None:
        """
        Export only the signal of the currently focussed read to a selected path in either binary npy or
        text format. The format can be selected in the File Browser. 

        Args:
            in_pa (bool): True if the pA signal gets exported.
        """
        if self.data_tab_viewer.count() > 0:
            export_str = "_export_pa" if in_pa else "_export" 
            read_id = self.data_tab_viewer.tabText(self.data_tab_viewer.currentIndex())
            filepath = self.filepath_dialog(
                caption = "Export current read",
                dir = read_id + export_str + ".npy",
                filter="Numpy Files (*.npy);;TXT Files (*.txt);;All Files (*)"
            )
            if filepath:
                self.write_numpy(read_id, filepath, in_pa)
        else:
            self.show_no_data_opened_message()


    def filepath_dialog(self, caption: str, dir: str, filter: str) -> str:
        """
        Opens a file dialog for selecting a target file for exporting data.

        Args:
            caption (str): Caption of the Dialog
            dir (str): Default directory/filename
            caption (str): Active filter for specific file types

        Returns:
            str: Path to the target file after confirming a selection
        """
        filepath, _ = QFileDialog.getSaveFileName(
            parent = self,
            caption = caption,
            dir = dir,
            filter=filter
        )
        return filepath


    def export_opened_reads(self) -> None:
        """
        Export all information of all opened reads to individual files in the specified 
        directory.
        """
        if self.data_tab_viewer.count() > 0:
            directory = self.dirpath_dialog()
            if directory:
                for i in range(self.data_tab_viewer.count()):
                    read_id = self.data_tab_viewer.tabText(i)
                    filepath = os.path.join(directory, read_id+"_export.json")
                    if self.resume_with_path(filepath):
                        success = self.write_json(read_id, filepath)
                        if not success: break
        else:
            self.show_no_data_opened_message()
        

    def export_opened_signals(self, in_pa: bool, suffix: str) -> None:
        """
        Export the (pA) signal of all opened reads to individual files in the specified 
        directory.

        Args:
            in_pa (bool): True if the pA signal gets exported
            suffix (str): Selected file format
        """
        if self.data_tab_viewer.count() > 0:
            directory = self.dirpath_dialog()
            if directory:
                export_str = "_export_pa" if in_pa else "_export" 
                for i in range(self.data_tab_viewer.count()):
                    read_id = self.data_tab_viewer.tabText(i)
                    filepath = os.path.join(directory, read_id + export_str + suffix)
                    if self.resume_with_path(filepath):
                        success = self.write_numpy(read_id, filepath, in_pa)
                        if not success: break
        else:
            self.show_no_data_opened_message()


    def dirpath_dialog(self) -> str:
        """
        Opens a file dialog for selecting a target directory for exporting data.

        Returns:
            str: Path to the target directory after confirming a selection
        """
        dirpath = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        return dirpath


    def resume_with_path(self, filepath: str) -> bool:
        """
        Check if a file exists at a given path. If so opens a warning message and lets
        the user select if they want to overwrite the file.

        Args:
            filepath (str): Path to a given file

        Returns:
            bool: True if the export process continues (file doesn't exist or gets overwritten) 
        """
        if os.path.isfile(filepath):
            msg = QMessageBox(self)
            msg.setWindowTitle("File Already Exists")
            msg.setText(f"{os.path.basename(filepath)} already exists.<br>Do you want to replace it?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setIcon(QMessageBox.Icon.Warning)
            choice = msg.exec()

            return choice == QMessageBox.StandardButton.Yes
        return True


    def write_json(self, read_id: str, filepath: str) -> bool:
        """
        Writes the information of a read to JSON format.

        Note: the bool return allows the program to break the for loop when exporting multiple files
        (if one fails, all will fail because it is the same directory).

        Args:
            read_id (str): ID of the read to retrieve information
            filepath (str): Path to the output JSON file

        Returns:
            bool: True, if the write operation was successfull
        """
        if read_id in self.opened_read_data.keys():
            read_dict = self.transform_data(self.opened_read_data[read_id], shorten=False)
            try: 
                with open(filepath, 'w') as file:
                    json.dump(read_dict, file, indent=4)
            except PermissionError:
                QMessageBox.critical(self, "Permission error", 
                                        f"Export failed. You do not have permissions to write to path {filepath}")
                return False
        return True


    def write_numpy(self, read_id: str, filepath: str, in_pa: bool) -> bool:
        """
        Writes the signal of a given read to a numpy npy or txt file.

        Note: the bool return allows the program to break the for loop when exporting multiple files
        (if one fails, all will fail because it is the same directory).

        Args:
            read_id (str): ID of the read to retrieve information
            filepath (str): Path to the output .npy/.txt file
        """
        to_npy = filepath.endswith(".npy")

        if read_id in self.opened_read_data.keys():
            signal = self.opened_read_data[read_id]["signal_pa" if in_pa else "signal"]
            try:
                if to_npy:
                    np.save(filepath, signal, allow_pickle=False)
                else:
                    np.savetxt(filepath, signal)
            except PermissionError:
                QMessageBox.critical(self, "Permission error", 
                                        f"Export failed. You do not have permissions to write to path {filepath}")
                return False
        return True


    def transform_data(self, data: Dict[str, Any], shorten: bool = True) -> Dict[str, Any]:
        """
        Prepares the data to be shown in the data view panel or for exporting. Transforms
        data types to types that can be handled by JSON format.

        Args:
            data (Dict[str, Any]): The data to be transformed
            shorten (bool): True when setting up data for exporting 

        Returns:
            Dict[str, Any]: The transformed data.
        """
        transformed_data = {}
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                num_values = 100
                if shorten and (len(value) > num_values):
                    transformed_data[key] = ",".join(str(x) for x in value[:num_values]) + "..."
                else:
                    transformed_data[key] = value.tolist()
            elif isinstance(value, uuid.UUID):
                transformed_data[key] = str(value)
            elif isinstance(value, (date, datetime)):
                transformed_data[key] = value.isoformat()
            elif isinstance(value, Dict):
                transformed_data[key] = self.transform_data(value, False)
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
        else:
            self.show_no_data_opened_message()

    def plot_signal(self, in_pa: bool = False, single: bool = True) -> None:
        """
        Plots the signal data for the selected read(s) in a new window.
        Can plot either a single read or all opened reads.

        Args:
            in_pa (bool): If True, plots the signal in picoamperes. Default is False.
            single (bool): If True, plots only the current read. If False, plots all opened reads. Default is True.        
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
                
            self.plot_window = FigureWindow(plot_data, in_pa=in_pa)
            self.plot_window.setWindowIcon(self.icon)
            self.plot_window.show()
        else:
            self.show_no_data_opened_message()

    def clear_viewer(self) -> None:
        """
        Clears the data viewer by setting the model to an empty QStandardItemModel.
        """
        self.model = QStandardItemModel()
        self.data_tab_viewer.clear()
        self.opened_read_data = {}
        self.plot_window = None
        self.file_navigator.clear()

    def show_no_data_opened_message(self) -> None:
        """
        Shows a message if the user wants to analyze a read, but no read is opened.
        """      
        QMessageBox.warning(self, "No read opened", 
            "A read must be opened to perform this action. Load and access at least one read.")


def main() -> None:
    app = QApplication(sys.argv)

    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None

    window = Pod5Viewer(file_paths)
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
