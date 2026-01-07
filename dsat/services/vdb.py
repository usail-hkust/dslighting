"""
Service for managing an in-memory vector database for case-based reasoning.
"""
import logging
from pathlib import Path
from typing import List

import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

class VDBService:
    """
    Manages embedding and retrieving text documents (cases) for retrieval-augmented generation.
    """
    def __init__(self, case_dir: str, model_name: str = "BAAI/llm-embedder"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()
        self.case_files: List[Path] = []
        self.embedding_bank: torch.Tensor = None
        self._build_index(Path(case_dir))

    def _build_index(self, case_dir: Path):
        """Loads cases from a directory and builds the vector index."""
        logger.info(f"Building vector index from cases in: {case_dir}")
        if not case_dir.exists():
            logger.warning(f"Case directory not found: {case_dir}. Creating empty index.")
            return
        
        self.case_files = sorted(list(case_dir.glob("*.py")))
        case_texts = []
        for file_path in self.case_files:
            with open(file_path, "r", encoding="utf-8") as f:
                case_texts.append(f.read())
        
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

    def retrieve(self, query: str, top_k: int) -> List[str]:
        """Retrieves the top_k most similar case texts for a given query."""
        if self.embedding_bank is None:
            return []
            
        with torch.no_grad():
            inputs = self.tokenizer([query], padding=True, truncation=True, return_tensors='pt', max_length=512).to(self.device)
            query_embedding = self.model(**inputs).last_hidden_state[:, 0]
            query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)

        similarity = (query_embedding @ self.embedding_bank.T).squeeze()
        _, indices = torch.topk(similarity, min(top_k, len(self.case_files)))

        retrieved_cases = []
        for idx in indices.tolist():
            with open(self.case_files[idx], "r", encoding="utf-8") as f:
                retrieved_cases.append(f.read())
        return retrieved_cases

    async def store_documents(self, documents: list):
        """Store documents in vector database."""
        # This method is kept for compatibility but not used in DS-Agent workflow
        pass
    
    async def search(self, query: str, top_k: int = 5):
        """Search for similar documents."""
        return self.retrieve(query, top_k)