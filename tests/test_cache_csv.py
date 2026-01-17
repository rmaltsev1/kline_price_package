"""Tests for CSV cache handler."""

import pytest
import pandas as pd
from pathlib import Path
from kline_package.cache import CSVCache


class TestCSVCache:
    """Test suite for CSVCache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return CSVCache(cache_dir=str(tmp_path))
    
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
        assert cache.extension == ".csv"
    
    def test_save(self, cache, sample_data):
        """Test saving a DataFrame."""
        cache.save(sample_data, "test_file")
        file_path = cache.cache_dir / "test_file.csv"
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
    
    def test_save_without_index(self, cache, sample_data):
        """Test saving without index."""
        cache.save(sample_data, "no_index", index=False)
        assert cache.exists("no_index")


class TestCSVCacheDataIntegrity:
    """Test data integrity for CSV cache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return CSVCache(cache_dir=str(tmp_path))
    
    def test_numeric_values(self, cache):
        """Test that numeric values are preserved."""
        data = pd.DataFrame({'price': [1.5, 2.7, 3.9]})
        cache.save(data, "numeric_test")
        loaded = cache.load("numeric_test")
        
        assert loaded['price'].iloc[0] == pytest.approx(1.5)
        assert loaded['price'].iloc[1] == pytest.approx(2.7)
        assert loaded['price'].iloc[2] == pytest.approx(3.9)
    
    def test_string_values(self, cache):
        """Test that string values are preserved."""
        data = pd.DataFrame({'symbol': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']})
        cache.save(data, "string_test")
        loaded = cache.load("string_test")
        
        assert loaded['symbol'].iloc[0] == 'BTCUSDT'
        assert loaded['symbol'].iloc[1] == 'ETHUSDT'
    
    def test_load_with_custom_index_col(self, cache):
        """Test loading with custom index column."""
        data = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        cache.save(data, "custom_index")
        loaded = cache.load("custom_index", index_col=None)
        assert 'col1' in loaded.columns


class TestCSVCacheEdgeCases:
    """Test edge cases for CSV cache."""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create a temporary cache instance."""
        return CSVCache(cache_dir=str(tmp_path))
    
    def test_special_characters_in_filename(self, cache):
        """Test filenames with special patterns."""
        data = pd.DataFrame({'value': [1, 2, 3]})
        cache.save(data, "BTCUSDT_1h_2024")
        assert cache.exists("BTCUSDT_1h_2024")
    
    def test_large_dataframe(self, cache):
        """Test with larger DataFrame."""
        data = pd.DataFrame({
            'value': range(10000),
            'price': [float(i) * 1.5 for i in range(10000)]
        })
        cache.save(data, "large_test")
        loaded = cache.load("large_test")
        assert len(loaded) == 10000
    
    def test_unicode_data(self, cache):
        """Test handling unicode characters in data."""
        data = pd.DataFrame({'symbol': ['BTC₿', 'ETH∆', 'USD$']})
        cache.save(data, "unicode_test")
        loaded = cache.load("unicode_test")
        assert loaded['symbol'].iloc[0] == 'BTC₿'
