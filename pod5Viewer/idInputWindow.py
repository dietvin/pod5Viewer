from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QPushButton, QFileDialog, 
                               QMessageBox, QLabel, QWidget)
from PySide6.QtCore import Signal
from typing import List

try:
    from pod5Viewer.constants.idInputWindow_constants import (WINDOW_TITLE, WINDOW_GEOMETRY, 
                                                              INSTRUCTION_TEXT, LOAD_MSG_BOX_TEXT)
except ModuleNotFoundError:
    from constants.idInputWindow_constants import (WINDOW_TITLE, WINDOW_GEOMETRY, 
                                                   INSTRUCTION_TEXT, LOAD_MSG_BOX_TEXT)


class IDInputWindow(QMainWindow):
    """
    A window that allows users to input IDs manually or load them from a file.
    
    The window provides:
    - A QTextEdit widget for manual ID input, one ID per line.
    - A button to load IDs from a text file.
    - A submit button to process and validate the IDs.
    - A clear button to remove the content of the text input.

    Attributes:
        id_input (QTextEdit): Text browser that allows the user to provide IDs
    """
    current_ids: List[str] | None

    submitted = Signal()

    def __init__(self) -> None:
        """
        Initializes the main window.
        """
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        """
        Sets up the widgets and layout, and connects the buttons to their respective functions.
        """
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(*WINDOW_GEOMETRY)
        
        # Set up the central widget and main layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add a label to provide instructions to the user
        instructions_label = QLabel(INSTRUCTION_TEXT)
        layout.addWidget(instructions_label)
        
        # TextEdit widget for ID input
        self.id_input = QTextEdit()
        layout.addWidget(self.id_input)
        
        # Layout for the buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # Button to load IDs from a file
        load_button = QPushButton("Load IDs from File")
        load_button.clicked.connect(self.load_ids_from_file)
        button_layout.addWidget(load_button)

        # Button to clear the text input
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_ids)
        button_layout.addWidget(clear_button)
        
        # Button to submit the IDs
        submit_button = QPushButton("Done")
        submit_button.clicked.connect(self.submitted)
        button_layout.addWidget(submit_button)
    
        self.setCentralWidget(central_widget)

    def load_ids_from_file(self) -> None:
        """
        Opens a file dialog to select a file containing IDs.
        Reads the file and populates the QTextEdit widget.
        Includes error handling for permission errors.
        """
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select ID File")
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()
                
                if self.id_input.toPlainText().strip():
                    # If the input box is not empty, ask if the user wants to overwrite the content
                    result = QMessageBox.question(
                        self, 
                        "Overwrite Existing IDs?",
                        LOAD_MSG_BOX_TEXT,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if result == QMessageBox.StandardButton.Yes:
                        self.id_input.setText(file_content)
                else:
                    self.id_input.setText(file_content)
            
            except PermissionError:
                QMessageBox.critical(self, "Permission error", f"Read permission denied for file: {file_path}")
    
    def clear_ids(self) -> None:
        """
        Clears the content of the QTextEdit widget.
        """
        self.id_input.clear()
    
    def get_ids(self) -> List[str] | None:
        """
        Collects the IDs from the QTextEdit widget and closes the window.

        Returns:
            List[str] | None: List containing each line from the text browser as a separate element.
                None if the text browser is empty.
        """
        ids = self.id_input.toPlainText().strip().splitlines()
        ids = [id_.strip() for id_ in ids]

        self.close()

        if len(ids) < 1:
            return None
        else:
            return ids