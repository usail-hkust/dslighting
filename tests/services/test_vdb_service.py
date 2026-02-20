from __future__ import annotations

from pathlib import Path

import pytest
import torch

from dslighting.services import vdb as vdb_module
from dslighting.services.vdb import VDBService


class _DummyBatch(dict):
    def to(self, _device):
        return self


class _DummyTokenizer:
    def __call__(self, texts, **_kwargs):
        return _DummyBatch({"texts": texts})


class _DummyOutput:
    def __init__(self, embeddings: torch.Tensor):
        self.last_hidden_state = embeddings.unsqueeze(1)


class _DummyModel:
    def to(self, _device):
        return self

    def eval(self):
        return self

    def __call__(self, **kwargs):
        texts = kwargs["texts"]
        rows = []
        for text in texts:
            lower = text.lower()
            if "alpha" in lower:
                rows.append([1.0, 0.0])
            elif "beta" in lower:
                rows.append([0.0, 1.0])
            else:
                rows.append([0.7, 0.7])
        return _DummyOutput(torch.tensor(rows, dtype=torch.float32))


@pytest.fixture
def _stub_transformers(monkeypatch):
    monkeypatch.setattr(vdb_module.AutoTokenizer, "from_pretrained", lambda _name: _DummyTokenizer())
    monkeypatch.setattr(vdb_module.AutoModel, "from_pretrained", lambda _name: _DummyModel())


def test_retrieve_cases_returns_semantic_hits(tmp_path: Path, _stub_transformers) -> None:
    case_dir = tmp_path / "cases"
    case_dir.mkdir()
    (case_dir / "alpha.py").write_text("alpha strategy", encoding="utf-8")
    (case_dir / "beta.py").write_text("beta strategy", encoding="utf-8")

    service = VDBService(case_dir=str(case_dir))
    hits = service.retrieve_cases("how to solve alpha task", top_k=1)

    assert len(hits) == 1
    assert "alpha" in hits[0].lower()


def test_search_returns_path_and_score(tmp_path: Path, _stub_transformers) -> None:
    case_dir = tmp_path / "cases"
    case_dir.mkdir()
    (case_dir / "alpha.py").write_text("alpha strategy", encoding="utf-8")

    service = VDBService(case_dir=str(case_dir))
    results = service.search("alpha query", limit=3)

    assert len(results) == 1
    key, score = results[0]
    assert key.endswith("alpha.py")
    assert isinstance(score, float)


def test_search_rejects_vector_query(tmp_path: Path, _stub_transformers) -> None:
    case_dir = tmp_path / "cases"
    case_dir.mkdir()
    (case_dir / "alpha.py").write_text("alpha strategy", encoding="utf-8")
    service = VDBService(case_dir=str(case_dir))

    with pytest.raises(NotImplementedError, match="text queries"):
        service.search([0.1, 0.2], limit=1)


def test_key_retrieve_is_not_supported(tmp_path: Path, _stub_transformers) -> None:
    case_dir = tmp_path / "cases"
    case_dir.mkdir()
    (case_dir / "alpha.py").write_text("alpha strategy", encoding="utf-8")
    service = VDBService(case_dir=str(case_dir))

    with pytest.raises(NotImplementedError, match="key-based retrieval"):
        service.retrieve("alpha.py")
