from app.core import paths


def test_backend_root_contains_app_package():
    root = paths.backend_root_dir()
    assert (root / 'app').is_dir()
    assert (root / 'app' / 'core' / 'paths.py').is_file()


def test_resolve_absolute_unchanged(tmp_path):
    abs_p = tmp_path / 'x'
    assert paths.resolve_backend_path(abs_p) == abs_p


def test_resolve_relative_joins_backend_root():
    root = paths.backend_root_dir()
    assert paths.resolve_backend_path('.cache/foo') == root / '.cache' / 'foo'


def test_resolve_strips_backend_prefix():
    root = paths.backend_root_dir()
    assert paths.resolve_backend_path('backend/.cache/foo') == root / '.cache' / 'foo'
