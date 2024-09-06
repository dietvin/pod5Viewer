try:
    from pod5Viewer.pod5Viewer import Pod5Viewer
except ModuleNotFoundError:
    from pod5Viewer import Pod5Viewer
    
from PySide6.QtWidgets import QApplication, QMessageBox
import sys, traceback

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
    sys.excepthook = error_handler

    app = QApplication(sys.argv)
    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None

    window = Pod5Viewer(file_paths)
    window.show()
    sys.exit(app.exec())
    

if __name__=="__main__":
    main()