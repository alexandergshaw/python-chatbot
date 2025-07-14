from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os
from typing import List, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.knowledge_entries = []
        self.embeddings = None

    def load_from_file(self, file_path: str) -> None:
        try:
            _, ext = os.path.splitext(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                if ext.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")
            if not isinstance(data, list):
                raise ValueError("Knowledge base must be a list of entries")
            for entry in data:
                if not isinstance(entry, dict):
                    raise ValueError("Each entry must be a dictionary")
                if 'question' not in entry or 'answer' not in entry:
                    raise ValueError("Each entry must have 'question' and 'answer' fields")
            self.knowledge_entries = data
            self._update_embeddings()
            logger.info(f"Loaded {len(self.knowledge_entries)} entries from {file_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base from {file_path}: {str(e)}")
            raise

    def add_entry(self, question: str, answer: str, metadata: Optional[Dict] = None) -> None:
        entry = {
            'question': question,
            'answer': answer,
            'metadata': metadata or {}
        }
        self.knowledge_entries.append(entry)
        self._update_embeddings()

    def save_to_file(self, file_path: str) -> None:
        try:
            _, ext = os.path.splitext(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                if ext.lower() == '.json':
                    json.dump(self.knowledge_entries, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")
            logger.info(f"Saved {len(self.knowledge_entries)} entries to {file_path}")
        except Exception as e:
            logger.error(f"Error saving knowledge base to {file_path}: {str(e)}")
            raise

    def _update_embeddings(self) -> None:
        if not self.knowledge_entries:
            self.embeddings = None
            return
        questions = [entry['question'] for entry in self.knowledge_entries]
        self.embeddings = self.model.encode(questions, convert_to_tensor=True)

    def find_best_matches(self, query: str, top_k: int = 3, threshold: float = 0.6) -> List[Dict]:
        if not self.knowledge_entries or self.embeddings is None:
            return []
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        similarities = np.inner(self.embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= threshold:
                entry = self.knowledge_entries[idx].copy()
                entry['similarity'] = similarity
                results.append(entry)
        return results

    def get_response(self, query: str, include_similarity: bool = False) -> Union[str, Dict]:
        matches = self.find_best_matches(query, top_k=1)
        if not matches:
            return {
                'answer': "I don't have enough information to answer that question.",
                'similarity': 0.0
            } if include_similarity else "I don't have enough information to answer that question."
        best_match = matches[0]
        if include_similarity:
            return {
                'answer': best_match['answer'],
                'similarity': best_match['similarity']
            }
        return best_match['answer']
