import pandas as pd
import numpy as np
import Levenshtein  # python-Levenshtein para otimização
import jellyfish    # para Jaro-Winkler
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Importar o matcher personalizado
try:
    from custom_model_integration import CustomTrainedMatcher
    CUSTOM_MODEL_AVAILABLE = True
except ImportError:
    CUSTOM_MODEL_AVAILABLE = False
    print("⚠️ Modelo personalizado não disponível. Usando apenas algoritmos padrão.")

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
            
            # Adicionar configuração do modelo personalizado se disponível
            if 'custom_trained' in config and CUSTOM_MODEL_AVAILABLE:
                self.config.update({
                    'custom_threshold': config['custom_trained'].get('threshold', 0.75),
                    'custom_model_path': config['custom_trained'].get('model_path', 'company_matching_trainer/models/manual_validated_matcher'),
                    'custom_batch_size': config['custom_trained'].get('batch_size', 32),
                    'custom_max_length': config['custom_trained'].get('max_length', 128)
                })
        
        # Initialize sentence transformer model (load on first use)
        self.embedding_model = None
        
        # Initialize custom matcher (load on first use)
        self.custom_matcher = None
    
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
    
    def _load_custom_matcher(self):
        """Carrega o matcher personalizado sob demanda"""
        if self.custom_matcher is None and CUSTOM_MODEL_AVAILABLE:
            try:
                custom_config = {
                    'custom_threshold': self.config.get('custom_threshold', 0.75),
                    'model_path': self.config.get('custom_model_path', 'company_matching_trainer/models/manual_validated_matcher'),
                    'batch_size': self.config.get('custom_batch_size', 32),
                    'max_length': self.config.get('custom_max_length', 128)
                }
                self.custom_matcher = CustomTrainedMatcher(custom_config)
                print("✅ Modelo personalizado carregado com sucesso")
            except Exception as e:
                print(f"❌ Erro ao carregar modelo personalizado: {e}")
                raise
    
    def preprocess_text(self, text):
        """Preprocess text for better matching"""
        if pd.isna(text):
            return ""
        
        # Convert to string if not already
        text = str(text).lower().strip()
        
        # Extract company name from info_empresa format: [CNPJ] NOME DA EMPRESA [UF] [Porte] [CNAE]
        if text.startswith('[') and ']' in text:
            # Find the end of CNPJ and start of company name
            first_bracket_end = text.find(']')
            if first_bracket_end != -1:
                # Extract everything after first ] until next [
                remaining = text[first_bracket_end + 1:].strip()
                next_bracket = remaining.find('[')
                if next_bracket != -1:
                    text = remaining[:next_bracket].strip()
                else:
                    text = remaining
        
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
    
    def embedding_matching(self, source_df, target_df, source_col, target_col, date_cols=None, save_partial=True):
        """
        OTIMIZAÇÃO 1: Aplicar filtro de data ANTES de gerar embeddings
        Reduz de 76M para ~8M comparações (90% de redução!)
        
        Args:
            source_df: DataFrame with source data (e.g., GEREM interactions)
            target_df: DataFrame with target data (e.g., prospections)
            source_col: Column name in source_df to use for matching
            target_col: Column name in target_df to use for matching
            date_cols: Tuple (source_date_col, target_date_col) for date filtering
            save_partial: Whether to save partial results during processing
            
        Returns:
            DataFrame with matches and similarity scores
        """
        # Load embedding model
        self._load_embedding_model()
        
        # Preprocess data
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # Filter out empty strings
        source_df = source_df[source_df['normalized_text'] != ""]
        target_df = target_df[target_df['normalized_text'] != ""]
        
        if source_df.empty or target_df.empty:
            return pd.DataFrame()
        
        # *** FILTRO DE DATA ANTECIPADO - MAIOR IMPACTO ***
        if date_cols and len(date_cols) == 2:
            print("🔥 Aplicando filtro de data ANTES dos embeddings...")
            
            # Criar pares válidos baseados na data
            valid_pairs = []
            valid_target_indices = set()
            
            for source_idx, source_row in source_df.iterrows():
                source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                if not pd.isna(source_date):
                    # Encontrar targets com data posterior
                    mask = pd.to_datetime(target_df[date_cols[1]], errors='coerce') > source_date
                    valid_targets = target_df[mask]
                    
                    for target_idx, target_row in valid_targets.iterrows():
                        valid_pairs.append((source_idx, target_idx))
                        valid_target_indices.add(target_idx)
            
            # Filtrar apenas os targets que têm pelo menos um match de data
            target_df_filtered = target_df.loc[list(valid_target_indices)]
            
            original_comparisons = len(source_df) * len(target_df)
            new_comparisons = len(valid_pairs)
            reduction = (1 - new_comparisons/original_comparisons) * 100
            
            print(f"📊 Filtro de data: {original_comparisons:,} → {new_comparisons:,} comparações")
            print(f"🎯 Redução: {reduction:.1f}%")
            
            target_df = target_df_filtered
        
        # Gerar embeddings apenas para dados filtrados
        source_texts = source_df['normalized_text'].tolist()
        target_texts = target_df['normalized_text'].tolist()
        
        print(f"🧠 Gerando embeddings: {len(source_texts)} origem × {len(target_texts)} destino")
        
        source_embeddings = self.embedding_model.encode(source_texts, batch_size=32, show_progress_bar=True)
        target_embeddings = self.embedding_model.encode(target_texts, batch_size=32, show_progress_bar=True)
        
        # Calcular similaridade apenas para pares válidos
        matches = []
        if date_cols:
            # Usar apenas pares válidos de data
            source_to_idx = {idx: i for i, idx in enumerate(source_df.index)}
            target_to_idx = {idx: i for i, idx in enumerate(target_df.index)}
            
            print(f"🔍 Processando {len(valid_pairs):,} comparações válidas...")
            
            # Processar em lotes para evitar travamento
            batch_size = 10000  # Processar 10k comparações por vez
            total_batches = (len(valid_pairs) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, len(valid_pairs))
                batch_pairs = valid_pairs[start_idx:end_idx]
                
                print(f"📦 Processando lote {batch_idx + 1}/{total_batches} ({len(batch_pairs):,} comparações)")
                
                for source_idx, target_idx in batch_pairs:
                    if source_idx in source_to_idx and target_idx in target_to_idx:
                        i = source_to_idx[source_idx]
                        j = target_to_idx[target_idx]
                        
                        similarity = cosine_similarity([source_embeddings[i]], [target_embeddings[j]])[0, 0]
                        
                        if similarity >= self.config['embedding_threshold']:
                            source_row = source_df.loc[source_idx]
                            target_row = target_df.loc[target_idx]
                            
                            # Extrair ano da data de interação GEREM
                            source_year = None
                            if date_cols and len(date_cols) >= 1:
                                try:
                                    source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                                    if not pd.isna(source_date):
                                        source_year = source_date.year
                                except:
                                    pass
                            
                            match_data = {
                                'source_id': source_idx,
                                'target_id': target_idx,
                                'source_text': source_row[source_col],
                                'target_text': target_row[target_col],
                                'similarity': similarity,
                                'algorithm': 'embedding'
                            }
                            
                            # Adicionar coluna de ano se disponível
                            if source_year is not None:
                                match_data['ano_interacao'] = source_year
                            
                            matches.append(match_data)
                
                # Mostrar progresso a cada lote
                matches_found = len(matches)
                print(f"✅ Lote {batch_idx + 1} concluído. Matches encontrados até agora: {matches_found:,}")
                
                # Salvar resultados parciais a cada 10 lotes ou no último lote
                if save_partial and (batch_idx % 10 == 0 or batch_idx == total_batches - 1):
                    if matches:
                        partial_df = pd.DataFrame(matches).sort_values('similarity', ascending=False)
                        partial_filename = f"embedding_matches_partial_batch_{batch_idx + 1}.xlsx"
                        try:
                            partial_df.to_excel(partial_filename, index=False)
                            print(f"💾 Resultados parciais salvos: {partial_filename}")
                        except Exception as e:
                            print(f"⚠️ Erro ao salvar resultados parciais: {e}")
                
                # Permitir interrupção controlada
                try:
                    import time
                    time.sleep(0.1)  # Pequena pausa para permitir KeyboardInterrupt
                except KeyboardInterrupt:
                    print(f"\n🛑 Processo interrompido pelo usuário no lote {batch_idx + 1}")
                    print(f"📊 Matches encontrados até a interrupção: {len(matches):,}")
                    if matches:
                        interrupted_df = pd.DataFrame(matches).sort_values('similarity', ascending=False)
                        interrupted_filename = f"embedding_matches_interrupted_batch_{batch_idx + 1}.xlsx"
                        try:
                            interrupted_df.to_excel(interrupted_filename, index=False)
                            print(f"💾 Resultados salvos antes da interrupção: {interrupted_filename}")
                        except:
                            pass
                    return pd.DataFrame(matches).sort_values('similarity', ascending=False) if matches else pd.DataFrame()
        else:
            # Método original se não há filtro de data
            print("Calculando matriz de similaridade...")
            similarity_matrix = cosine_similarity(source_embeddings, target_embeddings)
            
            # For each source record
            for i, (_, source_row) in enumerate(source_df.iterrows()):
                # Find matches in target
                for j, (_, target_row) in enumerate(target_df.iterrows()):
                    # Get similarity from matrix
                    similarity = similarity_matrix[i, j]
                    
                    # Keep match if above threshold
                    if similarity >= self.config['embedding_threshold']:
                        # Extrair ano da data de interação GEREM
                        source_year = None
                        if date_cols and len(date_cols) >= 1:
                            try:
                                source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                                if not pd.isna(source_date):
                                    source_year = source_date.year
                            except:
                                pass
                        
                        match_data = {
                            'source_id': source_row.name,
                            'target_id': target_row.name,
                            'source_text': source_row[source_col],
                            'target_text': target_row[target_col],
                            'similarity': similarity,
                            'algorithm': 'embedding'
                        }
                        
                        # Adicionar coluna de ano se disponível
                        if source_year is not None:
                            match_data['ano_interacao'] = source_year
                        
                        matches.append(match_data)
        
        return pd.DataFrame(matches).sort_values('similarity', ascending=False) if matches else pd.DataFrame()
    
    def custom_trained_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        VERSÃO OTIMIZADA - Matching usando modelo personalizado treinado com 99.50% de acurácia
        Inclui otimizações para evitar travamentos:
        - Filtro de data aplicado ANTES dos embeddings
        - Processamento em lotes pequenos
        - Limite de comparações por segurança
        - Salvamento de resultados parciais
        - Limpeza de memória
        
        Args:
            source_df: DataFrame com dados de origem (ex: GEREM interactions)
            target_df: DataFrame com dados de destino (ex: prospections)
            source_col: Nome da coluna em source_df para matching
            target_col: Nome da coluna em target_df para matching
            date_cols: Tupla (source_date_col, target_date_col) para filtro de data
            
        Returns:
            DataFrame com matches encontrados
        """
        if not CUSTOM_MODEL_AVAILABLE:
            print("❌ Modelo personalizado não disponível. Use outro algoritmo.")
            return pd.DataFrame()
        
        # Carregar matcher se necessário
        self._load_custom_matcher()
        
        # OTIMIZAÇÃO 1: Configurar para modo eficiente
        self.custom_matcher.config.update({
            'custom_threshold': self.config.get('custom_threshold', 0.75),
            'batch_size': 16,  # Reduzido para evitar travamento
            'max_comparisons_per_batch': 20000,  # Limite de segurança
            'save_partial_results': True,
            'memory_efficient': True
        })
        
        # OTIMIZAÇÃO 2: Usar método otimizado
        return self.custom_matcher.custom_trained_matching(
            source_df, target_df, source_col, target_col, date_cols
        )
