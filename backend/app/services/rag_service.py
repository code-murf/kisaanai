"""
RAG (Retrieval-Augmented Generation) Service for KisaanAI.

Provides context-aware responses using historical price data and agricultural knowledge.
"""
import logging
from typing import List, Optional, Dict
import numpy as np

logger = logging.getLogger(__name__)

# Try to import FAISS, fall back to simple retrieval if not available
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available, using simple keyword-based retrieval")


class RAGService:
    """
    RAG service for context-aware AI responses.
    
    Usage:
        rag = RAGService()
        rag.create_index(documents)
        context = rag.retrieve("wheat price trends")
        response = bedrock.chat_with_context(query, context)
    """
    
    def __init__(self):
        self.documents = []
        self.index = None
        self.model = None
        
        if FAISS_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Initialized RAG with FAISS and SentenceTransformer")
            except Exception as e:
                logger.warning(f"Failed to initialize SentenceTransformer: {e}")
                self.model = None
    
    def create_index(self, documents: List[str]):
        """
        Create FAISS index from documents.
        
        Args:
            documents: List of text documents
        """
        self.documents = documents
        
        if not FAISS_AVAILABLE or self.model is None:
            logger.info(f"Created simple index with {len(documents)} documents")
            return
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(documents, show_progress_bar=False)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings.astype('float32'))
            
            logger.info(f"Created FAISS index with {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            self.index = None
    
    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """
        Retrieve top-k relevant documents.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if not self.documents:
            return []
        
        # Use FAISS if available
        if FAISS_AVAILABLE and self.index is not None and self.model is not None:
            return self._retrieve_with_faiss(query, k)
        
        # Fall back to simple keyword matching
        return self._retrieve_simple(query, k)
    
    def _retrieve_with_faiss(self, query: str, k: int) -> List[str]:
        """Retrieve using FAISS vector search."""
        try:
            query_embedding = self.model.encode([query], show_progress_bar=False)
            distances, indices = self.index.search(query_embedding.astype('float32'), k)
            
            results = []
            for idx in indices[0]:
                if idx < len(self.documents):
                    results.append(self.documents[idx])
            
            return results
        except Exception as e:
            logger.error(f"FAISS retrieval error: {e}")
            return self._retrieve_simple(query, k)
    
    def _retrieve_simple(self, query: str, k: int) -> List[str]:
        """Simple keyword-based retrieval."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score documents by keyword overlap
        scores = []
        for doc in self.documents:
            doc_lower = doc.lower()
            doc_words = set(doc_lower.split())
            overlap = len(query_words & doc_words)
            scores.append(overlap)
        
        # Get top-k documents
        top_indices = np.argsort(scores)[-k:][::-1]
        return [self.documents[i] for i in top_indices if scores[i] > 0]
    
    def add_documents(self, new_documents: List[str]):
        """
        Add new documents to the index.
        
        Args:
            new_documents: List of new documents to add
        """
        all_documents = self.documents + new_documents
        self.create_index(all_documents)
    
    def get_context_string(self, query: str, k: int = 3) -> str:
        """
        Get context as a formatted string.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        docs = self.retrieve(query, k)
        if not docs:
            return ""
        
        context = "Relevant Information:\n"
        for i, doc in enumerate(docs, 1):
            context += f"{i}. {doc}\n"
        
        return context


# Singleton instance
rag_service = RAGService()


# Initialize with agricultural knowledge base
AGRICULTURAL_KNOWLEDGE = [
    # Price trends
    "Wheat prices typically increase during winter months (November-February) due to higher demand.",
    "Rice prices are generally stable throughout the year but may spike during monsoon season.",
    "Cotton prices fluctuate based on global demand and weather conditions in growing regions.",
    "Sugarcane prices are influenced by sugar mill operations and government policies.",
    
    # Market insights
    "Delhi mandis offer competitive prices for wheat and rice due to high urban demand.",
    "Punjab mandis are known for best prices for wheat and rice during harvest season.",
    "Maharashtra mandis specialize in cotton and sugarcane trading.",
    "Uttar Pradesh has extensive mandi network covering multiple commodities.",
    
    # Seasonal patterns
    "Rabi crops (wheat, mustard) are harvested in March-April, leading to price drops.",
    "Kharif crops (rice, cotton) are harvested in September-October.",
    "Monsoon delays can significantly impact crop yields and prices.",
    "Post-harvest prices are typically 10-15% lower than pre-harvest prices.",
    
    # Disease information
    "Leaf blight in wheat is common during humid conditions, treat with fungicide.",
    "Rice blast disease spreads rapidly in wet conditions, requires immediate treatment.",
    "Cotton bollworm is a major pest, use integrated pest management.",
    "Rust diseases in wheat can be prevented with resistant varieties.",
    
    # Best practices
    "Selling immediately after harvest often results in lower prices.",
    "Storage facilities can help farmers wait for better prices.",
    "Diversifying crops reduces risk from price fluctuations.",
    "Government MSP (Minimum Support Price) provides price floor for major crops.",
    
    # Regional insights
    "North India: Major wheat and rice producing region.",
    "Central India: Cotton and soybean belt.",
    "South India: Rice, sugarcane, and spices.",
    "West India: Cotton, groundnut, and pulses.",
]

# Initialize RAG with knowledge base
rag_service.create_index(AGRICULTURAL_KNOWLEDGE)
logger.info("RAG service initialized with agricultural knowledge base")
