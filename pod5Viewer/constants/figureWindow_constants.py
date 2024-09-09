
OVERVIEW_BIN_COUNT = 1000

COLOR_CYCLE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

SUBSAMPLE_BIN_COUNT = 5000

WINDOW_TITLE = "pod5Viewer - Plot signal"
WINDOW_GEOMETRY = (100, 100, 800, 600)
LEGEND_CHECKBOX_SIZE = (20, 20)

EXPORT_FIG_SIZE = (10, 6)

LABEL_PA_SUFFIX = "[pA]"
ZOOM_LABEL_TEXT = "Options for zooming below:"
ERROR_INVALID_ZOOM_INPUT = "Invalid input - only full numbers are allowed."
MESSAGE_NO_SUBSETTING = "No subsetting performed - each point corresponds to one measurement."

HELP_TEXT = """
<center>
    <b>Usage of the figure window</b>
</center>
<p>
    The figure Window consists of three elements:
    <ol>
        <li>The figure itself (top left)</li>
        <li>A legend (top right)</li>
        <li>The zoom selection (bottom)</li>
    </ol>
    Uncheck elements in the legend to hide them in the figure. For zooming, either select 
    a range in the preview of the figure or for more precise selections use type the range
    in the input fields below and press the zoom button. The reset zoom button reverts it
    back to the initial view.
    <br><br>
    Use the data menu to switch between normalized and unnormalized data shown in the plot.
    <br><br>
    Use the Export menu to save the figure.
</p>
"""