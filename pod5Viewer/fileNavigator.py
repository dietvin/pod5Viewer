from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget, QTreeWidget, 
                               QTreeWidgetItem, QLineEdit, QPushButton, QStyle)
from PySide6.QtCore import Qt, Signal
from typing import List, Dict


class FileNavigator(QWidget):
    """
    A QWidget subclass that provides a graphical interface for navigating
    and interacting with a hierarchical file (top-level items) and read 
    (children of top-level items) structure.

    Reads can be search and filtered. Both reads and files can be sorted 

    Attributes:
        reads_of_interest (List[str] | None): Stores reads that are actively 
            filtered for (these come from the id_input_window). None if no 
            filter is active.
        search_string (str | None): Stores the active search string; 
            None if no search is performed
        search_input (QLineEdit): LineEdit for search input
        clear_search_button (QPushButton): Button to clear the search input
        asc_icon (QIcon): Icon indicating ascending sort order
        desc_icon (): Icon indicating descending sort order
        sort_files_button (QPushButton): Button for changing the sort order of the files
        sort_order_files_asc (bool): bool indicating if the sort order of the files 
            is currently ascending
        sort_reads_button (QPushButton): Button for changing the sort order of the reads
        sort_order_reads_asc (bool): bool indicating if the sort order of the reads 
            is currently ascending
        file_navigator (QTreeWidget): TreeWidget containing file paths (top-level items) and
            read IDs (children of corresponding top-level items)
    """

    reads_of_interest: List[str] | None
    search_string: str | None

    itemSelectionChanged = Signal()
    itemDoubleClicked = Signal(QTreeWidgetItem, int)
    itemActivated = Signal(QTreeWidgetItem, int)
    
    def __init__(self) -> None:
        """
        Initializes the FileNavigator widget.
        """
        super().__init__()
        self.reads_of_interest = None 
        self.search_string = None 
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initialize the UI elements. 
        """
        user_input_layout = self.init_user_input_widgets()

        # set up tree widget
        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)

        # layout containing the rest of the widgets and the tree widget to the main layout 
        main_layout = QVBoxLayout()
        main_layout.addLayout(user_input_layout)
        main_layout.addWidget(self.file_navigator)
        self.setLayout(main_layout)
        
        self.init_connections()
        
    def init_user_input_widgets(self) -> QHBoxLayout:
        """
        Initialize widgets in the top of the FileNavigator widget for search and
        sort input.

        Returns:
            QHBoxLayout: Layout containing all user input widgets
        """
        # set up search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search read IDs...")
        # set up clear button
        clear_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton"))
        self.clear_search_button = QPushButton()
        self.clear_search_button.setIcon(clear_icon)
        #set up sort elements
        self.asc_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarShadeButton"))
        self.desc_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarUnshadeButton"))
        self.sort_files_button = QPushButton(icon=self.asc_icon, text="Sort files")
        self.sort_files_button.setToolTip("Sort files only")
        self.sort_order_files_asc = True
        self.sort_reads_button = QPushButton(icon=self.asc_icon, text="Sort reads")
        self.sort_reads_button.setToolTip("Sort reads only")
        self.sort_order_reads_asc = True
        # add widgets to layout
        layout = QHBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.clear_search_button)
        layout.addWidget(self.sort_files_button)
        layout.addWidget(self.sort_reads_button)
        return layout

    def init_connections(self) -> None:
        """
        Connect signals to slots.
        """        
        # redirect the signals from the TreeWidget to the FileNavigator parent
        # so it can be accessed directly from the outside
        self.file_navigator.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.file_navigator.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.file_navigator.itemActivated.connect(self.itemActivated)
        # signals for search input
        self.search_input.textEdited.connect(self.update_search_str)
        self.clear_search_button.pressed.connect(self.clear_search)
        # signals for sort input
        self.sort_files_button.pressed.connect(self.sort_files)
        self.sort_reads_button.pressed.connect(self.sort_reads)


    def load_data(self, id_path_dict: Dict[str, List[str]]) -> None:
        """
        Populates the file navigator with data from a dictionary mapping paths to read IDs.
        
        Args:
            id_path_dict (Dict[str, List[str]]): A dictionary where each key is a path (string)
                                                 and each value is a list of read IDs (strings)
                                                 associated with that path.
        """
        self.file_navigator.clear()

        for path, items in id_path_dict.items():
            path_item = QTreeWidgetItem([path])
            path_item.setToolTip(0,path)
            
            for id_item in items:
                id_tree_item = QTreeWidgetItem([id_item])

                hide_item = self.hide_item(id_item)
                id_tree_item.setHidden(hide_item)

                path_item.addChild(id_tree_item)

            self.file_navigator.addTopLevelItem(path_item)            

    def contains_data(self) -> bool:
        """
        Checks if the FileNavigator object has data loaded 
        (i.e. if the load_data method has been called).

        Returns:
            bool: True if data has been loaded.
        """
        return self.file_navigator.topLevelItemCount() >= 1

    def clear(self) -> None:
        """
        Clears all items from the file navigator tree.
        Resets search and filter attributes.
        """
        self.file_navigator.clear()
        self.reads_of_interest = None
        self.search_string = None

    def clear_search(self) -> None:
        """
        Clears the search input and resets the visibility of all items in the file navigator.
        """
        self.search_string = None
        self.search_input.setText("")
        self.update_view()

    def update_search_str(self) -> None:
        """
        Updates the search_str attribute to the current input from the search widget.
        """
        search_str = self.search_input.text()
        if len(search_str) < 1:
            self.search_string = None
        else:
            self.search_string = search_str
        self.update_view()

    def update_reads_of_interest(self, new_reads_of_interest: List[str] | None) -> None:
        """
        Updates the reads_of_interest attribute. Intended to be accessed from outside the
        object.

        Args:
            new_reads_of_interest (List[str] | None): List containing the IDs that should be
                filtered for. None if no filtering should be performed.
        """
        self.reads_of_interest = new_reads_of_interest
        self.update_view()

    def update_view(self) -> None:
        """
        Central method for updating the elements in the tree widget. Iterates through all 
        elements and set fitting items to hidden based on the current search and filter 
        status.
        """
        for i in range(self.file_navigator.topLevelItemCount()):
                for child_idx in range(self.file_navigator.topLevelItem(i).childCount()):
                    child = self.file_navigator.topLevelItem(i).child(child_idx)
                    
                    hide_child = self.hide_item(child.text(0))
                    child.setHidden(hide_child)

    def hide_item(self, item_str: str) -> bool:
        """
        Determines whether a given item (read) should be shown or hidden based on the current
        search and sort status. First determines if a search and filtering is performed at the
        moment (attribute is None if that is not the case) and sets the return value accordingly.

        Args:
            item_str (str): Text of an item in the TreeView.

        Returns:
            bool: True if the item should be hidden. False otherwise.
        """
        # is a search active?
        search_active = not self.search_string is None
        # are reads of interest present?
        read_filter_active = not self.reads_of_interest is None

        if search_active and read_filter_active: 
            # both active -> read is hidden if only one or both do not fit
            not_fits_search = not item_str.startswith(self.search_string) # type: ignore if statement checks if not None
            not_in_reads_of_interest = not item_str in self.reads_of_interest # type: ignore read_filter_active ensures not None
            return not_fits_search or not_in_reads_of_interest
        
        elif search_active: 
             # only search active -> read is hidden if the search string does not fit
             return not item_str.startswith(self.search_string) # type: ignore if statement checks if not None
        
        elif read_filter_active:
            # only read filter active -> read is hidden if it is not one of the reads of interest
            return not item_str in self.reads_of_interest # type: ignore read_filter_active ensures not None
        
        else: 
            # neither is active -> all reads are shown
            return False

    def sort_files(self) -> None:
        """
        Sorts the top-level items (files) in the file navigator tree.
        The sorting order toggles between ascending and descending on each call.
        """
        self.sort_top_level_items(ascending=self.sort_order_files_asc)
        if self.sort_order_files_asc:
            self.sort_files_button.setIcon(self.desc_icon)
            self.sort_files_button.setToolTip("Order files in descending order")
            self.sort_order_files_asc = False
        else:
            self.sort_files_button.setIcon(self.asc_icon)
            self.sort_files_button.setToolTip("Order files in ascending order")
            self.sort_order_files_asc = True

    def sort_reads(self) -> None:
        """
        Sorts the child items (reads) under each top-level item in the file navigator tree.
        The sorting order toggles between ascending and descending on each call.
        """
        self.sort_child_items(ascending=self.sort_order_reads_asc)
        if self.sort_order_reads_asc:
            self.sort_reads_button.setIcon(self.desc_icon)
            self.sort_reads_button.setToolTip("Order reads in descending order")
            self.sort_order_reads_asc = False
            
        else:
            self.sort_reads_button.setIcon(self.asc_icon)
            self.sort_reads_button.setToolTip("Order reads in ascending order")
            self.sort_order_reads_asc = True
            
    def sort_top_level_items(self, ascending: bool = True) -> None:
        """
        Sorts the top-level items (i.e., file paths) in the file navigator tree.

        Args:
            ascending (bool): If True, sorts the items in ascending order; otherwise, sorts in descending order.
                              Defaults to True.
        
        This method preserves the expanded state of each top-level item before sorting and restores it after sorting.
        """
        # take all top level items (i.e. file paths) and add them to a list for sorting
        top_level_items = []
        for _ in range(self.file_navigator.topLevelItemCount()):
            # store the bool if it was expanded before sorting to retain that status
            is_expanded = self.file_navigator.topLevelItem(0).isExpanded()
            item = self.file_navigator.takeTopLevelItem(0)
            top_level_items.append((item, is_expanded))

        # sort top-level items
        top_level_items.sort(key=lambda x: x[0].text(0), reverse=not ascending)

        # re-insert the sorted top-level items back into the tree
        for item, was_expanded in top_level_items:
            self.file_navigator.addTopLevelItem(item)
            self.file_navigator.topLevelItem(self.file_navigator.topLevelItemCount()-1).setExpanded(was_expanded)

    def sort_child_items(self, ascending: bool = True) -> None:
        """
        Sorts the child items (i.e., read IDs) under each top-level item in the file navigator tree.

        Args:
            ascending (bool): If True, sorts the items in ascending order; otherwise, sorts in descending order.
                              Defaults to True.
        
        This method sorts the children of each top-level item independently, based on the specified order.
        """
        sort_order = Qt.SortOrder.AscendingOrder if ascending else Qt.SortOrder.DescendingOrder
        for i in range(self.file_navigator.topLevelItemCount()):
            parent_item = self.file_navigator.topLevelItem(i)
            parent_item.sortChildren(0, sort_order)

    def selectedItems(self) -> List[QTreeWidgetItem]:
        return self.file_navigator.selectedItems()