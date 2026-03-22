import importlib


def test_import_dslighting_smoke():
    module = importlib.import_module("dslighting")
    assert hasattr(module, "__version__")
    assert callable(module.help)


def test_lazy_export_registration():
    import dslighting

    assert "run_agent" in dslighting.__all__
