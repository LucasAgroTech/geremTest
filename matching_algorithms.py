import pandas as pd
import numpy as np
import Levenshtein  # python-Levenshtein para otimização
import jellyfish    # para Jaro-Winkler
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class MatchingAlgorithms:
    def __init__(self, config=None):
        """Initialize matching algorithms with configuration"""
        # Default configuration
        self.config = {
            'levenshtein_threshold': 0.7,  # Threshold para Levenshtein
            'jaro_winkler_threshold': 0.8,  # Threshold para Jaro-Winkler
            'embedding_threshold': 0.6,     # Threshold para Text Embeddings
            'embedding_model': 'paraphrase-multilingual-MiniLM-L12-v2'  # Modelo para embeddings
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Initialize sentence transformer model (load on first use)
        self.embedding_model = None
    
    def _load_embedding_model(self):
        """Load the sentence transformer model on first use"""
        if self.embedding_model is None:
            try:
                print("Carregando modelo de embeddings...")
                self.embedding_model = SentenceTransformer(self.config['embedding_model'])
                print(f"Modelo '{self.config['embedding_model']}' carregado com sucesso")
            except Exception as e:
                print(f"Erro ao carregar modelo de embeddings: {e}")
                raise
    
    def preprocess_text(self, text):
        """Preprocess text for better matching"""
        if pd.isna(text):
            return ""
        
        # Convert to string if not already
        text = str(text).lower().strip()
        
        # Remove common prefixes/suffixes that don't add value
        prefixes = ['empresa ', 'companhia ', 'industria ', 'industrias ', 'ind. ']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        
        return text
    
    def levenshtein_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        Perform matching using Levenshtein distance
        
        Args:
            source_df: DataFrame with source data (e.g., GEREM interactions)
            target_df: DataFrame with target data (e.g., prospections)
            source_col: Column name in source_df to use for matching
            target_col: Column name in target_df to use for matching
            date_cols: Tuple (source_date_col, target_date_col) for date filtering
            
        Returns:
            DataFrame with matches and similarity scores
        """
        # Preprocess data
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        # Add normalized text columns for matching
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # Initialize results list
        matches = []
        
        # For each source record
        for _, source_row in source_df.iterrows():
            source_text = source_row['normalized_text']
            if not source_text:  # Skip empty strings
                continue
            
            # Filter target by date if date columns provided
            filtered_target = target_df
            if date_cols and len(date_cols) == 2:
                source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                if not pd.isna(source_date):
                    # Filter only target records with date after source date
                    filtered_target = target_df[pd.to_datetime(target_df[date_cols[1]], errors='coerce') > source_date]
            
            # Find matches in target
            for _, target_row in filtered_target.iterrows():
                target_text = target_row['normalized_text']
                if not target_text:  # Skip empty strings
                    continue
                
                # Calculate Levenshtein distance
                max_len = max(len(source_text), len(target_text))
                if max_len == 0:  # Avoid division by zero
                    similarity = 0
                else:
                    distance = Levenshtein.distance(source_text, target_text)
                    similarity = 1 - (distance / max_len)
                
                # Keep match if above threshold
                if similarity >= self.config['levenshtein_threshold']:
                    matches.append({
                        'source_id': source_row.name,
                        'target_id': target_row.name,
                        'source_text': source_row[source_col],
                        'target_text': target_row[target_col],
                        'similarity': similarity,
                        'algorithm': 'levenshtein'
                    })
        
        # Create DataFrame from matches
        matches_df = pd.DataFrame(matches)
        
        # Sort by similarity (descending)
        if not matches_df.empty:
            matches_df = matches_df.sort_values('similarity', ascending=False)
        
        return matches_df
    
    def jaro_winkler_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        Perform matching using Jaro-Winkler similarity
        
        Args:
            source_df: DataFrame with source data (e.g., GEREM interactions)
            target_df: DataFrame with target data (e.g., prospections)
            source_col: Column name in source_df to use for matching
            target_col: Column name in target_df to use for matching
            date_cols: Tuple (source_date_col, target_date_col) for date filtering
            
        Returns:
            DataFrame with matches and similarity scores
        """
        # Preprocess data
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        # Add normalized text columns for matching
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # Initialize results list
        matches = []
        
        # For each source record
        for _, source_row in source_df.iterrows():
            source_text = source_row['normalized_text']
            if not source_text:  # Skip empty strings
                continue
            
            # Filter target by date if date columns provided
            filtered_target = target_df
            if date_cols and len(date_cols) == 2:
                source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                if not pd.isna(source_date):
                    # Filter only target records with date after source date
                    filtered_target = target_df[pd.to_datetime(target_df[date_cols[1]], errors='coerce') > source_date]
            
            # Find matches in target
            for _, target_row in filtered_target.iterrows():
                target_text = target_row['normalized_text']
                if not target_text:  # Skip empty strings
                    continue
                
                # Calculate Jaro-Winkler similarity
                similarity = jellyfish.jaro_winkler_similarity(source_text, target_text)
                
                # Keep match if above threshold
                if similarity >= self.config['jaro_winkler_threshold']:
                    matches.append({
                        'source_id': source_row.name,
                        'target_id': target_row.name,
                        'source_text': source_row[source_col],
                        'target_text': target_row[target_col],
                        'similarity': similarity,
                        'algorithm': 'jaro_winkler'
                    })
        
        # Create DataFrame from matches
        matches_df = pd.DataFrame(matches)
        
        # Sort by similarity (descending)
        if not matches_df.empty:
            matches_df = matches_df.sort_values('similarity', ascending=False)
        
        return matches_df
    
    def embedding_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        Perform matching using text embeddings and cosine similarity
        
        Args:
            source_df: DataFrame with source data (e.g., GEREM interactions)
            target_df: DataFrame with target data (e.g., prospections)
            source_col: Column name in source_df to use for matching
            target_col: Column name in target_df to use for matching
            date_cols: Tuple (source_date_col, target_date_col) for date filtering
            
        Returns:
            DataFrame with matches and similarity scores
        """
        # Load embedding model if not already loaded
        self._load_embedding_model()
        
        # Preprocess data
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        # Add normalized text columns for matching
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # Filter out empty strings
        source_df = source_df[source_df['normalized_text'] != ""]
        target_df = target_df[target_df['normalized_text'] != ""]
        
        if source_df.empty or target_df.empty:
            return pd.DataFrame()
        
        # Generate embeddings for source and target texts
        source_texts = source_df['normalized_text'].tolist()
        target_texts = target_df['normalized_text'].tolist()
        
        print(f"Gerando embeddings para {len(source_texts)} textos de origem...")
        source_embeddings = self.embedding_model.encode(source_texts, convert_to_tensor=False)
        
        print(f"Gerando embeddings para {len(target_texts)} textos de destino...")
        target_embeddings = self.embedding_model.encode(target_texts, convert_to_tensor=False)
        
        print("Calculando matriz de similaridade...")
        # Calculate cosine similarity between all pairs
        similarity_matrix = cosine_similarity(source_embeddings, target_embeddings)
        
        # Initialize results list
        matches = []
        
        # For each source record
        for i, (_, source_row) in enumerate(source_df.iterrows()):
            # Find matches in target
            for j, (_, target_row) in enumerate(target_df.iterrows()):
                # Get similarity from matrix
                similarity = similarity_matrix[i, j]
                
                # Apply date filtering if specified
                if date_cols and len(date_cols) == 2:
                    source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                    target_date = pd.to_datetime(target_row[date_cols[1]], errors='coerce')
                    if not pd.isna(source_date) and not pd.isna(target_date) and target_date <= source_date:
                        continue
                
                # Keep match if above threshold
                if similarity >= self.config['embedding_threshold']:
                    matches.append({
                        'source_id': source_row.name,
                        'target_id': target_row.name,
                        'source_text': source_row[source_col],
                        'target_text': target_row[target_col],
                        'similarity': similarity,
                        'algorithm': 'embedding'
                    })
        
        # Create DataFrame from matches
        matches_df = pd.DataFrame(matches)
        
        # Sort by similarity (descending)
        if not matches_df.empty:
            matches_df = matches_df.sort_values('similarity', ascending=False)
        
        return matches_df