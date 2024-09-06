WINDOW_TITLE = "pod5Viewer"
WINDOW_GEOMETRY = (100, 100, 1200, 800) 
SHORTCUT_HELP_TEXT = """<center>
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

HELP_STRINGS = {
    "byte_count": "Number of bytes used to store the reads data",
    "calibration": "Calibration data associated with the read",
    "calibration offset": "Calibration offset used to convert raw ADC data into pA readings",
    "calibration scale": "Calibration scale factor used to convert raw ADC data into pA readings",
    "calibration_digitisation": "Digitisation value used by the sequencer. Intended to assist workflows ported from legacy file formats",
    "calibration_range": "Calibration range value. Intended to assist workflows ported from legacy file formats",
    "end_reason": "End reason data associated with the read",
    "end_reason forced": "True if it is a 'forced' read break (e.g. mux_change, unblock), false otherwise",
    "end_reason name": "Reason name as a lower string",
    "end_reason reason": "End reason enumeration",
    "end_reason reason name": "End reason enumeration name", 
    "end_reason reason value": "End reason enumeration value",
    "end_reason_index": "Dictionary index of the end reason data associated with the read. This property is the same as the EndReason enumeration value",
    "has_cached_signal": "Cached signal is available for this read",
    "median_before": "Get the median before level (in pico amps) for the read",
    "num_minknow_events": "Find the number of minknow events in the read",
    "num_reads_since_mux_change": "Number of selected reads since the last mux change on this reads channel",
    "num_samples": "Get the number of samples in the reads signal data",
    "pore": "Pore data associated with the read",
    "pore channel": "1-indexed channel", 
    "pore pore_type": "Name of the pore type present in the well", 
    "pore well": "1-indexed well",
    "predicted_scaling": "Predicted scaling value in the read",
    "predicted_scaling scale": "Scale of the predicted scaling",
    "predicted_scaling shift": "Shift of the predicted scaling",
    "read_id": "Unique read identifier for the read as a UUID",
    "read_number": "Get the integer read number of the read",
    "run_info": "Run info data associated with the read",
    "acquisition_id": "A unique identifier for the acquisition",
    "acquisition_start_time": "Clock time for sample 0",
    "adc_max": "The maximum ADC value that might be encountered",
    "adc_min": "The minimum ADC value that might be encountered",
    "context_tags": "The context tags for the run. (For compatibility with fast5)",
    "context_tags barcoding_enabled": "Barcoding is enabled",
    "context_tags basecall_config_filename": "Name of the config file used for basecalling",
    "context_tags experiment_type": "Type of experiment",
    "context_tags local_basecalling": None,
    "context_tags package": None,
    "context_tags package_version": None,
    "context_tags sample_frequency": "Sample frequency",
    "context_tags selected_speed_bases_per_second": "Selected speed in bases per second",
    "context_tags sequencing_kit": "Sequencing kit",
    "experiment_name": "User-supplied name for the experiment being run",
    "flow_cell_id": "Uniquely identifies the flow cell the data was captured on",
    "flow_cell_product_code": "Type of flow cell the data was captured on",
    "protocol_name": "Name of the protocol that was run",
    "protocol_run_id": "Unique identifier for the protocol run that produced this data",
    "protocol_start_time": "When the protocol that the acquisition was part of started",
    "sample_id": "User-supplied name for the sample being analysed",
    "sample_rate": "Number of samples acquired each second on each channel",
    "sequencer_position": "Sequencer position the data was collected on",
    "sequencer_position_type": "Type of sequencing hardware the data was collected on",
    "sequencing_kit": "Type of sequencing kit used to prepare the sample",
    "software": "Software that acquired the data",
    "system_name": "Name of the system the data was collected on",
    "system_type": "Type of system the data was collected on",
    "tracking_id": "Tracking id for the run. (For compatibility with fast5",
    "tracking_id asic_id": None,
    "tracking_id asic_id_eeprom": None,
    "tracking_id asic_temp": None,
    "tracking_id asic_version": None,
    "tracking_id configuration_version": None,
    "tracking_id data_source": None,
    "tracking_id device_id": None,
    "tracking_id device_type": None,
    "tracking_id distribution_status": None,
    "tracking_id distribution_version": None,
    "tracking_id exp_script_name": None,
    "tracking_id exp_script_purpose": None,
    "tracking_id exp_start_time": None,
    "tracking_id flow_cell_id": None,
    "tracking_id flow_cell_product_code": None,
    "tracking_id fpga_board_id": None,
    "tracking_id fpga_firmware_version": None,
    "tracking_id guppy_version": None,
    "tracking_id heatsink_temp": None,
    "tracking_id host_product_code": None,
    "tracking_id host_product_serial_number": None,
    "tracking_id hostname": None,
    "tracking_id installation_type": None,
    "tracking_id is_simulated": None,
    "tracking_id operating_system": None,
    "tracking_id protocol_group_id": None,
    "tracking_id protocol_run_id": None,
    "tracking_id protocol_start_time": None,
    "tracking_id protocols_version": None,
    "tracking_id run_id": None,
    "tracking_id sample_id": None,
    "tracking_id sequencer_hardware_revision": None,
    "tracking_id sequencer_product_code": None,
    "tracking_id sequencer_serial_number": None,
    "tracking_id usb_config": None,
    "tracking_id version": None,
    "run_info_index": "Dictionary index of the run info data associated with the read",
    "sample_count": "Number of samples in the reads signal data",
    "signal": "Full signal for the read",
    "signal_pa": "Full signal for the read, calibrated in pico amp",
    "signal_rows": "All signal rows for the read",
    "signal_rows batch_index": "Alias for field number 0",
    "signal_rows batch_row_index": "Alias for field number 1",
    "signal_rows byte_count": "Alias for field number 3",
    "signal_rows sample_count": "Alias for field number 2",
    "start_sample": "Absolute sample which the read started",
    "time_since_mux_change": "Time in seconds since the last mux change on this reads channel",
    "tracked_scaling": "Tracked scaling value in the read",
    "tracked_scaling scale": "Scale of the predicted scaling", 
    "tracked_scaling shift": "Shift of the predicted scaling"
}
