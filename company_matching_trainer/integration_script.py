#!/usr/bin/env python3
"""
Script de Integração com Sistema Existente
==========================================

Este script integra o modelo treinado com o sistema GEREM existente,
permitindo usar o modelo personalizado como um novo algoritmo de matching.
"""

import torch
import numpy as np
from transformers import AutoTokenizer
from company_matching_trainer import CompanyMatchingModel
import pandas as pd
import os
from pathlib import Path

class CustomMatchingAlgorithm:
    """
    Algoritmo de matching personalizado usando o modelo treinado
    Pode ser integrado ao sistema GEREM existente
    """
    
    def __init__(self, model_path='models/company_matcher', threshold=0.7):
        """
        Inicializa o algoritmo personalizado
        
        Args:
            model_path: Caminho para o modelo treinado
            threshold: Threshold para considerar um match válido
        """
        self.model_path = model_path
        self.threshold = threshold
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo treinado"""
        try:
            # Carregar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Carregar modelo
            self.model = CompanyMatchingModel()
            
            # Carregar weights
            model_file = os.path.join(self.model_path, 'pytorch_model.bin')
            if os.path.exists(model_file):
                self.model.load_state_dict(torch.load(model_file, map_location=self.device))
            else:
                # Tentar carregar de outro local
                model_file = os.path.join(self.model_path, 'model.safetensors')
                if os.path.exists(model_file):
                    from safetensors.torch import load_file
                    self.model.load_state_dict(load_file(model_file))
                else:
                    raise FileNotFoundError(f"Modelo não encontrado em {self.model_path}")
            
            self.model.to(self.device)
            self.model.eval()
            
            print(f"✅ Modelo carregado de: {self.model_path}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            raise
    
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
    
    def predict_single(self, text_a, text_b):
        """
        Faz predição para um par de textos
        
        Args:
            text_a: Primeiro texto
            text_b: Segundo texto
            
        Returns:
            dict: Resultado da predição
        """
        # Pré-processar textos
        text_a = self.preprocess_text(text_a)
        text_b = self.preprocess_text(text_b)
        
        # Tokenizar
        encoding = self.tokenizer(
            text_a, text_b,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        # Mover para device
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        # Predição
        with torch.no_grad():
            outputs = self.model(**encoding)
            probabilities = torch.softmax(outputs['logits'], dim=-1)
            prediction = torch.argmax(probabilities, dim=-1)
            confidence = torch.max(probabilities, dim=-1)[0]
        
        # Converter similarity baseada na probabilidade de match
        similarity_score = float(probabilities[0][1].item())  # Probabilidade de ser match
        
        return {
            'is_match': bool(prediction.item()),
            'similarity': similarity_score,
            'confidence': float(confidence.item()),
            'probabilities': {
                'no_match': float(probabilities[0][0].item()),
                'match': float(probabilities[0][1].item())
            }
        }
    
    def custom_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        Implementa matching personalizado compatível com o sistema GEREM
        
        Args:
            source_df: DataFrame com dados de origem (ex: GEREM interactions)
            target_df: DataFrame com dados de destino (ex: prospections)
            source_col: Nome da coluna em source_df para matching
            target_col: Nome da coluna em target_df para matching
            date_cols: Tupla (source_date_col, target_date_col) para filtro de data
            
        Returns:
            DataFrame com matches e scores de similaridade
        """
        print(f"🔍 Iniciando matching personalizado...")
        print(f"   - Origem: {len(source_df)} registros")
        print(f"   - Destino: {len(target_df)} registros")
        print(f"   - Threshold: {self.threshold}")
        
        # Preparar dados
        source_df = source_df.copy()
        target_df = target_df.copy()
        
        # Pré-processar textos
        source_df['normalized_text'] = source_df[source_col].apply(self.preprocess_text)
        target_df['normalized_text'] = target_df[target_col].apply(self.preprocess_text)
        
        # Filtrar textos vazios
        source_df = source_df[source_df['normalized_text'] != ""]
        target_df = target_df[target_df['normalized_text'] != ""]
        
        if source_df.empty or target_df.empty:
            print("⚠️ Nenhum texto válido encontrado após pré-processamento")
            return pd.DataFrame()
        
        # Inicializar lista de matches
        matches = []
        total_comparisons = 0
        
        # Para cada registro de origem
        for source_idx, source_row in source_df.iterrows():
            source_text = source_row['normalized_text']
            
            # Filtrar destino por data se especificado
            filtered_target = target_df
            if date_cols and len(date_cols) == 2:
                source_date = pd.to_datetime(source_row[date_cols[0]], errors='coerce')
                if not pd.isna(source_date):
                    mask = pd.to_datetime(target_df[date_cols[1]], errors='coerce') > source_date
                    filtered_target = target_df[mask]
            
            # Para cada registro de destino filtrado
            for target_idx, target_row in filtered_target.iterrows():
                target_text = target_row['normalized_text']
                total_comparisons += 1
                
                # Fazer predição
                result = self.predict_single(source_text, target_text)
                
                # Manter match se acima do threshold
                if result['similarity'] >= self.threshold:
                    matches.append({
                        'source_id': source_idx,
                        'target_id': target_idx,
                        'source_text': source_row[source_col],
                        'target_text': target_row[target_col],
                        'similarity': result['similarity'],
                        'confidence': result['confidence'],
                        'algorithm': 'custom_trained'
                    })
            
            # Log de progresso
            if source_idx % 100 == 0:
                print(f"   - Processado: {source_idx + 1}/{len(source_df)} registros de origem")
        
        # Criar DataFrame com resultados
        matches_df = pd.DataFrame(matches)
        
        if not matches_df.empty:
            matches_df = matches_df.sort_values('similarity', ascending=False)
        
        print(f"✅ Matching concluído:")
        print(f"   - Comparações realizadas: {total_comparisons:,}")
        print(f"   - Matches encontrados: {len(matches_df):,}")
        print(f"   - Similaridade média: {matches_df['similarity'].mean():.3f}" if not matches_df.empty else "   - Similaridade média: N/A")
        
        return matches_df
    
    def batch_predict(self, text_pairs, batch_size=32):
        """
        Faz predições em lote para melhor performance
        
        Args:
            text_pairs: Lista de tuplas (text_a, text_b)
            batch_size: Tamanho do lote
            
        Returns:
            List: Lista com resultados das predições
        """
        results = []
        
        for i in range(0, len(text_pairs), batch_size):
            batch = text_pairs[i:i + batch_size]
            
            # Preparar batch
            texts_a = [self.preprocess_text(pair[0]) for pair in batch]
            texts_b = [self.preprocess_text(pair[1]) for pair in batch]
            
            # Tokenizar batch
            encodings = self.tokenizer(
                texts_a, texts_b,
                truncation=True,
                padding='max_length',
                max_length=128,
                return_tensors='pt'
            )
            
            # Mover para device
            encodings = {k: v.to(self.device) for k, v in encodings.items()}
            
            # Predições
            with torch.no_grad():
                outputs = self.model(**encodings)
                probabilities = torch.softmax(outputs['logits'], dim=-1)
                predictions = torch.argmax(probabilities, dim=-1)
                confidences = torch.max(probabilities, dim=-1)[0]
            
            # Processar resultados do batch
            for j in range(len(batch)):
                similarity_score = float(probabilities[j][1].item())
                
                results.append({
                    'is_match': bool(predictions[j].item()),
                    'similarity': similarity_score,
                    'confidence': float(confidences[j].item()),
                    'probabilities': {
                        'no_match': float(probabilities[j][0].item()),
                        'match': float(probabilities[j][1].item())
                    }
                })
        
        return results

