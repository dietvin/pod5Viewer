from typing import Dict, Any, List
import pod5, pathlib, datetime, uuid, numpy as np, tempfile, os
from pod5.pod5_types import EndReasonEnum


class DataHandler:
    """
    Handles data loading and processing from POD5 files.

    Attributes:
        pod5_paths (List[pathlib.Path]): A list of file paths to the POD5 files.
        pod5_ids_to_path (Dict[str, List[str]]): A dictionary mapping POD5 file IDs to their respective paths.

    Methods:
        ids_to_path() -> Dict[str, List[str]]:
            Constructs a dictionary mapping file paths to lists of read IDs contained in each file.

        load_read_data(read_id: str) -> Dict[str, Any]:
            Loads and processes data for a specific read ID.

        members_to_dict(obj: Any) -> Dict[str, Any]:
            Converts the attributes of an object to a dictionary, processing different types accordingly.

        process_signal_rows(sig_rows: list[pod5.reader.SignalRowInfo]) -> Dict[str, Any]:
            Processes signal row information into a dictionary format.
    """
    pod5_paths: List[pathlib.Path]
    pod5_ids_to_path: Dict[str, List[str]]

    def __init__(self, pod5_paths: List[pathlib.Path]) -> None:
        """
        Initializes the DataHandler with a list of POD5 file paths.

        Args:
            pod5_paths (List[pathlib.Path]): List of pathlib.Path objects representing POD5 file paths.
        """
        self.pod5_paths = pod5_paths
        self.dataset_reader = pod5.DatasetReader(pod5_paths)


    def ids_to_path(self) -> Dict[str, List[str]]:
        """
        Creates a dictionary mapping each file path to a list of read IDs it contains.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are file paths (as strings) and values are lists of read IDs.
        """
        original_cwd = os.getcwd()
        temp_dir = tempfile.gettempdir()
        try:
            os.chdir(temp_dir)
            file_paths = self.dataset_reader.paths
            id_path_dict = dict(zip([str(file) for file in file_paths],
                                    [self.dataset_reader.get_reader(file).read_ids for file in file_paths]))
            return id_path_dict
        except Exception as e:
            raise e
        finally:    
            os.chdir(original_cwd)

    
    def load_read_data(self, read_id: str) -> Dict[str, Any]:
        """
        Loads data for a specified read ID and converts it to a dictionary.

        Args:
            read_id (str): The read ID for which data needs to be loaded.

        Returns:
            Dict[str, Any]: A dictionary containing the read data.
        """
        read_record = self.dataset_reader.get_read(read_id)
        return self.members_to_dict(read_record)

    def members_to_dict(self, obj) -> Dict[str, Any]:
        """
        Converts an object's attributes to a dictionary, handling various types of attributes.
        Dictionary can be nested, as the method can be called recursively. In case an attribute
        can not be loaded, fills the value with the error message for that attribute.

        Args:
            obj (Any): The object whose attributes need to be converted.

        Returns:
            Dict[str, Any]: A dictionary representation of the object's attributes.
        """
        obj_dict = {}

        members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]

        for member in members: 
            try:
                member_value = getattr(obj, member)
                if member == "signal_rows":
                    obj_dict[member] = self.process_signal_rows(member_value)
                elif type(member_value) in [float, int, str, bool, dict, datetime.datetime, uuid.UUID, np.ndarray]:
                    obj_dict[member] = member_value
                # implemented to fix recursion error on MacOS:
                elif type(member_value) == EndReasonEnum: 
                    return {"name": member_value.name, "value": member_value.value}
                else:
                    obj_dict[member] = self.members_to_dict(member_value)
            except Exception as e:
                obj_dict[member] = f"ERROR: {e}"

        return obj_dict

    def process_signal_rows(self, sig_rows: list[pod5.reader.SignalRowInfo]) -> Dict[str, Any]:
        """
        Processes a list of signal rows into a dictionary format.

        Args:
            sig_rows (list[pod5.reader.SignalRowInfo]): A list of SignalRowInfo objects to be processed.

        Returns:
            Dict[str, Any]: A dictionary where each key is a row index (as a string) and the value is a dictionary 
                            representation of the row's attributes.
        """
        row_dict = {}
        for i, row in enumerate(sig_rows, start=1):
            row_dict[str(i)] = self.members_to_dict(row)
        return row_dict

