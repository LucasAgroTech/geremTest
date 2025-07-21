#!/usr/bin/env python3
"""
Integração do Modelo Personalizado Treinado
==========================================

Este módulo integra o modelo treinado com 99.50% de acurácia ao sistema GEREM existente.
"""

import torch
import numpy as np
import pandas as pd
import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics.pairwise import cosine_similarity
import logging

class CustomTrainedMatcher:
    """
    Algoritmo de matching usando o modelo personalizado treinado
    Compatível com a interface do sistema GEREM existente
    """
    
    def __init__(self, config=None):
        """
        Inicializa o matcher personalizado
        
        Args:
            config: Dicionário com configurações
        """
        # Configuração padrão
        self.config = {
            'custom_threshold': 0.75,
            'model_path': 'company_matching_trainer/models/manual_validated_matcher',
            'batch_size': 32,
            'max_length': 128
        }
        
        # Atualizar com configuração fornecida
        if config:
            self.config.update(config)
        
        # Componentes do modelo
        self.tokenizer = None
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Logger
        self.logger = logging.getLogger('custom_matcher')
    
    def _load_model(self):
        """Carrega o modelo treinado sob demanda"""
        if self.model is None:
            try:
                model_path = self.config['model_path']
                
                self.logger.info(f"Carregando modelo personalizado de: {model_path}")
                
                # Carregar tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                # Carregar modelo BERT para classificação
                self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
                self.model.to(self.device)
                self.model.eval()
                
                self.logger.info("✅ Modelo personalizado carregado com sucesso")
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao carregar modelo personalizado: {e}")
                # Fallback para modelo padrão
                self.logger.info("🔄 Usando modelo padrão como fallback")
                self.tokenizer = AutoTokenizer.from_pretrained('neuralmind/bert-base-portuguese-cased')
                self.model = AutoModelForSequenceClassification.from_pretrained('neuralmind/bert-base-portuguese-cased', num_labels=2)
                self.model.to(self.device)
                self.model.eval()
    
    def preprocess_text(self, text):
        """Pré-processa texto da mesma forma que o sistema original"""
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
    
    def get_embeddings(self, texts):
        """
        Gera embeddings para uma lista de textos
        
        Args:
            texts: Lista de textos
            
        Returns:
            numpy.ndarray: Embeddings dos textos
        """
        self._load_model()
        
        embeddings = []
        batch_size = self.config['batch_size']
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenizar
            encoding = self.tokenizer(
                batch_texts,
                truncation=True,
                padding='max_length',
                max_length=self.config['max_length'],
                return_tensors='pt'
            )
            
            # Mover para device
            encoding = {k: v.to(self.device) for k, v in encoding.items()}
            
            # Gerar embeddings
            with torch.no_grad():
                outputs = self.model(**encoding, output_hidden_states=True)
                # Usar [CLS] token embedding da última camada oculta
                batch_embeddings = outputs.hidden_states[-1][:, 0, :].cpu().numpy()
                embeddings.append(batch_embeddings)
        
        return np.vstack(embeddings)
    
    def apply_date_filter_optimized(self, source_df, target_df, date_cols):
        """Aplica filtro de data de forma otimizada ANTES de qualquer processamento"""
        if not date_cols or len(date_cols) != 2:
            return source_df, target_df, None
        
        self.logger.info("🔥 Aplicando filtro de data otimizado...")
        
        source_date_col, target_date_col = date_cols
        
        # Converter datas uma vez só
        source_dates = pd.to_datetime(source_df[source_date_col], errors='coerce')
        target_dates = pd.to_datetime(target_df[target_date_col], errors='coerce')
        
        # Criar índice de datas válidas
        valid_source_mask = source_dates.notna()
        valid_target_mask = target_dates.notna()
        
        source_df_filtered = source_df[valid_source_mask].copy()
        target_df_filtered = target_df[valid_target_mask].copy()
        
        source_dates_filtered = source_dates[valid_source_mask]
        target_dates_filtered = target_dates[valid_target_mask]
        
        # Criar pares válidos de forma eficiente
        valid_pairs = []
        
        # Usar broadcasting para comparação eficiente
        for i, (source_idx, source_date) in enumerate(zip(source_df_filtered.index, source_dates_filtered)):
            # Encontrar targets com data posterior
            valid_target_indices = target_df_filtered.index[target_dates_filtered > source_date]
            
            for target_idx in valid_target_indices:
                valid_pairs.append((source_idx, target_idx))
            
            # Limitar número de comparações para evitar travamento
            if len(valid_pairs) > 50000:  # Limite de segurança
                self.logger.warning(f"Atingido limite de {len(valid_pairs):,} comparações. Parando para evitar travamento.")
                break
        
        # Filtrar apenas targets que têm pelo menos um match
        target_indices_with_matches = set(pair[1] for pair in valid_pairs)
        target_df_final = target_df_filtered.loc[list(target_indices_with_matches)]
        
        original_comparisons = len(source_df) * len(target_df)
        new_comparisons = len(valid_pairs)
        reduction = (1 - new_comparisons/original_comparisons) * 100 if original_comparisons > 0 else 0
        
        self.logger.info(f"📊 Filtro de data aplicado:")
        self.logger.info(f"   - Comparações: {original_comparisons:,} → {new_comparisons:,}")
        self.logger.info(f"   - Redução: {reduction:.1f}%")
        self.logger.info(f"   - Targets filtrados: {len(target_df)} → {len(target_df_final)}")
        
        return source_df_filtered, target_df_final, valid_pairs

    def get_embeddings_batch(self, texts, batch_size=None):
        """Gera embeddings em lotes otimizados"""
        # Garantir que o modelo está carregado
        self._load_model()
        
        if batch_size is None:
            batch_size = self.config['batch_size']
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                # Verificar se tokenizer está carregado
                if self.tokenizer is None:
                    self.logger.error("Tokenizer não carregado!")
                    continue
                
                # Tokenizar com limite de memória
                encoding = self.tokenizer(
                    batch_texts,
                    truncation=True,
                    padding='max_length',
                    max_length=self.config['max_length'],
                    return_tensors='pt'
                )
                
                encoding = {k: v.to(self.device) for k, v in encoding.items()}
                
                # Gerar embeddings
                import torch
                with torch.no_grad():
                    outputs = self.model(**encoding, output_hidden_states=True)
                    batch_embeddings = outputs.hidden_states[-1][:, 0, :].cpu().numpy()
                    embeddings.append(batch_embeddings)
                
                # Limpeza de memória
                del encoding, outputs
                if hasattr(torch.cuda, 'empty_cache'):
                    torch.cuda.empty_cache()
                    
            except Exception as e:
                self.logger.warning(f"Erro no lote {i//batch_size + 1}: {e}")
                # Continuar com próximo lote
                continue
        
        if embeddings:
            return np.vstack(embeddings)
        else:
            return np.array([])

    def custom_trained_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        VERSÃO OTIMIZADA - Executa matching usando o modelo personalizado treinado
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
            DataFrame com matches e scores de similaridade
        """
        import time
        
        self.logger.info("🚀 Iniciando matching OTIMIZADO com modelo personalizado treinado")
        self.logger.info(f"   - Origem: {len(source_df)} registros")
        self.logger.info(f"   - Destino: {len(target_df)} registros")
        self.logger.info(f"   - Threshold: {self.config['custom_threshold']}")
        
        start_time = time.time()
        
        # 1. Preparar dados
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        # 2. Pré-processar textos
        self.logger.info("📝 Pré-processando textos...")
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # 3. Filtrar textos vazios
        source_df = source_df[source_df['normalized_text'] != ""]
        target_df = target_df[target_df['normalized_text'] != ""]
        
        if source_df.empty or target_df.empty:
            self.logger.warning("⚠️ Nenhum texto válido encontrado após pré-processamento")
            return pd.DataFrame()
        
        # 4. Aplicar filtro de data OTIMIZADO
        source_df_filtered, target_df_filtered, valid_pairs = self.apply_date_filter_optimized(
            source_df, target_df, date_cols
        )
        
        if not valid_pairs:
            self.logger.warning("⚠️ Nenhum par válido encontrado após filtro de data")
            return pd.DataFrame()
        
        # 5. Limitar número de comparações para evitar travamento
        max_comparisons = self.config.get('max_comparisons_per_batch', 20000)
        if len(valid_pairs) > max_comparisons:
            self.logger.warning(f"⚠️ Limitando comparações a {max_comparisons:,} para evitar travamento")
            valid_pairs = valid_pairs[:max_comparisons]
        
        # 6. Gerar embeddings apenas para dados necessários
        self.logger.info(f"🧠 Gerando embeddings para dados filtrados...")
        
        source_texts = source_df_filtered['normalized_text'].tolist()
        target_texts = target_df_filtered['normalized_text'].tolist()
        
        self.logger.info(f"   - Textos origem: {len(source_texts)}")
        self.logger.info(f"   - Textos destino: {len(target_texts)}")
        
        try:
            source_embeddings = self.get_embeddings_batch(source_texts)
            target_embeddings = self.get_embeddings_batch(target_texts)
            
            if source_embeddings.size == 0 or target_embeddings.size == 0:
                self.logger.error("❌ Falha ao gerar embeddings")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar embeddings: {e}")
            return pd.DataFrame()
        
        # 7. Criar mapeamentos de índices
        source_idx_map = {idx: i for i, idx in enumerate(source_df_filtered.index)}
        target_idx_map = {idx: i for i, idx in enumerate(target_df_filtered.index)}
        
        # 8. Processar matches em lotes pequenos
        self.logger.info(f"🔍 Processando {len(valid_pairs):,} comparações em lotes...")
        
        matches = []
        batch_size = 2000  # Lotes menores para evitar travamento
        total_batches = (len(valid_pairs) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(valid_pairs))
            batch_pairs = valid_pairs[start_idx:end_idx]
            
            self.logger.info(f"📦 Lote {batch_idx + 1}/{total_batches} ({len(batch_pairs):,} comparações)")
            
            batch_start_time = time.time()
            
            for source_idx, target_idx in batch_pairs:
                try:
                    if source_idx in source_idx_map and target_idx in target_idx_map:
                        source_emb_idx = source_idx_map[source_idx]
                        target_emb_idx = target_idx_map[target_idx]
                        
                        # Calcular similaridade
                        similarity = cosine_similarity(
                            [source_embeddings[source_emb_idx]], 
                            [target_embeddings[target_emb_idx]]
                        )[0, 0]
                        
                        # Manter match se acima do threshold
                        if similarity >= self.config['custom_threshold']:
                            source_row = source_df_filtered.loc[source_idx]
                            target_row = target_df_filtered.loc[target_idx]
                            
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
                                'algorithm': 'custom_trained_optimized'
                            }
                            
                            # Adicionar coluna de ano se disponível
                            if source_year is not None:
                                match_data['ano_interacao'] = source_year
                            
                            matches.append(match_data)
                            
                except Exception as e:
                    self.logger.warning(f"Erro na comparação: {e}")
                    continue
            
            batch_time = time.time() - batch_start_time
            matches_found = len(matches)
            
            self.logger.info(f"✅ Lote {batch_idx + 1} concluído em {batch_time:.1f}s")
            self.logger.info(f"   - Matches encontrados até agora: {matches_found:,}")
            
            # Salvar resultados parciais a cada 10 lotes
            if matches_found > 0 and (batch_idx % 10 == 0 or batch_idx == total_batches - 1):
                try:
                    partial_df = pd.DataFrame(matches).sort_values('similarity', ascending=False)
                    partial_filename = f"custom_matches_partial_batch_{batch_idx + 1}.xlsx"
                    partial_df.to_excel(partial_filename, index=False)
                    self.logger.info(f"💾 Resultados parciais salvos: {partial_filename}")
                except Exception as e:
                    self.logger.warning(f"Erro ao salvar parciais: {e}")
            
            # Pausa pequena para permitir interrupção
            time.sleep(0.1)
        
        # 9. Criar DataFrame final
        matches_df = pd.DataFrame(matches)
        
        if not matches_df.empty:
            matches_df = matches_df.sort_values('similarity', ascending=False)
        
        total_time = time.time() - start_time
        
        self.logger.info(f"✅ Matching OTIMIZADO concluído em {total_time:.1f}s:")
        self.logger.info(f"   - Comparações realizadas: {len(valid_pairs):,}")
        self.logger.info(f"   - Matches encontrados: {len(matches_df):,}")
        if not matches_df.empty:
            self.logger.info(f"   - Similaridade média: {matches_df['similarity'].mean():.3f}")
            self.logger.info(f"   - Similaridade máxima: {matches_df['similarity'].max():.3f}")
        
        return matches_df

# Função para integrar ao MatchingAlgorithms existente
def add_custom_algorithm_to_existing_class():
    """
    Adiciona o algoritmo personalizado à classe MatchingAlgorithms existente
    """
    return """