# Função para integrar no sistema existente
def integrate_custom_algorithm():
    """
    Função para integrar o algoritmo personalizado no sistema GEREM existente
    
    Modifica o arquivo matching_algorithms.py para incluir o novo algoritmo
    """
    
    integration_code = '''
# Adicionar ao final do arquivo matching_algorithms.py

from integration_script import CustomMatchingAlgorithm

class MatchingAlgorithms:
    # ... código existente ...
    
    def __init__(self, config=None):
        # ... código existente ...
        
        # Adicionar configuração do algoritmo personalizado
        self.config.update({
            'custom_threshold': 0.7,
            'custom_model_path': 'models/company_matcher'
        })
        
        # Inicializar algoritmo personalizado
        self.custom_algorithm = None
    
    def _load_custom_algorithm(self):
        """Carrega o algoritmo personalizado sob demanda"""
        if self.custom_algorithm is None:
            try:
                self.custom_algorithm = CustomMatchingAlgorithm(
                    model_path=self.config['custom_model_path'],
                    threshold=self.config['custom_threshold']
                )
                print("✅ Algoritmo personalizado carregado com sucesso")
            except Exception as e:
                print(f"❌ Erro ao carregar algoritmo personalizado: {e}")
                raise
    
    def custom_trained_matching(self, source_df, target_df, source_col, target_col, date_cols=None):
        """
        Matching usando modelo personalizado treinado
        
        Args:
            source_df: DataFrame com dados de origem
            target_df: DataFrame com dados de destino
            source_col: Coluna para matching na origem
            target_col: Coluna para matching no destino
            date_cols: Tupla com colunas de data para filtro
            
        Returns:
            DataFrame com matches encontrados
        """
        # Carregar algoritmo se necessário
        self._load_custom_algorithm()
        
        # Configurar threshold
        self.custom_algorithm.threshold = self.config.get('custom_threshold', 0.7)
        
        # Executar matching
        return self.custom_algorithm.custom_matching(
            source_df, target_df, source_col, target_col, date_cols
        )
'''
    
    print("🔧 Código de integração:")
    print(integration_code)
    print("\n📝 Para integrar:")
    print("1. Adicione o código acima ao arquivo matching_algorithms.py")
    print("2. Atualize a configuração para incluir o algoritmo personalizado")
    print("3. Modifique o main.py para executar o algoritmo personalizado")

# Exemplo de uso do algoritmo personalizado
def example_usage():
    """Exemplo de como usar o algoritmo personalizado"""
    
    # Inicializar algoritmo
    custom_algo = CustomMatchingAlgorithm(
        model_path='models/company_matcher',
        threshold=0.7
    )
    
    # Exemplo de predição única
    result = custom_algo.predict_single("BASF", "BASF S.A.")
    print(f"Resultado: {result}")
    
    # Exemplo de matching em DataFrames
    # source_df = pd.DataFrame({'empresa': ['BASF', 'Petrobras']})
    # target_df = pd.DataFrame({'nome': ['BASF S.A.', 'Petróleo Brasileiro']})
    # matches = custom_algo.custom_matching(source_df, target_df, 'empresa', 'nome')
    # print(f"Matches encontrados: {len(matches)}")

if __name__ == "__main__":
    print("=== Script de Integração ===")
    print("Este script integra o modelo treinado com o sistema GEREM existente")
    
    # Verificar se o modelo existe
    model_path = Path('models/company_matcher')
    if model_path.exists():
        print("✅ Modelo encontrado, testando integração...")
        try:
            example_usage()
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    else:
        print("⚠️ Modelo não encontrado. Execute o treinamento primeiro.")
    
    # Mostrar código de integração
    integrate_custom_algorithm()