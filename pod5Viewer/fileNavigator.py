from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QLineEdit, QPushButton, QStyle
from PySide6.QtCore import Qt, Signal
from typing import List, Dict


class FileNavigator(QWidget):
    """
    A QWidget subclass that provides a graphical interface for navigating
    and interacting with a hierarchical file and read structure.

    This widget allows users to search, clear, sort files and reads within
    a tree-like structure using a QTreeWidget. It provides sorting functionality
    both for files (top-level items) and reads (children of top-level items).
    """
    itemSelectionChanged = Signal()
    itemDoubleClicked = Signal(QTreeWidgetItem, int)
    itemActivated = Signal(QTreeWidgetItem, int)
    
    def __init__(self) -> None:
        """
        Initializes the FileNavigator widget, setting up the layout, search bar,
        clear button, sorting buttons, and the file navigation tree. Also connects
        signals to their respective slots for handling user interactions.
        """
        super().__init__()
        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search read IDs...")
        clear_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarCloseButton"))
        self.clear_search_button = QPushButton(icon=clear_icon)

        self.asc_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarShadeButton"))
        self.desc_icon = self.style().standardIcon(getattr(QStyle, "SP_TitleBarUnshadeButton"))

        self.sort_files_button = QPushButton(icon=self.asc_icon, text="Sort files")
        self.sort_files_button.setToolTip("Sort files only")
        self.sort_order_files_asc = True
        
        self.sort_reads_button = QPushButton(icon=self.asc_icon, text="Sort reads")
        self.sort_reads_button.setToolTip("Sort reads only")
        self.sort_order_reads_asc = True

        self.file_navigator = QTreeWidget()
        self.file_navigator.setHeaderHidden(True)

        hlayout.addWidget(self.search_input)
        hlayout.addWidget(self.clear_search_button)
        hlayout.addWidget(self.sort_files_button)
        hlayout.addWidget(self.sort_reads_button)

        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.file_navigator)

        self.setLayout(vlayout)
        
        self.file_navigator.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.file_navigator.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.file_navigator.itemActivated.connect(self.itemActivated)

        self.search_input.textEdited.connect(self.search_items)
        self.clear_search_button.pressed.connect(self.clear_search)

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
                path_item.addChild(id_tree_item)

            self.file_navigator.addTopLevelItem(path_item)            

    def clear(self) -> None:
        """
        Clears all items from the file navigator tree.
        """
        self.file_navigator.clear()

    def search_items(self, search_str: str) -> None:
        """
        Searches for items in the file navigator that match the given search string.
        Items that do not match the search string are hidden.

        Args:
            search_str (str): The string to search for within the read IDs.
        """
        if len(search_str)<1: self.clear_search()
        else:
            n_top_level_items = self.file_navigator.topLevelItemCount()
            for i in range(n_top_level_items):
                child_count = self.file_navigator.topLevelItem(i).childCount()
                for child_idx in range(child_count):
                    self.file_navigator.topLevelItem(i).child(child_idx).setHidden(
                        not self.file_navigator.topLevelItem(i).child(child_idx).text(0).startswith(search_str)
                    )

    def clear_search(self) -> None:
        """
        Clears the search input and resets the visibility of all items in the file navigator.
        """
        self.search_input.setText("")
        for i in range(self.file_navigator.topLevelItemCount()):
                for child_idx in range(self.file_navigator.topLevelItem(i).childCount()):
                    self.file_navigator.topLevelItem(i).child(child_idx).setHidden(False)

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