#!/usr/bin/env python3
"""
Análise de Matches para Identificação de Padrões
===============================================

Analisa os dados de matching para identificar padrões de falsos positivos
e ajudar na validação manual.
"""

import sys
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from collections import Counter
import re

# Adicionar o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

from data_loader_enhanced import GeremDataLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MatchAnalyzer:
    """Analisador de padrões em matches"""
    
    def __init__(self):
        self.data_loader = GeremDataLoader(results_base_path="../results")
        
    def load_and_analyze(self):
        """Carrega dados e executa análises"""
        
        logger.info("Carregando dados para análise...")
        data = self.data_loader.load_all_latest_data()
        
        logger.info(f"Total de registros: {len(data):,}")
        
        # Análises básicas
        self.basic_statistics(data)
        self.similarity_distribution(data)
        self.identify_potential_false_positives(data)
        self.analyze_company_patterns(data)
        self.suggest_validation_priorities(data)
        
        return data
    
    def basic_statistics(self, data):
        """Estatísticas básicas dos dados"""
        
        logger.info("\n=== ESTATÍSTICAS BÁSICAS ===")
        logger.info(f"Total de registros: {len(data):,}")
        
        # Por fonte
        logger.info("\nDistribuição por fonte:")
        for source, count in data['source_type'].value_counts().items():
            logger.info(f"  {source}: {count:,} ({count/len(data)*100:.1f}%)")
        
        # Similaridade
        logger.info(f"\nSimilaridade:")
        logger.info(f"  Média: {data['similarity'].mean():.3f}")
        logger.info(f"  Mediana: {data['similarity'].median():.3f}")
        logger.info(f"  Desvio padrão: {data['similarity'].std():.3f}")
        logger.info(f"  Mínima: {data['similarity'].min():.3f}")
        logger.info(f"  Máxima: {data['similarity'].max():.3f}")
    
    def similarity_distribution(self, data):
        """Análise da distribuição de similaridade"""
        
        logger.info("\n=== DISTRIBUIÇÃO DE SIMILARIDADE ===")
        
        # Faixas de similaridade
        bins = [0.0, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0]
        labels = ['0.0-0.65', '0.65-0.70', '0.70-0.75', '0.75-0.80', 
                 '0.80-0.85', '0.85-0.90', '0.90-0.95', '0.95-1.0']
        
        data['similarity_range'] = pd.cut(data['similarity'], bins=bins, labels=labels, include_lowest=True)
        
        logger.info("Distribuição por faixas de similaridade:")
        for range_label, count in data['similarity_range'].value_counts().sort_index().items():
            percentage = count / len(data) * 100
            logger.info(f"  {range_label}: {count:,} ({percentage:.1f}%)")
    
    def identify_potential_false_positives(self, data):
        """Identifica potenciais falsos positivos"""
        
        logger.info("\n=== POTENCIAIS FALSOS POSITIVOS ===")
        
        # Casos suspeitos: alta similaridade mas empresas muito diferentes
        suspicious_cases = []
        
        # Analisar casos com alta similaridade
        high_sim = data[data['similarity'] > 0.85].copy()
        
        for idx, row in high_sim.iterrows():
            source = str(row['source_text']).lower().strip()
            target = str(row['target_text']).lower().strip()
            
            # Padrões suspeitos
            suspicious_patterns = [
                # Nomes muito diferentes em tamanho
                abs(len(source) - len(target)) > 20,
                
                # Um é sigla e outro nome completo muito diferente
                (len(source) <= 10 and len(target) > 30) or (len(target) <= 10 and len(source) > 30),
                
                # Contém palavras muito diferentes
                self.has_conflicting_keywords(source, target),
                
                # Números muito diferentes
                self.has_conflicting_numbers(source, target)
            ]
            
            if any(suspicious_patterns):
                suspicious_cases.append({
                    'source_text': row['source_text'],
                    'target_text': row['target_text'],
                    'similarity': row['similarity'],
                    'source_type': row['source_type']
                })
        
        logger.info(f"Casos suspeitos identificados: {len(suspicious_cases)}")
        
        if suspicious_cases:
            logger.info("\nExemplos de casos suspeitos:")
            for i, case in enumerate(suspicious_cases[:5]):
                logger.info(f"  {i+1}. Similaridade: {case['similarity']:.3f}")
                logger.info(f"     A: {case['source_text']}")
                logger.info(f"     B: {case['target_text']}")
                logger.info(f"     Fonte: {case['source_type']}")
                logger.info("")
        
        return suspicious_cases
    
    def has_conflicting_keywords(self, text1, text2):
        """Verifica se há palavras-chave conflitantes"""
        
        # Palavras que indicam setores/tipos diferentes
        conflicting_keywords = [
            ['petrobras', 'vale'], ['microsoft', 'apple'], ['banco', 'mineração'],
            ['energia', 'tecnologia'], ['saúde', 'educação'], ['construção', 'alimentação']
        ]
        
        for keywords in conflicting_keywords:
            has_first = any(kw in text1 for kw in keywords)
            has_second = any(kw in text2 for kw in keywords)
            
            if has_first and has_second:
                # Verificar se são palavras diferentes do mesmo grupo
                words1 = [kw for kw in keywords if kw in text1]
                words2 = [kw for kw in keywords if kw in text2]
                if set(words1) != set(words2):
                    return True
        
        return False
    
    def has_conflicting_numbers(self, text1, text2):
        """Verifica se há números conflitantes (CNPJ, códigos, etc.)"""
        
        # Extrair números
        numbers1 = re.findall(r'\d{4,}', text1)  # Números com 4+ dígitos
        numbers2 = re.findall(r'\d{4,}', text2)
        
        if numbers1 and numbers2:
            # Se ambos têm números longos e são diferentes, pode ser suspeito
            return len(set(numbers1) & set(numbers2)) == 0
        
        return False
    
    def analyze_company_patterns(self, data):
        """Analisa padrões nos nomes das empresas"""
        
        logger.info("\n=== PADRÕES NOS NOMES DAS EMPRESAS ===")
        
        # Palavras mais comuns
        all_words = []
        for text in pd.concat([data['source_text'], data['target_text']]):
            if pd.notna(text):
                words = re.findall(r'\b\w+\b', str(text).lower())
                all_words.extend([w for w in words if len(w) > 2])
        
        word_counts = Counter(all_words)
        
        logger.info("Palavras mais comuns nos nomes:")
        for word, count in word_counts.most_common(15):
            logger.info(f"  {word}: {count:,}")
        
        # Sufixos comuns
        suffixes = []
        for text in pd.concat([data['source_text'], data['target_text']]):
            if pd.notna(text):
                text_clean = str(text).strip()
                # Extrair possíveis sufixos (últimas palavras)
                words = text_clean.split()
                if len(words) > 1:
                    suffixes.extend(words[-2:])  # Últimas 2 palavras
        
        suffix_counts = Counter([s.lower() for s in suffixes if len(s) > 1])
        
        logger.info("\nSufixos mais comuns:")
        for suffix, count in suffix_counts.most_common(10):
            logger.info(f"  {suffix}: {count:,}")
    
    def suggest_validation_priorities(self, data):
        """Sugere prioridades para validação manual"""
        
        logger.info("\n=== SUGESTÕES PARA VALIDAÇÃO MANUAL ===")
        
        # Prioridade 1: Casos com alta similaridade mas suspeitos
        priority1 = data[
            (data['similarity'] > 0.85) & 
            (data['similarity'] < 0.95)
        ].copy()
        
        # Prioridade 2: Casos com similaridade média-alta
        priority2 = data[
            (data['similarity'] >= 0.75) & 
            (data['similarity'] <= 0.85)
        ].copy()
        
        # Prioridade 3: Casos com similaridade média
        priority3 = data[
            (data['similarity'] >= 0.65) & 
            (data['similarity'] < 0.75)
        ].copy()
        
        logger.info("Sugestão de prioridades para validação:")
        logger.info(f"  Prioridade 1 (0.85-0.95): {len(priority1):,} casos")
        logger.info(f"  Prioridade 2 (0.75-0.85): {len(priority2):,} casos")
        logger.info(f"  Prioridade 3 (0.65-0.75): {len(priority3):,} casos")
        
        logger.info(f"\nRecomendação: Comece validando ~200-500 casos da Prioridade 1")
        logger.info("Isso deve fornecer dados suficientes para um primeiro treinamento.")
        
        # Salvar amostras para validação
        if len(priority1) > 0:
            sample_p1 = priority1.sample(n=min(500, len(priority1)), random_state=42)
            sample_p1.to_csv("data/priority1_sample.csv", index=False)
            logger.info(f"Amostra da Prioridade 1 salva em: data/priority1_sample.csv")
        
        return {
            'priority1': priority1,
            'priority2': priority2,
            'priority3': priority3
        }
    
    def export_analysis_report(self, data):
        """Exporta relatório de análise"""
        
        report_path = "data/match_analysis_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE ANÁLISE DE MATCHES\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Data da análise: {pd.Timestamp.now()}\n")
            f.write(f"Total de registros analisados: {len(data):,}\n\n")
            
            # Estatísticas por fonte
            f.write("DISTRIBUIÇÃO POR FONTE:\n")
            for source, count in data['source_type'].value_counts().items():
                f.write(f"  {source}: {count:,} ({count/len(data)*100:.1f}%)\n")
            
            f.write(f"\nESTATÍSTICAS DE SIMILARIDADE:\n")
            f.write(f"  Média: {data['similarity'].mean():.3f}\n")
            f.write(f"  Mediana: {data['similarity'].median():.3f}\n")
            f.write(f"  Desvio padrão: {data['similarity'].std():.3f}\n")
            f.write(f"  Mínima: {data['similarity'].min():.3f}\n")
            f.write(f"  Máxima: {data['similarity'].max():.3f}\n")
        
        logger.info(f"Relatório de análise salvo em: {report_path}")

def main():
    """Função principal"""
    
    analyzer = MatchAnalyzer()
    
    print("=== Análise de Matches ===")
    print("Analisando padrões nos dados de matching...")
    
    try:
        data = analyzer.load_and_analyze()
        analyzer.export_analysis_report(data)
        
        print("\n✅ Análise concluída!")
        print("📄 Relatório salvo em: data/match_analysis_report.txt")
        print("📊 Amostra prioritária salva em: data/priority1_sample.csv")
        
        print("\n💡 Próximos passos recomendados:")
        print("1. Execute 'python3 manual_validation.py' para começar a validação")
        print("2. Foque primeiro nos casos de Prioridade 1 (similaridade 0.85-0.95)")
        print("3. Valide pelo menos 200-500 casos antes do primeiro treinamento")
        
    except Exception as e:
        logger.error(f"Erro durante análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
