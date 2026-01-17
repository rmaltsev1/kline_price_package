"""Tests for Parquet cache handler."""

import pytest
import pandas as pd
from pathlib import Path
from kline_package.cache import ParquetCache


class TestParquetCache:
    """Test suite for ParquetCache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return ParquetCache(cache_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Open Time': pd.date_range('2024-01-01', periods=10, freq='h', tz='UTC'),
            'Open': [100.0 + i for i in range(10)],
            'High': [101.0 + i for i in range(10)],
            'Low': [99.0 + i for i in range(10)],
            'Close': [100.5 + i for i in range(10)],
            'Volume': [1000.0 + i*10 for i in range(10)]
        })
    
    def test_initialization(self, cache, tmp_path):
        """Test cache initialization."""
        assert cache is not None
        assert cache.cache_dir == tmp_path
        assert tmp_path.exists()
    
    def test_extension(self, cache):
        """Test that correct extension is set."""
        assert cache.extension == ".parquet"
    
    def test_save(self, cache, sample_data):
        """Test saving a DataFrame."""
        cache.save(sample_data, "test_file")
        file_path = cache.cache_dir / "test_file.parquet"
        assert file_path.exists()
    
    def test_save_empty_raises(self, cache):
        """Test that saving empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            cache.save(empty_df, "empty_file")
    
    def test_save_none_raises(self, cache):
        """Test that saving None raises ValueError."""
        with pytest.raises(ValueError):
            cache.save(None, "none_file")
    
    def test_load(self, cache, sample_data):
        """Test loading a DataFrame."""
        cache.save(sample_data, "test_load")
        loaded = cache.load("test_load")
        
        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(sample_data)
        assert list(loaded.columns) == list(sample_data.columns)
    
    def test_load_nonexistent_raises(self, cache):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            cache.load("nonexistent")
    
    def test_exists_true(self, cache, sample_data):
        """Test exists returns True for existing file."""
        cache.save(sample_data, "exists_test")
        assert cache.exists("exists_test") is True
    
    def test_exists_false(self, cache):
        """Test exists returns False for nonexistent file."""
        assert cache.exists("nonexistent") is False
    
    def test_delete(self, cache, sample_data):
        """Test deleting a cache file."""
        cache.save(sample_data, "delete_test")
        assert cache.exists("delete_test")
        cache.delete("delete_test")
        assert cache.exists("delete_test") is False
    
    def test_delete_nonexistent_no_error(self, cache):
        """Test that deleting nonexistent file doesn't raise."""
        cache.delete("nonexistent")
    
    def test_list_files_empty(self, cache):
        """Test listing files when cache is empty."""
        files = cache.list_files()
        assert files == []
    
    def test_list_files(self, cache, sample_data):
        """Test listing cache files."""
        cache.save(sample_data, "file1")
        cache.save(sample_data, "file2")
        cache.save(sample_data, "file3")
        
        files = cache.list_files()
        assert len(files) == 3
        assert "file1" in files
        assert "file2" in files
        assert "file3" in files


class TestParquetCacheCompression:
    """Test compression options for Parquet cache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return ParquetCache(cache_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame."""
        return pd.DataFrame({'value': [float(i) for i in range(100)]})
    
    def test_snappy_compression(self, cache, sample_data):
        """Test saving with snappy compression (default)."""
        cache.save(sample_data, "snappy_test", compression="snappy")
        assert cache.exists("snappy_test")
        loaded = cache.load("snappy_test")
        assert len(loaded) == 100
    
    def test_gzip_compression(self, cache, sample_data):
        """Test saving with gzip compression."""
        cache.save(sample_data, "gzip_test", compression="gzip")
        assert cache.exists("gzip_test")
        loaded = cache.load("gzip_test")
        assert len(loaded) == 100


class TestParquetCacheDataIntegrity:
    """Test data integrity for Parquet cache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return ParquetCache(cache_dir=str(tmp_path))
    
    def test_numeric_precision(self, cache):
        """Test that numeric precision is maintained."""
        data = pd.DataFrame({'price': [1.123456789012345, 2.987654321098765]})
        cache.save(data, "precision_test")
        loaded = cache.load("precision_test")
        assert loaded['price'].iloc[0] == pytest.approx(1.123456789012345, rel=1e-10)
    
    def test_datetime_preservation(self, cache):
        """Test that datetime types are preserved."""
        data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='h', tz='UTC')
        })
        cache.save(data, "datetime_test")
        loaded = cache.load("datetime_test")
        assert pd.api.types.is_datetime64_any_dtype(loaded['timestamp'])
    
    def test_index_preservation(self, cache):
        """Test that index is preserved."""
        data = pd.DataFrame({'value': [1, 2, 3]}, index=['a', 'b', 'c'])
        cache.save(data, "index_test")
        loaded = cache.load("index_test")
        assert list(loaded.index) == ['a', 'b', 'c']