# Adicionar ao arquivo matching_algorithms.py

from custom_model_integration import CustomTrainedMatcher

# Modificar a classe MatchingAlgorithms:

class MatchingAlgorithms:
    def __init__(self, config=None):
        # ... código existente ...
        
        # Adicionar configuração do modelo personalizado
        if config and 'custom_trained' in config:
            self.config.update({
                'custom_threshold': config['custom_trained'].get('threshold', 0.75),
                'custom_model_path': config['custom_trained'].get('model_path', 'company_matching_trainer/models/manual_validated_matcher'),
                'custom_batch_size': config['custom_trained'].get('batch_size', 32),
                'custom_max_length': config['custom_trained'].get('max_length', 128)
            })
        
        # Inicializar matcher personalizado
        self.custom_matcher = None
    
    def _load_custom_matcher(self):
        '''Carrega o matcher personalizado sob demanda'''
        if self.custom_matcher is None:
            custom_config = {
                'custom_threshold': self.config.get('custom_threshold', 0.75),
                'model_path': self.config.get('custom_model_path', 'company_matching_trainer/models/manual_validated_matcher'),
                'batch_size': self.config.get('custom_batch_size', 32),
                'max_length': self.config.get('custom_max_length', 128)
            }
            self.custom_matcher = CustomTrainedMatcher(custom_config)
    
    def custom_trained_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        '''
        Matching usando modelo personalizado treinado
        
        Args:
            source_df: DataFrame com dados de origem
            target_df: DataFrame com dados de destino  
            source_col: Coluna para matching na origem
            target_col: Coluna para matching no destino
            date_cols: Tupla com colunas de data para filtro
            
        Returns:
            DataFrame com matches encontrados
        '''
        # Carregar matcher se necessário
        self._load_custom_matcher()
        
        # Configurar threshold
        self.custom_matcher.config['custom_threshold'] = self.config.get('custom_threshold', 0.75)
        
        # Executar matching
        return self.custom_matcher.custom_trained_matching(
            source_df, target_df, source_col, target_col, date_cols
        )
"""

if __name__ == "__main__":
    print("=== Integração do Modelo Personalizado ===")
    print("Este módulo integra o modelo treinado ao sistema GEREM existente")
    
    # Verificar se o modelo existe
    model_path = Path('company_matching_trainer/models/manual_validated_matcher')
    if model_path.exists():
        print("✅ Modelo encontrado!")
        print(f"📁 Caminho: {model_path}")
        
        # Listar arquivos do modelo
        model_files = list(model_path.glob('*'))
        print("📋 Arquivos do modelo:")
        for file in model_files:
            print(f"   - {file.name}")
    else:
        print("⚠️ Modelo não encontrado. Verifique o caminho.")
    
    print("\n" + add_custom_algorithm_to_existing_class())
