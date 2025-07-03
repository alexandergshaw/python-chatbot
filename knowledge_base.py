"""
Knowledge Base for the Chatbot

This module implements an AI-powered knowledge base using sentence transformers.
It can:
1. Store question-answer pairs
2. Find the most similar questions to a user's query
3. Return the best matching answer
4. Save and load knowledge from files

Key concepts:
- Sentence Transformers: Convert text into numbers (embeddings) that capture meaning
- Cosine Similarity: Measure how similar two pieces of text are
- Knowledge Entry: A stored question-answer pair with optional metadata
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import json
import yaml
import os
from typing import List, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the knowledge base with a sentence transformer model.
        
        Args:
            model_name (str): Name of the pre-trained model to use.
                            Default is 'all-MiniLM-L6-v2', which is a good
                            balance between speed and accuracy.
        
        The sentence transformer model converts text into vectors (embeddings)
        that capture the meaning of the text. Similar meanings will have
        similar vectors, even if they use different words.
        """
        # Load the AI model that converts text to meaningful numbers
        self.model = SentenceTransformer(model_name)
        # List to store our knowledge entries (questions and answers)
        self.knowledge_entries = []
        # Cache for the numerical representations of our questions
        self.embeddings = None
        
    def load_from_file(self, file_path: str) -> None:
        """
        Load knowledge base from a JSON or YAML file.
        
        Args:
            file_path (str): Path to the file to load from
            
        The file should contain a list of entries, where each entry has:
        - question: The text someone might ask
        - answer: The response to give
        - metadata: Optional extra information about this entry
        
        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        try:
            # Figure out what type of file we're reading (JSON or YAML)
            _, ext = os.path.splitext(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                if ext.lower() == '.json':
                    data = json.load(f)
                elif ext.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")
                
            # Make sure the file contains valid data
            if not isinstance(data, list):
                raise ValueError("Knowledge base must be a list of entries")
                
            for entry in data:
                if not isinstance(entry, dict):
                    raise ValueError("Each entry must be a dictionary")
                if 'question' not in entry or 'answer' not in entry:
                    raise ValueError("Each entry must have 'question' and 'answer' fields")
                
            # Store the entries and update their vector representations
            self.knowledge_entries = data
            self._update_embeddings()
            logger.info(f"Loaded {len(self.knowledge_entries)} entries from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base from {file_path}: {str(e)}")
            raise
            
    def add_entry(self, question: str, answer: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a new entry to the knowledge base.
        
        Args:
            question (str): The question or prompt to match against
            answer (str): The response to give when this entry matches
            metadata (dict, optional): Additional information about this entry
                                     (e.g., categories, tags, source)
        """
        entry = {
            'question': question,
            'answer': answer,
            'metadata': metadata or {}
        }
        self.knowledge_entries.append(entry)
        # Update the vector representations to include the new entry
        self._update_embeddings()
        
    def save_to_file(self, file_path: str) -> None:
        """
        Save the current knowledge base to a file.
        
        Args:
            file_path (str): Where to save the knowledge base.
                            The file extension (.json or .yaml) determines the format.
        
        Raises:
            ValueError: If the file extension isn't supported
            IOError: If there's an error writing the file
        """
        try:
            # Determine the format to save in based on the file extension
            _, ext = os.path.splitext(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                if ext.lower() == '.json':
                    json.dump(self.knowledge_entries, f, indent=2, ensure_ascii=False)
                elif ext.lower() in ['.yml', '.yaml']:
                    yaml.dump(self.knowledge_entries, f, allow_unicode=True)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")
            logger.info(f"Saved {len(self.knowledge_entries)} entries to {file_path}")
        except Exception as e:
            logger.error(f"Error saving knowledge base to {file_path}: {str(e)}")
            raise
            
    def _update_embeddings(self) -> None:
        """
        Update the vector representations (embeddings) for all questions.
        
        This is called automatically when:
        1. Loading entries from a file
        2. Adding a new entry
        
        The embeddings are used to quickly find similar questions without
        having to process the text each time.
        """
        if not self.knowledge_entries:
            self.embeddings = None
            return
            
        # Get just the questions from our entries
        questions = [entry['question'] for entry in self.knowledge_entries]
        # Convert all questions to their vector representations
        self.embeddings = self.model.encode(questions, convert_to_tensor=True)
        
    def find_best_matches(self, query: str, top_k: int = 3, threshold: float = 0.6) -> List[Dict]:
        """
        Find the best matching entries for a given query.
        
        Args:
            query (str): The text to find matches for
            top_k (int): Maximum number of matches to return
            threshold (float): Minimum similarity score (0-1) for a match
                             Higher numbers mean closer matches
        
        Returns:
            list: Up to top_k entries that match well, sorted by similarity
        """
        if not self.knowledge_entries or self.embeddings is None:
            return []
            
        # Convert the query to its vector representation
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Calculate how similar the query is to each stored question
        similarities = np.inner(self.embeddings, query_embedding)
        
        # Find the indices of the top K most similar questions
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build the list of matching entries with their similarity scores
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= threshold:
                entry = self.knowledge_entries[idx].copy()
                entry['similarity'] = similarity
                results.append(entry)
                
        return results
        
    def get_response(self, query: str, include_similarity: bool = False) -> Union[str, Dict]:
        """
        Get the best response for a query.
        
        Args:
            query (str): The text to find a response for
            include_similarity (bool): Whether to return the confidence score
        
        Returns:
            Union[str, dict]: Either just the answer string, or a dictionary
                            with both the answer and its similarity score
        """
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

# Example knowledge base format:
"""
[
    {
        "question": "What is Python?",
        "answer": "Python is a high-level, interpreted programming language...",
        "metadata": {
            "category": "programming",
            "tags": ["basics", "introduction"]
        }
    },
    ...
]
""" 