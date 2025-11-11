from typing import Callable, Any, Dict, Optional, List
from pathlib import Path

from reder.utils.reder_registry import FileReaderRegistry, csv_reader, json_reader, joblib_reader, parquet_reader, text_reader


def read_file(filepath: str, reader: Callable, **kwargs) -> Any:
    """
    Read file using a registered reader function

    Args:
        filepath: Path to file
        reader: Registered reader function
        **kwargs: Additional arguments for reader

    Returns:
        Content from reader

    Raises:
        ValueError: If reader not registered
        FileNotFoundError: If file doesn't exist

    Example:
        >>> data = read_file('data.csv', csv_reader)
        >>> model = read_file('model.joblib', joblib_reader, mmap_mode='r')
    """
    # Validate registration
    if not FileReaderRegistry.is_registered(reader):
        raise ValueError(
            f"Reader '{reader.__name__}' not registered. "
            f"Available: {FileReaderRegistry.list_readers()}"
        )

    # Check file exists
    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read
    return reader(filepath, **kwargs)


def read_file_auto(filepath: str, **kwargs) -> Any:
    """
    Auto-detect and use appropriate reader based on file extension

    Args:
        filepath: Path to file
        **kwargs: Additional arguments for reader

    Returns:
        Content from reader

    Example:
        >>> df = read_file_auto('data.csv')
        >>> model = read_file_auto('model.joblib')
        >>> text = read_file_auto('file.txt')
    """
    path = Path(filepath)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Get extension
    extension = path.suffix

    # Find reader
    reader = FileReaderRegistry.get_reader_by_extension(extension)
    if reader is None:
        available_exts = list(FileReaderRegistry.list_extensions().keys())
        raise ValueError(
            f"No reader registered for '{extension}'. "
            f"Registered extensions: {available_exts}"
        )

    print(f"Using {reader.__name__} for {extension}")
    return reader(filepath, **kwargs)
