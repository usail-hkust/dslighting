"""Case-based vector retrieval service used by RAG-enabled workflows."""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
from transformers import AutoModel, AutoTokenizer

from dslighting.core.interfaces.vector_storage import VectorStorageInterface

__all__ = ["VDBService"]

logger = logging.getLogger(__name__)


class VDBService(VectorStorageInterface):
    """
    Manages embedding and retrieving text documents (cases) for retrieval-augmented generation.

    This service uses transformer-based embeddings to build a vector index of case files,
    enabling semantic similarity search for case-based reasoning.
    """

    def __init__(self, case_dir: str, model_name: str = "BAAI/llm-embedder"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()
        self.model_name = model_name
        self.case_dir = str(case_dir)
        self.case_files: List[Path] = []
        self.case_texts: Dict[str, str] = {}  # key -> text content
        self.embedding_bank: Optional[torch.Tensor] = None
        self._build_index(Path(case_dir))

    def _build_index(self, case_dir: Path):
        """Loads cases from a directory and builds the vector index."""
        logger.info(
            "Building vector index from case_dir=%s with model=%s on device=%s",
            case_dir,
            self.model_name,
            self.device,
        )
        if not case_dir.exists():
            logger.warning(f"Case directory not found: {case_dir}. Creating empty index.")
            return

        self.case_files = sorted(list(case_dir.glob("*.py")))
        case_texts = []
        for file_path in self.case_files:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            case_texts.append(text)
            self.case_texts[str(file_path)] = text

        if not case_texts:
            logger.warning("No case files found to build index.")
            return

        with torch.no_grad():
            inputs = self.tokenizer(case_texts, padding=True, truncation=True, return_tensors='pt', max_length=512).to(self.device)
            outputs = self.model(**inputs)
            # Use CLS pooling
            embeddings = outputs.last_hidden_state[:, 0]
            self.embedding_bank = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        logger.info(f"Successfully built index with {len(self.case_files)} cases.")

    def _semantic_retrieve_with_scores(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        if self.embedding_bank is None or top_k <= 0:
            return []

        with torch.no_grad():
            inputs = self.tokenizer(
                [query],
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            ).to(self.device)
            query_embedding = self.model(**inputs).last_hidden_state[:, 0]
            query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)

        similarity = (query_embedding @ self.embedding_bank.T).view(-1)
        values, indices = torch.topk(similarity, min(top_k, len(self.case_files)))
        return [(int(idx), float(score)) for idx, score in zip(indices.tolist(), values.tolist())]

    async def store_documents(self, documents: list):
        """Store documents in vector database.

        Note: Dynamic document storage is not supported. Use a dedicated
        vector database solution like FAISS, ChromaDB, or Milvus.

        Raises:
            NotImplementedError: Always, as dynamic document storage is not supported.
        """
        raise NotImplementedError(
            "VDBService does not support dynamic document storage. "
            "Use a dedicated vector database solution like FAISS, ChromaDB, or Milvus."
        )

    # === VectorStorageInterface Implementation ===

    def add(
        self,
        key: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a vector to the store.

        Note: VDBService uses transformer embeddings for case files.
        Direct vector addition is not supported.

        Raises:
            NotImplementedError: Always, as dynamic vector addition is not supported.
        """
        raise NotImplementedError(
            "VDBService does not support dynamic vector addition. "
            "Case vectors are built from case_dir at initialization."
        )

    def search(
        self,
        query: Union[List[float], str],
        limit: int = 10,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.

        Args:
            query: Query text or vector (text preferred for VDBService)
            limit: Maximum number of results
            **kwargs: Additional parameters (e.g., top_k for backward compatibility)

        Returns:
            List of (key, similarity_score) tuples
        """
        if not isinstance(query, str):
            raise NotImplementedError(
                "VDBService only supports text queries for semantic search. "
                "Use retrieve_cases(query, top_k) with a string query."
            )

        top_k = int(kwargs.get("top_k", limit))
        hits = self._semantic_retrieve_with_scores(query=query, top_k=top_k)
        return [(str(self.case_files[idx]), score) for idx, score in hits]

    def retrieve(
        self,
        key: str,
        include_metadata: bool = True
    ) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve a vector by its key.

        Note: VDBService retrieves by text query, not by key.
        For key-based retrieval, use SimpleVectorStore instead.

        Raises:
            NotImplementedError: Always, as key-based retrieval is not supported.
        """
        raise NotImplementedError(
            "VDBService does not support key-based retrieval. "
            "Use retrieve_cases(query, top_k) for semantic search."
        )

    def retrieve_cases(
        self,
        query: str,
        top_k: int = 5
    ) -> List[str]:
        """
        Retrieve the top_k most similar case texts for a given query.

        This is the primary method for VDBService semantic search.

        Args:
            query: Text query to search for
            top_k: Number of results to return

        Returns:
            List of retrieved case texts
        """
        hits = self._semantic_retrieve_with_scores(query=query, top_k=top_k)
        return [self.case_texts.get(str(self.case_files[idx]), "") for idx, _ in hits]

    def update(
        self,
        key: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing vector's metadata or vector data.

        Raises:
            NotImplementedError: Always, as dynamic updates are not supported.
        """
        raise NotImplementedError(
            "VDBService does not support dynamic updates. "
            "Reinitialize with updated case_dir to refresh the index."
        )

    def delete(self, key: str) -> bool:
        """
        Delete a vector by key.

        Raises:
            NotImplementedError: Always, as dynamic deletion is not supported.
        """
        raise NotImplementedError(
            "VDBService does not support dynamic deletion. "
            "Remove files from case_dir and reinitialize to refresh the index."
        )

    def clear(self) -> None:
        """
        Clear all vectors from the store.
        """
        self.case_files = []
        self.case_texts = {}
        self.embedding_bank = None
        logger.info("VDBService vector store cleared.")

    def count(self) -> int:
        """
        Get the number of vectors in the store.

        Returns:
            Number of stored vectors (case files)
        """
        return len(self.case_files)

    async def search_async(self, query: str, top_k: int = 5):
        """Async search for similar documents."""
        return self.retrieve_cases(query, top_k)
