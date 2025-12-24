"""Test suite for the Ultimate Kids Curiosity Club."""


def test_basic_import():
    """Test that the main package can be imported."""
    # Import inside test to verify package structure
    import src

    assert src.__version__ == "0.1.0"
