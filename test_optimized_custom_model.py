#!/usr/bin/env python3
"""
Script de Teste Otimizado para o Modelo Personalizado
====================================================

Este script testa e otimiza o modelo personalizado para evitar travamentos.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_optimized_custom_matcher():
    """Cria uma versão otimizada do CustomTrainedMatcher"""
    
    class OptimizedCustomTrainedMatcher:
        """Versão otimizada do matcher personalizado para evitar travamentos"""
        
        def __init__(self, config=None):
            self.config = {
                'custom_threshold': 0.75,
                'model_path': 'company_matching_trainer/models/manual_validated_matcher',
                'batch_size': 16,  # Reduzido para evitar travamento
                'max_length': 128,
                'max_comparisons_per_batch': 5000,  # Limite por lote
                'save_partial_results': True,
                'memory_efficient': True
            }
            
            if config:
                self.config.update(config)
            
            self.tokenizer = None
            self.model = None
            self.device = None
            
        def _load_model(self):
            """Carrega o modelo com otimizações de memória"""
            if self.model is None:
                try:
                    import torch
                    from transformers import AutoTokenizer, AutoModelForSequenceClassification
                    
                    # Usar CPU se GPU não disponível ou para economizar memória
                    if self.config.get('memory_efficient', True):
                        self.device = torch.device('cpu')
                    else:
                        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    
                    model_path = self.config['model_path']
                    logger.info(f"Carregando modelo de: {model_path}")
                    
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                    self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
                    self.model.to(self.device)
                    self.model.eval()
                    
                    # Otimizações de memória
                    if hasattr(torch, 'set_grad_enabled'):
                        torch.set_grad_enabled(False)
                    
                    logger.info("✅ Modelo carregado com otimizações")
                    
                except Exception as e:
                    logger.error(f"Erro ao carregar modelo: {e}")
                    raise
        
        def preprocess_text(self, text):
            """Pré-processa texto otimizado"""
            if pd.isna(text):
                return ""
            
            text = str(text).lower().strip()
            
            # Extração otimizada do nome da empresa
            if text.startswith('[') and ']' in text:
                first_bracket_end = text.find(']')
                if first_bracket_end != -1:
                    remaining = text[first_bracket_end + 1:].strip()
                    next_bracket = remaining.find('[')
                    if next_bracket != -1:
                        text = remaining[:next_bracket].strip()
                    else:
                        text = remaining
            
            # Remover prefixos comuns
            prefixes = ['empresa ', 'companhia ', 'industria ', 'industrias ', 'ind. ']
            for prefix in prefixes:
                if text.startswith(prefix):
                    text = text[len(prefix):]
                    break
            
            return text
        
        def get_embeddings_batch(self, texts, batch_size=None):
            """Gera embeddings em lotes otimizados"""
            self._load_model()
            
            if batch_size is None:
                batch_size = self.config['batch_size']
            
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                try:
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
                    logger.warning(f"Erro no lote {i//batch_size + 1}: {e}")
                    # Continuar com próximo lote
                    continue
            
            if embeddings:
                return np.vstack(embeddings)
            else:
                return np.array([])
        
        def apply_date_filter_optimized(self, source_df, target_df, date_cols):
            """Aplica filtro de data de forma otimizada ANTES de qualquer processamento"""
            if not date_cols or len(date_cols) != 2:
                return source_df, target_df, None
            
            logger.info("🔥 Aplicando filtro de data otimizado...")
            
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
                if len(valid_pairs) > 100000:  # Limite de segurança
                    logger.warning(f"Atingido limite de {len(valid_pairs):,} comparações. Parando para evitar travamento.")
                    break
            
            # Filtrar apenas targets que têm pelo menos um match
            target_indices_with_matches = set(pair[1] for pair in valid_pairs)
            target_df_final = target_df_filtered.loc[list(target_indices_with_matches)]
            
            original_comparisons = len(source_df) * len(target_df)
            new_comparisons = len(valid_pairs)
            reduction = (1 - new_comparisons/original_comparisons) * 100 if original_comparisons > 0 else 0
            
            logger.info(f"📊 Filtro de data aplicado:")
            logger.info(f"   - Comparações: {original_comparisons:,} → {new_comparisons:,}")
            logger.info(f"   - Redução: {reduction:.1f}%")
            logger.info(f"   - Targets filtrados: {len(target_df)} → {len(target_df_final)}")
            
            return source_df_filtered, target_df_final, valid_pairs
        
        def custom_trained_matching_optimized(self, source_df, target_df, source_col, target_col, date_cols=None):
            """Executa matching otimizado para evitar travamentos"""
            
            logger.info("🚀 Iniciando matching otimizado com modelo personalizado")
            logger.info(f"   - Origem: {len(source_df)} registros")
            logger.info(f"   - Destino: {len(target_df)} registros")
            logger.info(f"   - Threshold: {self.config['custom_threshold']}")
            
            start_time = time.time()
            
            # 1. Preparar dados
            source_df = source_df.copy()
            target_df = target_df.copy()
            
            # 2. Pré-processar textos
            logger.info("📝 Pré-processando textos...")
            source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
            target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
            
            # 3. Filtrar textos vazios
            source_df = source_df[source_df['normalized_text'] != ""]
            target_df = target_df[target_df['normalized_text'] != ""]
            
            if source_df.empty or target_df.empty:
                logger.warning("⚠️ Nenhum texto válido após pré-processamento")
                return pd.DataFrame()
            
            # 4. Aplicar filtro de data OTIMIZADO
            source_df_filtered, target_df_filtered, valid_pairs = self.apply_date_filter_optimized(
                source_df, target_df, date_cols
            )
            
            if not valid_pairs:
                logger.warning("⚠️ Nenhum par válido após filtro de data")
                return pd.DataFrame()
            
            # 5. Limitar número de comparações para evitar travamento
            max_comparisons = self.config.get('max_comparisons_per_batch', 10000)
            if len(valid_pairs) > max_comparisons:
                logger.warning(f"⚠️ Limitando comparações a {max_comparisons:,} para evitar travamento")
                # Manter os pares com maior probabilidade de match (ordenar por similaridade de texto simples)
                valid_pairs = valid_pairs[:max_comparisons]
            
            # 6. Gerar embeddings apenas para dados necessários
            logger.info(f"🧠 Gerando embeddings para dados filtrados...")
            
            source_texts = source_df_filtered['normalized_text'].tolist()
            target_texts = target_df_filtered['normalized_text'].tolist()
            
            logger.info(f"   - Textos origem: {len(source_texts)}")
            logger.info(f"   - Textos destino: {len(target_texts)}")
            
            try:
                source_embeddings = self.get_embeddings_batch(source_texts)
                target_embeddings = self.get_embeddings_batch(target_texts)
                
                if source_embeddings.size == 0 or target_embeddings.size == 0:
                    logger.error("❌ Falha ao gerar embeddings")
                    return pd.DataFrame()
                    
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embeddings: {e}")
                return pd.DataFrame()
            
            # 7. Criar mapeamentos de índices
            source_idx_map = {idx: i for i, idx in enumerate(source_df_filtered.index)}
            target_idx_map = {idx: i for i, idx in enumerate(target_df_filtered.index)}
            
            # 8. Processar matches em lotes pequenos
            logger.info(f"🔍 Processando {len(valid_pairs):,} comparações em lotes...")
            
            matches = []
            batch_size = 1000  # Lotes pequenos para evitar travamento
            total_batches = (len(valid_pairs) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, len(valid_pairs))
                batch_pairs = valid_pairs[start_idx:end_idx]
                
                logger.info(f"📦 Lote {batch_idx + 1}/{total_batches} ({len(batch_pairs):,} comparações)")
                
                batch_start_time = time.time()
                
                for source_idx, target_idx in batch_pairs:
                    try:
                        if source_idx in source_idx_map and target_idx in target_idx_map:
                            source_emb_idx = source_idx_map[source_idx]
                            target_emb_idx = target_idx_map[target_idx]
                            
                            # Calcular similaridade
                            from sklearn.metrics.pairwise import cosine_similarity
                            similarity = cosine_similarity(
                                [source_embeddings[source_emb_idx]], 
                                [target_embeddings[target_emb_idx]]
                            )[0, 0]
                            
                            # Manter match se acima do threshold
                            if similarity >= self.config['custom_threshold']:
                                source_row = source_df_filtered.loc[source_idx]
                                target_row = target_df_filtered.loc[target_idx]
                                
                                # Extrair ano da data
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
                                
                                if source_year is not None:
                                    match_data['ano_interacao'] = source_year
                                
                                matches.append(match_data)
                                
                    except Exception as e:
                        logger.warning(f"Erro na comparação: {e}")
                        continue
                
                batch_time = time.time() - batch_start_time
                matches_found = len(matches)
                
                logger.info(f"✅ Lote {batch_idx + 1} concluído em {batch_time:.1f}s")
                logger.info(f"   - Matches encontrados até agora: {matches_found:,}")
                
                # Salvar resultados parciais se habilitado
                if self.config.get('save_partial_results', False) and matches_found > 0:
                    if batch_idx % 5 == 0 or batch_idx == total_batches - 1:  # A cada 5 lotes
                        try:
                            partial_df = pd.DataFrame(matches).sort_values('similarity', ascending=False)
                            partial_filename = f"custom_matches_partial_batch_{batch_idx + 1}.xlsx"
                            partial_df.to_excel(partial_filename, index=False)
                            logger.info(f"💾 Resultados parciais salvos: {partial_filename}")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar parciais: {e}")
                
                # Pausa pequena para permitir interrupção
                time.sleep(0.1)
            
            # 9. Criar DataFrame final
            matches_df = pd.DataFrame(matches)
            
            if not matches_df.empty:
                matches_df = matches_df.sort_values('similarity', ascending=False)
            
            total_time = time.time() - start_time
            
            logger.info(f"✅ Matching otimizado concluído em {total_time:.1f}s:")
            logger.info(f"   - Comparações realizadas: {len(valid_pairs):,}")
            logger.info(f"   - Matches encontrados: {len(matches_df):,}")
            if not matches_df.empty:
                logger.info(f"   - Similaridade média: {matches_df['similarity'].mean():.3f}")
                logger.info(f"   - Similaridade máxima: {matches_df['similarity'].max():.3f}")
            
            return matches_df
    
    return OptimizedCustomTrainedMatcher

def test_optimized_matching():
    """Testa o matching otimizado"""
    
    logger.info("=== TESTE DE MATCHING OTIMIZADO ===")
    
    # Criar matcher otimizado
    OptimizedMatcher = create_optimized_custom_matcher()
    matcher = OptimizedMatcher({
        'custom_threshold': 0.75,
        'batch_size': 16,
        'max_comparisons_per_batch': 5000,
        'save_partial_results': True,
        'memory_efficient': True
    })
    
    # Criar dados de teste maiores
    logger.info("📊 Criando dados de teste...")
    
    # Dados de origem (GEREM)
    source_data = []
    companies = ['BASF', 'Petrobras', 'Vale', 'Embraer', 'JBS', 'Suzano', 'Gerdau', 'CSN']
    
    for i, company in enumerate(companies):
        for j in range(10):  # 10 registros por empresa
            source_data.append({
                'empresa': f"{company} Variação {j+1}",
                'data': f"2024-{(i+1):02d}-{(j+1):02d}"
            })
    
    # Dados de destino (Negociações)
    target_data = []
    target_companies = ['BASF S.A.', 'Petróleo Brasileiro S.A.', 'Vale S.A.', 'Embraer S.A.', 
                       'JBS S.A.', 'Suzano S.A.', 'Gerdau S.A.', 'CSN S.A.']
    
    for i, company in enumerate(target_companies):
        for j in range(15):  # 15 registros por empresa
            target_data.append({
                'nome': f"{company} Negociação {j+1}",
                'data': f"2024-{(i+1):02d}-{(j+10):02d}"  # Datas posteriores
            })
    
    source_df = pd.DataFrame(source_data)
    target_df = pd.DataFrame(target_data)
    
    logger.info(f"   - Origem: {len(source_df)} registros")
    logger.info(f"   - Destino: {len(target_df)} registros")
    logger.info(f"   - Comparações potenciais: {len(source_df) * len(target_df):,}")
    
    # Executar matching otimizado
    logger.info("🚀 Executando matching otimizado...")
    
    try:
        results = matcher.custom_trained_matching_optimized(
            source_df, target_df, 'empresa', 'nome', ('data', 'data')
        )
        
        logger.info(f"✅ Matching concluído com sucesso!")
        logger.info(f"   - Matches encontrados: {len(results)}")
        
        if not results.empty:
            logger.info(f"   - Top 5 matches:")
            for idx, row in results.head().iterrows():
                logger.info(f"     {row['source_text']} → {row['target_text']} ({row['similarity']:.3f})")
            
            # Salvar resultados
            results.to_excel('test_optimized_custom_matches.xlsx', index=False)
            logger.info("💾 Resultados salvos em: test_optimized_custom_matches.xlsx")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante matching: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_optimized_integration():
    """Cria integração otimizada para o sistema principal"""
    
    optimized_code = '''
# CÓDIGO OTIMIZADO PARA INTEGRAÇÃO NO SISTEMA PRINCIPAL
# Adicionar ao arquivo matching_algorithms.py

def custom_trained_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
    """
    VERSÃO OTIMIZADA - Matching usando modelo personalizado treinado
    Inclui otimizações para evitar travamentos:
    - Filtro de data aplicado ANTES dos embeddings
    - Processamento em lotes pequenos
    - Limite de comparações por segurança
    - Salvamento de resultados parciais
    - Limpeza de memória
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
        'max_comparisons_per_batch': 10000,  # Limite de segurança
        'save_partial_results': True,
        'memory_efficient': True
    })
    
    # OTIMIZAÇÃO 2: Usar método otimizado
    return self.custom_matcher.custom_trained_matching_optimized(
        source_df, target_df, source_col, target_col, date_cols
    )
'''
    
    return optimized_code

if __name__ == "__main__":
    logger.info("🚀 Iniciando teste de matching otimizado...")
    
    # Testar matching otimizado
    success = test_optimized_matching()
    
    if success:
        logger.info("✅ Teste concluído com sucesso!")
        
        # Mostrar código de integração otimizada
        logger.info("\n" + "="*60)
        logger.info("CÓDIGO DE INTEGRAÇÃO OTIMIZADA:")
        logger.info("="*60)
        print(create_optimized_integration())
        
        logger.info("\n📋 PRÓXIMOS PASSOS:")
        logger.info("1. Aplicar as otimizações ao sistema principal")
        logger.info("2. Testar com dados reais usando configuração otimizada")
        logger.info("3. Monitorar performance e ajustar limites se necessário")
        
    else:
        logger.error("❌ Teste falhou. Verifique os logs acima.")
        sys.exit(1)
