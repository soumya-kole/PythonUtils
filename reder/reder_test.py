
from reder.utils.custom_reader import read_file
from reder.utils.reder_registry import FileReaderRegistry, csv_reader, json_reader, joblib_reader, parquet_reader, text_reader

if __name__ == "__main__":
    import pandas as pd
    import joblib
    from pathlib import Path

    print("=" * 70)
    print("SIMPLIFIED FILE READER WITH REGISTRATION")
    print("=" * 70)


    # Create test files
    print("\nCreating test files...")
    df = pd.DataFrame({'id': [1, 2, 3], 'name': ['Alice', 'Bob', 'Charlie']})
    df.to_csv('test.csv', index=False)
    df.to_parquet('test.parquet', index=False)
    joblib.dump({'model': 'random_forest', 'accuracy': 0.95}, 'test.joblib')
    Path('test.json').write_text('{"status": "success", "count": 42}')
    Path('test.txt').write_text('Hello, World!')
    print("✓ Test files created")

    # Method 1: Explicit reader
    print("\n" + "=" * 70)
    print("METHOD 1: Explicit Reader (with validation)")
    print("=" * 70)

    print("\n1. Read CSV with explicit reader:")


    @FileReaderRegistry.register(extensions=['.csv'])
    def my_reader(filepath: str, **kwargs) -> bytes:
        """Read binary files"""
        return pd.read_csv(filepath, **kwargs)

    print(read_file('test.csv', csv_reader))

