# Pod5Viewer
Pod5Viewer is a Python application that provides a graphical interface for viewing and navigating through POD5 files. It allows users to open multiple POD5 files, explore their contents, and display detailed data for selected read IDs.

## Features
- Load and navigate multiple POD5 files.
- View detailed data for specific read IDs.
- User-friendly interface with file selection and directory browsing capabilities.

## Requirements
- Python 3.6+
- PySide6
- pod5 library
- numpy

## Installation
To install the required packages, you can use `pip`. If you haven't installed these libraries yet, run:

```bash
git clone https://github.com/dietvin/pod5Viewer.git
cd pod5Viewer
pip install .
```

## Usage
To run the application, navigate to the directory containing the script and execute it with Python:
```bash
pod5Viewer
```
You can optionally specify POD5 files as command-line arguments:
```bash
pod5Viewer file1.pod5 file2.pod5
```
## User Interface

- File Menu:
    - Open file(s)...: Opens a dialog to select and load one or more POD5 files.
    - Open directory...: Opens a dialog to select a directory containing POD5 files.
    - Exit: Closes the application.
- File Navigator: Located on the left, this section allows you to browse the loaded POD5 files and their read IDs.
- Data Viewer: Located on the right, this section displays detailed data for the selected read ID.

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.