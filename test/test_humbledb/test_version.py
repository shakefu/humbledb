"""
Tests for humbledb._version module.

This module tests version checking helpers and kwargs cleaning functionality.
"""

from unittest.mock import patch

from humbledb._version import _clean, _gte, _lt


# Test _lt function
@patch("humbledb._version.get_version")
def test_lt_true_when_pymongo_version_is_lower(mock_get_version):
    """Test _lt returns True when pymongo version is lower than target."""
    mock_get_version.return_value = "2.8.0"
    assert _lt("3.0.0") is True


@patch("humbledb._version.get_version")
def test_lt_false_when_pymongo_version_is_higher(mock_get_version):
    """Test _lt returns False when pymongo version is higher than target."""
    mock_get_version.return_value = "3.2.0"
    assert _lt("3.0.0") is False


@patch("humbledb._version.get_version")
def test_lt_false_when_pymongo_version_is_equal(mock_get_version):
    """Test _lt returns False when pymongo version equals target."""
    mock_get_version.return_value = "3.0.0"
    assert _lt("3.0.0") is False


@patch("humbledb._version.get_version")
def test_lt_with_complex_versions(mock_get_version):
    """Test _lt with complex version strings."""
    mock_get_version.return_value = "3.0.1"
    assert _lt("3.0.2") is True
    assert _lt("3.0.0") is False


@patch("humbledb._version.get_version")
def test_lt_with_prerelease_versions(mock_get_version):
    """Test _lt with pre-release versions."""
    mock_get_version.return_value = "3.0.0rc1"
    assert _lt("3.0.0") is True


# Test _gte function
@patch("humbledb._version.get_version")
def test_gte_true_when_pymongo_version_is_higher(mock_get_version):
    """Test _gte returns True when pymongo version is higher than target."""
    mock_get_version.return_value = "3.2.0"
    assert _gte("3.0.0") is True


@patch("humbledb._version.get_version")
def test_gte_true_when_pymongo_version_is_equal(mock_get_version):
    """Test _gte returns True when pymongo version equals target."""
    mock_get_version.return_value = "3.0.0"
    assert _gte("3.0.0") is True


@patch("humbledb._version.get_version")
def test_gte_false_when_pymongo_version_is_lower(mock_get_version):
    """Test _gte returns False when pymongo version is lower than target."""
    mock_get_version.return_value = "2.8.0"
    assert _gte("3.0.0") is False


@patch("humbledb._version.get_version")
def test_gte_with_complex_versions(mock_get_version):
    """Test _gte with complex version strings."""
    mock_get_version.return_value = "3.0.1"
    assert _gte("3.0.0") is True
    assert _gte("3.0.1") is True
    assert _gte("3.0.2") is False


@patch("humbledb._version.get_version")
def test_gte_with_prerelease_versions(mock_get_version):
    """Test _gte with pre-release versions."""
    mock_get_version.return_value = "3.0.0rc1"
    assert _gte("2.9.0") is True


# Test _clean function
@patch("humbledb._version._lt")
def test_clean_returns_early_for_old_pymongo_versions(mock_lt):
    """Test _clean returns early when pymongo version is less than 3.0."""
    mock_lt.return_value = True
    kwargs = {"safe": False, "other_param": "value"}
    original_kwargs = kwargs.copy()

    _clean(kwargs)

    # Should not modify kwargs for old versions
    assert kwargs == original_kwargs
    mock_lt.assert_called_once_with("3.0")


@patch("humbledb._version._lt")
def test_clean_returns_early_when_no_safe_param(mock_lt):
    """Test _clean returns early when 'safe' parameter is not present."""
    mock_lt.return_value = False
    kwargs = {"other_param": "value", "w": 1}
    original_kwargs = kwargs.copy()

    _clean(kwargs)

    # Should not modify kwargs when no 'safe' param
    assert kwargs == original_kwargs


@patch("humbledb._version._lt")
def test_clean_converts_safe_false_to_w_zero(mock_lt):
    """Test _clean converts safe=False to w=0."""
    mock_lt.return_value = False
    kwargs = {"safe": False, "other_param": "value"}

    _clean(kwargs)

    expected = {"w": 0, "other_param": "value"}
    assert kwargs == expected


@patch("humbledb._version._lt")
def test_clean_removes_safe_true(mock_lt):
    """Test _clean removes safe=True without adding w parameter."""
    mock_lt.return_value = False
    kwargs = {"safe": True, "other_param": "value"}

    _clean(kwargs)

    expected = {"other_param": "value"}
    assert kwargs == expected


@patch("humbledb._version._lt")
def test_clean_removes_safe_none(mock_lt):
    """Test _clean removes safe=None without adding w parameter."""
    mock_lt.return_value = False
    kwargs = {"safe": None, "other_param": "value"}

    _clean(kwargs)

    expected = {"other_param": "value"}
    assert kwargs == expected


@patch("humbledb._version._lt")
def test_clean_removes_safe_string(mock_lt):
    """Test _clean removes safe with string value without adding w parameter."""
    mock_lt.return_value = False
    kwargs = {"safe": "acknowledge", "other_param": "value"}

    _clean(kwargs)

    expected = {"other_param": "value"}
    assert kwargs == expected


@patch("humbledb._version._lt")
def test_clean_handles_empty_kwargs(mock_lt):
    """Test _clean handles empty kwargs dictionary."""
    mock_lt.return_value = False
    kwargs = {}

    _clean(kwargs)

    assert kwargs == {}


@patch("humbledb._version._lt")
def test_clean_preserves_existing_w_parameter_when_safe_false(mock_lt):
    """Test _clean overwrites existing w parameter when safe=False."""
    mock_lt.return_value = False
    kwargs = {"safe": False, "w": 2, "other_param": "value"}

    _clean(kwargs)

    expected = {"w": 0, "other_param": "value"}
    assert kwargs == expected


@patch("humbledb._version._lt")
def test_clean_preserves_existing_w_parameter_when_safe_not_false(mock_lt):
    """Test _clean preserves existing w parameter when safe is not False."""
    mock_lt.return_value = False
    kwargs = {"safe": True, "w": 2, "other_param": "value"}

    _clean(kwargs)

    expected = {"w": 2, "other_param": "value"}
    assert kwargs == expected


# Integration and edge case tests
@patch("humbledb._version.get_version")
def test_version_functions_with_actual_version_format(mock_get_version):
    """Test version functions with realistic version formats."""
    # Test with actual PyMongo-like version
    mock_get_version.return_value = "4.6.1"

    assert _lt("5.0.0") is True
    assert _lt("4.0.0") is False
    assert _gte("4.0.0") is True
    assert _gte("5.0.0") is False


@patch("humbledb._version._lt")
def test_clean_function_integration_old_version(mock_lt):
    """Test _clean function behavior with old PyMongo version."""
    mock_lt.return_value = True  # Simulate old version < 3.0

    kwargs = {"safe": False, "fsync": True}
    _clean(kwargs)

    # Should be unchanged for old versions
    assert kwargs == {"safe": False, "fsync": True}


@patch("humbledb._version._lt")
def test_clean_function_integration_new_version(mock_lt):
    """Test _clean function behavior with new PyMongo version."""
    mock_lt.return_value = False  # Simulate new version >= 3.0

    kwargs = {"safe": False, "fsync": True}
    _clean(kwargs)

    # Should transform safe=False to w=0
    assert kwargs == {"w": 0, "fsync": True}
