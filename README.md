![header](./images/github_header.png)

The pod5Viewer is a Python application that provides a graphical user interface for viewing and navigating through POD5 files. It allows users to open multiple POD5 files, explore their contents, and display detailed data for selected read IDs.

## Table of Contents

- [Installation and requirements](#installation-and-requirements)
  - [Windows](#windows)
  - [Linux](#linux)
  - [OS independent](#os-independent)
  - [Dependencies](#dependencies)
- [Usage](#usage)
  - [Viewing, plotting and exporting](#viewing,-plotting-and-exporting)
  - [Shortcuts](#shortcuts)
- [Limitations](#limitations)
- [License](#license)

## Installation and requirements

### Windows

For Windows systems the pod5Viewer can be installed conveniently via the installer. The installer can be downloaded here:

[pod5Viewer-1.0.2-Setup.exe](https://github.com/dietvin/pod5Viewer/releases/download/1.0.2/pod5Viewer-1.0.2-Setup.exe "Download pod5Viewer Windows installer")

After downloading the installer and following the steps provided, the pod5Viewer can be accessed and opened from the start menu or the desktop shortcut. It also sets the pod5Viewer as the standard application to open POD5 files, so it is possible to open a file by simply clicking on it.

#### Note:

When running the installer a the Windows defender might open the Window `Windows protected your PC`. To continue the installation, press `More Info` and `Run anyway`.

### Linux

DEB files are available for Ubuntu 22.04, 24.04 and Linux Mint 21.3 at the following links:

- [Ubuntu 22.04](https://github.com/dietvin/pod5Viewer/releases/download/1.0.2/pod5viewer_1.0.2_ubuntu22.04.deb "Download pod5Viewer for Ubuntu 22.04")
- [Ubuntu 24.04](https://github.com/dietvin/pod5Viewer/releases/download/1.0.2/pod5viewer_1.0.2_ubuntu24.04.deb "Download pod5Viewer for Ubuntu 24.04")
- [Linux Mint 21.3](https://github.com/dietvin/pod5Viewer/releases/download/1.0.2/pod5viewer_1.0.2_linuxmint21.3.deb "Download pod5Viewer for Linux Mint 21.3")

After downloading use apt to install it on the system:

```bash
sudo apt install ./pod5viewer_1.0.2_<SYSTEM>.deb
```

Like the Windows installation, the pod5Viewer can then be opened like any other installed application.

### OS-independent

The pod5Viewer can be installed via the Python packaging index using `pip`.

Note that when installing the pod5Viewer via pip, it can only be started from the command line. It is not possible to open POD5 files directly from a file browser.

Here we recommend installing the pod5Viewer into a fresh virtual environment via [Conda](https://docs.anaconda.com/miniconda/) or a similar environment manager:

```bash
conda create -n p5v python==3.12 
conda activate p5v
```

With the virtual environment active, the pod5Viewer can be installed via pip:

```bash
pip install pod5Viewer
```

To start the pod5Viewer from a python environment type:

```bash
pod5Viewer
```

Optionally specify one or more path(s) to POD5 file(s) to open these directly:

```bash
pod5Viewer file1.pod5 file2.pod5
```

---

Alternatively, the pod5Viewer can be installed from source:

```bash
git clone https://github.com/dietvin/pod5Viewer.git
cd pod5Viewer
pip install .
```

### Dependencies

The pod5Viewer is built in Python (v3.12.3) and relies on the following packages:

- pod5 (v0.3.10)
- pyside6 (v6.7.1)
- setuptools (v70.0.0)
- plotly (v5.22.0)
- pyyaml (v6.0.1)

The compliation for Windows was performed using the pyinstaller (v6.8.0) and the Windows installer was created using the Inno Setup Compiler (v6.3.1).

## Usage

![overview](./images/pod5Viewer_overview.png)

The pod5Viewer consists of two main panels. On the left side is the file navigator panel and on the right side is the data view panel. Files can be opened individiually by selecting the `Open file(s)...` option in the `File` menu. Alternatively all files in a directory can be opened simultaneously through the `Open directory...` option.

Upon opening one or more files, an entry for each file is added in the file navigator panel. Expanding an file reveals a list of all read entries contained in the given file. Selecting an entry displays its attributes as a new tab in the data view panel. A single click opens the entry in a preview mode, that is replaced by a new selection when changed. A double click opens an entry permanently until closed via the [X] symbol on the respective tab. This way multiple reads can be opened at the same time

Some attributes in read entries contain nested data. The attributes can be expanded by clicking on the parent attribute. For more information about individual attributes hover above a given one to show a short explanation. The values of given attributes can be selected for copying to the clipboard.

For clearing both file navigator and data view panel, select `Clear` in the `File` menu. The `Exit` option in the `File` menu closes the pod5Viewer.

### Viewing, plotting and exporting

Current signals of either all opened reads or only the currently focused read can be viewed and plotted via the `View` menu. For viewing the measurements select an option in the `View signal...` submenu. This shows individual current measurements (in pA if selected) of the currently focussed reads in bins of 100 values. The scroll bar is used to scroll through the bins.

Signals can be plotted via the `Plot signal...`, `Plot pA signal...` or `Plot normalized signal...` submenu. Depending on which option is selected, the (normalized) current signal (in pA) is shown for the currently focussed read (`Focussed read...`) or all currently opened reads (`All open reads...`). This opens a new Window containing an interactive Plotly figure, allowing for zooming and panning. The figure can also be exported to a PNG file. When plotting multiple signals, individual signals can be hidden by clicking the read-id in the legend.

If the normalized signal is chosen for plotting, the standard score is calculated for each current value by subtracting the mean current value of the given read and dividing by the standard deviation.

Due to limitations of the Plotly framework when displaying large amounts of data, the signals get downsampled if a read has more than 10000 measurements. For downsampling, the measurements get binned into 10000 subsets, from each of which the median is calculated to represent the subset in the downsampled array. Downsampled measurements are indicated by a dotted line in the figure.

Either all opened reads (`Export all opened reads...`) or only the currently focused one (`Export current read...`) can be exported to YAML format using the `Export` submenu in the `File` menu. When exporting, the user selects an output directory in the file browser, in which a YAML file is created for each exported read with the read-id as the file name.

### Shortcuts

Various keyboard shortcuts are available, allowing for all actions to be performed without a mouse. The following shortcuts are implemented:

- Ctrl+O: Open file(s)
- Ctrl+D: Open directory
- Ctrl+S: Export current read
- Ctrl+A: Export all opened reads
- Ctrl+Backspace: Clear viewer
- Ctrl+Q: Exit application

Navigation:

- Tab: Switch between file navigator and data viewer
- Ctrl+Tab: Cycle through tabs in the data viewer
- Ctrl+W: Close the current tab in the data viewer

Menu navigation:

- Alt & F: Open the file menu
- Alt & V: Open the view menu
- Alt & H: Open the help menu

View signal window:

- Pagedown: Scroll down (large steps)
- Pageup: Scroll up (large steps)
- Arrow down: Scroll down
- Arrow up: Scroll up

## Limitations

### Plotting large amounts of data

When plotting many reads at a time the figure can become too large for displaying it in the plot window and it may show a white screen only. This is due to limitations of the plotly framework. The limit for this is around 40000 measurements in one plot, if this number is exceeded a warning pops up when opening the plot window.
If a plot does not show, it is recommended to plot fewer reads at a time.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
