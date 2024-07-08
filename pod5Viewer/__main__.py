try:
    from pod5Viewer.pod5Viewer import Pod5Viewer
except ModuleNotFoundError:
    from pod5Viewer import Pod5Viewer
    
from PySide6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)

    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None

    window = Pod5Viewer(file_paths)
    window.show()
    sys.exit(app.exec())
    

if __name__=="__main__":
    main()