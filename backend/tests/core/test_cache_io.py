from app.core import cache_io


def test_read_missing_returns_none(tmp_path):
    assert cache_io.read_json_dict_safe(tmp_path / 'nope.json') is None


def test_read_invalid_json_returns_none(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{', encoding='utf-8')
    assert cache_io.read_json_dict_safe(path) is None


def test_read_non_dict_returns_none(tmp_path):
    path = tmp_path / 'arr.json'
    path.write_text('[1]', encoding='utf-8')
    assert cache_io.read_json_dict_safe(path) is None


def test_write_atomic_roundtrip(tmp_path):
    path = tmp_path / 'sub' / 'data.json'
    payload = {'a': 1, 'b': 'δ'}
    cache_io.write_json_atomic(path, payload, indent=2)
    assert cache_io.read_json_dict_safe(path) == payload
