from typing import Callable, Any, Dict, Optional, List


class FileReaderRegistry:
    """Registry for file reader functions"""

    _readers: Dict[str, Callable] = {}
    _extensions: Dict[str, str] = {}  # extension -> reader_name

    @classmethod
    def register(cls, name: Optional[str] = None, extensions: Optional[List[str]] = None):
        """
        Decorator to register a reader function

        Args:
            name: Optional custom name (defaults to function name)
            extensions: File extensions this reader handles (e.g., ['.csv', '.tsv'])

        Example:
            @FileReaderRegistry.register(extensions=['.csv', '.tsv'])
            def csv_reader(filepath, **kwargs):
                return pd.read_csv(filepath, **kwargs)
        """

        def decorator(func: Callable) -> Callable:
            reader_name = name or func.__name__

            # Register function
            cls._readers[reader_name] = func

            # Register extensions
            if extensions:
                for ext in extensions:
                    ext_lower = ext.lower()
                    cls._extensions[ext_lower] = reader_name

            # Store metadata on function
            func._registered_name = reader_name
            func._extensions = extensions or []

            print(f"✓ Registered: {reader_name}" +
                  (f" (extensions: {extensions})" if extensions else ""))

            return func

        return decorator

    @classmethod
    def is_registered(cls, func: Callable) -> bool:
        """Check if function is registered"""
        return func in cls._readers.values()

    @classmethod
    def get_reader(cls, name: str) -> Callable:
        """Get reader by name"""
        if name not in cls._readers:
            raise ValueError(
                f"Reader '{name}' not found. Available: {list(cls._readers.keys())}"
            )
        return cls._readers[name]

    @classmethod
    def get_reader_by_extension(cls, extension: str) -> Optional[Callable]:
        """Get reader for a file extension"""
        ext_lower = extension.lower()
        if ext_lower in cls._extensions:
            reader_name = cls._extensions[ext_lower]
            return cls._readers[reader_name]
        return None

    @classmethod
    def list_readers(cls) -> List[str]:
        """List all registered reader names"""
        return list(cls._readers.keys())

    @classmethod
    def list_extensions(cls) -> Dict[str, str]:
        """List all registered extensions and their readers"""
        return dict(cls._extensions)


# ============================================================================
# PRE-REGISTERED READERS
# ============================================================================

@FileReaderRegistry.register(extensions=['.csv', '.tsv'])
def csv_reader(filepath: str, **kwargs) -> Any:
    """Read CSV/TSV files using pandas"""
    import pandas as pd
    return pd.read_csv(filepath, **kwargs)


@FileReaderRegistry.register(extensions=['.parquet', '.pq'])
def parquet_reader(filepath: str, **kwargs) -> Any:
    """Read Parquet files using pandas"""
    import pandas as pd
    return pd.read_parquet(filepath, **kwargs)


@FileReaderRegistry.register(extensions=['.xlsx', '.xls'])
def excel_reader(filepath: str, **kwargs) -> Any:
    """Read Excel files using pandas"""
    import pandas as pd
    return pd.read_excel(filepath, **kwargs)


@FileReaderRegistry.register(extensions=['.joblib', '.pkl'])
def joblib_reader(filepath: str, **kwargs) -> Any:
    """Read joblib files"""
    import joblib
    return joblib.load(filepath, **kwargs)


@FileReaderRegistry.register(extensions=['.pickle'])
def pickle_reader(filepath: str, **kwargs) -> Any:
    """Read pickle files"""
    import pickle
    with open(filepath, 'rb') as f:
        return pickle.load(f)


@FileReaderRegistry.register(extensions=['.json'])
def json_reader(filepath: str, **kwargs) -> dict:
    """Read JSON files"""
    import json
    with open(filepath, 'r') as f:
        return json.load(f)


@FileReaderRegistry.register(extensions=['.yaml', '.yml'])
def yaml_reader(filepath: str, **kwargs) -> dict:
    """Read YAML files"""
    import yaml
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


@FileReaderRegistry.register(extensions=['.txt', '.log', '.md'])
def text_reader(filepath: str, encoding: str = 'utf-8', **kwargs) -> str:
    """Read text files"""
    with open(filepath, 'r', encoding=encoding) as f:
        return f.read()


@FileReaderRegistry.register(extensions=['.bin', '.dat'])
def binary_reader(filepath: str, **kwargs) -> bytes:
    """Read binary files"""
    with open(filepath, 'rb') as f:
        return f.read()




