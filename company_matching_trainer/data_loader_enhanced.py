#!/usr/bin/env python3
"""
Enhanced Data Loader for Company Matching Trainer
================================================

Carrega automaticamente os dados de embedding mais recentes dos resultados do GEREM.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import json
import yaml
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class GeremDataLoader:
    """Carregador de dados otimizado para os resultados do GEREM"""
    
    def __init__(self, results_base_path: str = "results", config_path: str = "config.yaml"):
        self.results_base_path = Path(results_base_path)
        self.data_sources = ['gerem_negociacoes', 'gerem_projetos', 'gerem_prospecoes']
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuração do arquivo YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuração carregada de: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Erro ao carregar configuração: {e}. Usando configuração padrão.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão caso não seja possível carregar do arquivo"""
        return {
            'data': {
                'auto_labeling': {
                    'high_similarity_threshold': 0.95,
                    'medium_similarity_threshold': 0.85,
                    'low_similarity_threshold': 0.5,
                    'sample_high_similarity': True,
                    'sample_rate': 0.15,
                    'suspicious_patterns': {
                        'enabled': True,
                        'patterns': [
                            "LTDA.*S\\.A\\.",
                            "BRASIL.*CORPORATION",
                            "DISTRIBUIDORA.*S\\.A\\.",
                            "NORTE.*SUL",
                            "\\d+.*\\d+",
                            "FILIAL.*MATRIZ"
                        ]
                    },
                    'always_validate_companies': [
                        "MICROSOFT", "GOOGLE", "AMAZON", "PETROBRAS", 
                        "VALE", "BASF", "VOLKSWAGEN", "GENERAL MOTORS", "FORD", "TOYOTA"
                    ]
                }
            }
        }
    
    def _detect_suspicious_patterns(self, source_text: str, target_text: str) -> bool:
        """Detecta padrões suspeitos que indicam possíveis falsos positivos"""
        if not self.config.get('data', {}).get('auto_labeling', {}).get('suspicious_patterns', {}).get('enabled', False):
            return False
        
        patterns = self.config['data']['auto_labeling']['suspicious_patterns'].get('patterns', [])
        combined_text = f"{source_text} {target_text}".upper()
        
        for pattern in patterns:
            if re.search(pattern, combined_text):
                return True
        
        return False
    
    def _is_always_validate_company(self, source_text: str, target_text: str) -> bool:
        """Verifica se contém empresas que sempre precisam validação manual"""
        always_validate = self.config.get('data', {}).get('auto_labeling', {}).get('always_validate_companies', [])
        combined_text = f"{source_text} {target_text}".upper()
        
        for company in always_validate:
            if company.upper() in combined_text:
                return True
        
        return False
    
    def _sample_high_similarity_cases(self, df: pd.DataFrame, high_threshold: float) -> pd.DataFrame:
        """Amostra casos de alta similaridade para validação manual"""
        config = self.config.get('data', {}).get('auto_labeling', {})
        
        if not config.get('sample_high_similarity', False):
            return df
        
        sample_rate = config.get('sample_rate', 0.15)
        
        # Identificar casos de alta similaridade
        high_sim_cases = df[df['similarity'] >= high_threshold].copy()
        
        if high_sim_cases.empty:
            return df
        
        # Calcular tamanho da amostra
        sample_size = max(1, int(len(high_sim_cases) * sample_rate))
        
        # Amostrar casos para validação manual
        sampled_indices = high_sim_cases.sample(n=sample_size, random_state=42).index
        
        # Marcar casos amostrados para validação manual
        df.loc[sampled_indices, 'label'] = -1
        df.loc[sampled_indices, 'confidence'] = 'high_similarity_sample'
        df.loc[sampled_indices, 'reason'] = 'Amostra de alta similaridade para validação'
        
        logger.info(f"🎯 Amostrados {len(sampled_indices)} casos de alta similaridade para validação manual")
        
        return df
        
    def find_latest_results(self) -> Dict[str, str]:
        """Encontra os diretórios com os resultados mais recentes para cada fonte"""
        latest_results = {}
        
        for source in self.data_sources:
            source_path = self.results_base_path / source
            if not source_path.exists():
                logger.warning(f"Diretório não encontrado: {source_path}")
                continue
                
            # Listar diretórios com timestamp
            timestamp_dirs = [d for d in source_path.iterdir() 
                            if d.is_dir() and d.name.replace('_', '').replace('.DS_Store', '').isdigit()]
            
            if not timestamp_dirs:
                logger.warning(f"Nenhum diretório de resultados encontrado em: {source_path}")
                continue
                
            # Ordenar por timestamp (mais recente primeiro)
            latest_dir = max(timestamp_dirs, key=lambda x: x.name)
            latest_results[source] = str(latest_dir)
            
            logger.info(f"Dados mais recentes para {source}: {latest_dir.name}")
            
        return latest_results
    
    def load_embedding_data(self, source_path: str) -> Optional[pd.DataFrame]:
        """Carrega dados de embedding de um diretório específico"""
        embedding_file = Path(source_path) / "embedding_matches.xlsx"
        
        if not embedding_file.exists():
            logger.warning(f"Arquivo de embedding não encontrado: {embedding_file}")
            return None
            
        try:
            df = pd.read_excel(embedding_file)
            logger.info(f"Carregados {len(df)} registros de embedding de {embedding_file}")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar {embedding_file}: {e}")
            return None
    
    def standardize_embedding_data(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """Padroniza os dados de embedding para o formato esperado pelo trainer"""
        
        # Mapear colunas baseado no tipo de fonte
        column_mapping = {
            'gerem_negociacoes': {
                'source_text': 'gerem_empresa',
                'target_text': 'negociacoes_empresa', 
                'similarity': 'embedding_similarity'
            },
            'gerem_projetos': {
                'source_text': 'gerem_empresa',
                'target_text': 'projetos_empresa',
                'similarity': 'embedding_similarity'
            },
            'gerem_prospecoes': {
                'source_text': 'gerem_empresa', 
                'target_text': 'prospecoes_empresa',
                'similarity': 'embedding_similarity'
            }
        }
        
        mapping = column_mapping.get(source_type, {})
        
        # Verificar se as colunas existem
        available_cols = df.columns.tolist()
        logger.info(f"Colunas disponíveis em {source_type}: {available_cols}")
        
        # Tentar diferentes variações de nomes de colunas
        possible_source_cols = ['source_text', 'gerem_empresa', 'source_empresa', 'empresa_gerem', 'nome_empresa_gerem']
        possible_target_cols = ['target_text', f'{source_type.split("_")[1]}_empresa', 'target_empresa', 'empresa_target']
        possible_similarity_cols = ['similarity', 'embedding_similarity', 'score', 'embedding_score']
        
        source_col = None
        target_col = None
        similarity_col = None
        
        # Encontrar colunas corretas
        for col in possible_source_cols:
            if col in available_cols:
                source_col = col
                break
                
        for col in possible_target_cols:
            if col in available_cols:
                target_col = col
                break
                
        for col in possible_similarity_cols:
            if col in available_cols:
                similarity_col = col
                break
        
        if not all([source_col, target_col, similarity_col]):
            logger.error(f"Não foi possível encontrar todas as colunas necessárias em {source_type}")
            logger.error(f"Source: {source_col}, Target: {target_col}, Similarity: {similarity_col}")
            return pd.DataFrame()
        
        # Criar DataFrame padronizado
        standardized_df = pd.DataFrame({
            'source_text': df[source_col].astype(str),
            'target_text': df[target_col].astype(str), 
            'similarity': pd.to_numeric(df[similarity_col], errors='coerce'),
            'source_type': source_type,
            'original_index': df.index
        })
        
        # Remover linhas com valores nulos
        initial_len = len(standardized_df)
        standardized_df = standardized_df.dropna(subset=['source_text', 'target_text', 'similarity'])
        final_len = len(standardized_df)
        
        if initial_len != final_len:
            logger.warning(f"Removidas {initial_len - final_len} linhas com valores nulos de {source_type}")
        
        logger.info(f"Dados padronizados para {source_type}: {len(standardized_df)} registros")
        
        return standardized_df
    
    def load_all_latest_data(self) -> pd.DataFrame:
        """Carrega e combina todos os dados de embedding mais recentes"""
        latest_results = self.find_latest_results()
        
        if not latest_results:
            raise ValueError("Nenhum resultado encontrado nos diretórios de dados!")
        
        all_data = []
        
        for source_type, source_path in latest_results.items():
            logger.info(f"Processando dados de {source_type}...")
            
            # Carregar dados de embedding
            df = self.load_embedding_data(source_path)
            if df is None or df.empty:
                logger.warning(f"Pulando {source_type} - dados não disponíveis")
                continue
            
            # Padronizar dados
            standardized_df = self.standardize_embedding_data(df, source_type)
            if not standardized_df.empty:
                all_data.append(standardized_df)
        
        if not all_data:
            raise ValueError("Nenhum dado válido foi carregado!")
        
        # Combinar todos os dados
        combined_df = pd.concat(all_data, ignore_index=True)
        
        logger.info(f"Total de registros combinados: {len(combined_df)}")
        logger.info(f"Distribuição por fonte:")
        for source in combined_df['source_type'].value_counts().items():
            logger.info(f"  {source[0]}: {source[1]} registros")
        
        return combined_df
    
    def create_training_labels_optimized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria labels automáticos com lógica otimizada para capturar falsos positivos de alta similaridade
        """
        df = df.copy()
        
        # Carregar thresholds da configuração
        config = self.config.get('data', {}).get('auto_labeling', {})
        high_threshold = config.get('high_similarity_threshold', 0.95)
        medium_threshold = config.get('medium_similarity_threshold', 0.85)
        low_threshold = config.get('low_similarity_threshold', 0.5)
        
        logger.info("🎯 Aplicando estratégia otimizada de rotulação:")
        logger.info(f"   - Alta similaridade (>{high_threshold}): Automático correto")
        logger.info(f"   - Faixa crítica ({medium_threshold}-{high_threshold}): VALIDAÇÃO OBRIGATÓRIA")
        logger.info(f"   - Baixa similaridade (<{low_threshold}): Automático incorreto")
        
        # Inicializar colunas
        df['label'] = -1  # Padrão: precisa revisão
        df['confidence'] = 'needs_review'
        df['reason'] = 'Faixa de similaridade média'
        df['priority'] = 2  # Prioridade padrão
        
        # 1. CASOS DE BAIXA SIMILARIDADE - Automático incorreto
        low_sim_mask = df['similarity'] <= low_threshold
        df.loc[low_sim_mask, 'label'] = 0
        df.loc[low_sim_mask, 'confidence'] = 'high'
        df.loc[low_sim_mask, 'reason'] = f'Baixa similaridade (<={low_threshold})'
        df.loc[low_sim_mask, 'priority'] = 3
        
        # 2. CASOS DE ALTA SIMILARIDADE - Inicialmente automático correto
        high_sim_mask = df['similarity'] >= high_threshold
        df.loc[high_sim_mask, 'label'] = 1
        df.loc[high_sim_mask, 'confidence'] = 'high'
        df.loc[high_sim_mask, 'reason'] = f'Alta similaridade (>={high_threshold})'
        df.loc[high_sim_mask, 'priority'] = 3
        
        # 3. FAIXA CRÍTICA - Sempre validação manual
        critical_mask = (df['similarity'] >= medium_threshold) & (df['similarity'] < high_threshold)
        df.loc[critical_mask, 'label'] = -1
        df.loc[critical_mask, 'confidence'] = 'critical_review'
        df.loc[critical_mask, 'reason'] = f'Faixa crítica ({medium_threshold}-{high_threshold})'
        df.loc[critical_mask, 'priority'] = 1  # MÁXIMA PRIORIDADE
        
        # 4. DETECTAR PADRÕES SUSPEITOS (força validação manual)
        suspicious_count = 0
        for idx, row in df.iterrows():
            if self._detect_suspicious_patterns(row['source_text'], row['target_text']):
                df.loc[idx, 'label'] = -1
                df.loc[idx, 'confidence'] = 'suspicious_pattern'
                df.loc[idx, 'reason'] = 'Padrão suspeito detectado'
                df.loc[idx, 'priority'] = 1
                suspicious_count += 1
        
        # 5. EMPRESAS QUE SEMPRE PRECISAM VALIDAÇÃO
        always_validate_count = 0
        for idx, row in df.iterrows():
            if self._is_always_validate_company(row['source_text'], row['target_text']):
                df.loc[idx, 'label'] = -1
                df.loc[idx, 'confidence'] = 'important_company'
                df.loc[idx, 'reason'] = 'Empresa importante - validação obrigatória'
                df.loc[idx, 'priority'] = 1
                always_validate_count += 1
        
        # 6. AMOSTRAGEM DE CASOS DE ALTA SIMILARIDADE
        df = self._sample_high_similarity_cases(df, high_threshold)
        
        # Estatísticas detalhadas
        label_counts = df['label'].value_counts()
        confidence_counts = df['confidence'].value_counts()
        priority_counts = df['priority'].value_counts()
        
        logger.info("\n📊 Estatísticas de rotulação otimizada:")
        logger.info(f"   ✅ Matches corretos automáticos (label=1): {label_counts.get(1, 0)}")
        logger.info(f"   ❌ Matches incorretos automáticos (label=0): {label_counts.get(0, 0)}")
        logger.info(f"   🔍 Precisam validação manual (label=-1): {label_counts.get(-1, 0)}")
        
        logger.info(f"\n🎯 Detecções especiais:")
        logger.info(f"   🚨 Padrões suspeitos: {suspicious_count}")
        logger.info(f"   🏢 Empresas importantes: {always_validate_count}")
        logger.info(f"   📈 Faixa crítica: {sum(critical_mask)}")
        
        logger.info(f"\n⚡ Prioridades de validação:")
        logger.info(f"   🔥 Prioridade 1 (crítica): {priority_counts.get(1, 0)}")
        logger.info(f"   📋 Prioridade 2 (normal): {priority_counts.get(2, 0)}")
        logger.info(f"   📝 Prioridade 3 (baixa): {priority_counts.get(3, 0)}")
        
        return df
    
    def create_training_labels(self, df: pd.DataFrame, 
                             high_threshold: float = None,
                             low_threshold: float = None) -> pd.DataFrame:
        """
        Método principal para criar labels - usa a versão otimizada
        Mantém compatibilidade com código existente
        """
        if high_threshold is not None or low_threshold is not None:
            logger.warning("⚠️ Thresholds manuais ignorados - usando configuração otimizada do config.yaml")
        
        return self.create_training_labels_optimized(df)
    
    def save_training_data(self, df: pd.DataFrame, output_path: str = "data/training_data.csv"):
        """Salva os dados preparados para treinamento"""
        
        # Criar diretório se não existir
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar dados
        df.to_csv(output_path, index=False)
        logger.info(f"Dados de treinamento salvos em: {output_path}")
        
        # Salvar também dados que precisam de revisão
        needs_review = df[df['label'] == -1]
        if not needs_review.empty:
            review_path = output_path.replace('.csv', '_needs_review.csv')
            needs_review.to_csv(review_path, index=False)
            logger.info(f"Dados para revisão salvos em: {review_path}")
        
        return output_path

def main():
    """Função principal para testar o carregador de dados"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Inicializar carregador
        loader = GeremDataLoader()
        
        # Carregar todos os dados mais recentes
        logger.info("=== Carregando dados de embedding mais recentes ===")
        combined_data = loader.load_all_latest_data()
        
        # Criar labels automáticos
        logger.info("=== Criando labels de treinamento ===")
        training_data = loader.create_training_labels(combined_data)
        
        # Salvar dados preparados
        logger.info("=== Salvando dados preparados ===")
        output_path = loader.save_training_data(training_data)
        
        logger.info(f"✅ Processo concluído! Dados salvos em: {output_path}")
        
        # Mostrar estatísticas finais
        logger.info("\n=== Estatísticas Finais ===")
        logger.info(f"Total de registros: {len(training_data)}")
        logger.info(f"Similaridade média: {training_data['similarity'].mean():.3f}")
        logger.info(f"Similaridade mínima: {training_data['similarity'].min():.3f}")
        logger.info(f"Similaridade máxima: {training_data['similarity'].max():.3f}")
        
    except Exception as e:
        logger.error(f"Erro durante o processamento: {e}")
        raise

if __name__ == "__main__":
    main()
