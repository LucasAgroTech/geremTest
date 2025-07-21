#!/usr/bin/env python3
"""
Extensão da Validação Manual (Acumulativa)
==========================================

Script para adicionar novos dados à validação existente, preservando todas as validações anteriores.
"""

import sys
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

from data_loader_enhanced import GeremDataLoader
from manual_validation import ManualValidator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AccumulativeValidator(ManualValidator):
    """Validador que acumula validações anteriores com novos dados"""
    
    def __init__(self):
        super().__init__()
        self.accumulated_file = "data/accumulated_validation.csv"
        
    def backup_current_validation(self):
        """Faz backup da validação atual"""
        validation_data = self.load_validation_data()
        if validation_data is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/validation_backup_{timestamp}.csv"
            validation_data.to_csv(backup_path, index=False)
            logger.info(f"Backup salvo em: {backup_path}")
            return backup_path
        return None
    
    def get_validated_pairs(self, validation_data):
        """Extrai pares já validados para evitar duplicatas"""
        validated = validation_data[validation_data['manual_label'] != -1]
        if len(validated) == 0:
            return set()
        
        # Criar conjunto de pares únicos (source_text, target_text)
        pairs = set()
        for _, row in validated.iterrows():
            pair = (str(row['source_text']).strip().lower(), 
                   str(row['target_text']).strip().lower())
            pairs.add(pair)
        
        return pairs
    
    def load_new_data_excluding_validated(self, existing_pairs, include_high_similarity=True, 
                                        sample_size=1000):
        """Carrega novos dados excluindo pares já validados"""
        
        logger.info("Carregando novos dados (excluindo já validados)...")
        
        # Carregar todos os dados
        combined_data = self.data_loader.load_all_latest_data()
        
        # Filtrar dados já validados
        new_data = []
        for _, row in combined_data.iterrows():
            pair = (str(row['source_text']).strip().lower(), 
                   str(row['target_text']).strip().lower())
            
            if pair not in existing_pairs:
                new_data.append(row)
        
        if not new_data:
            logger.warning("Nenhum dado novo encontrado (todos já foram validados)")
            return pd.DataFrame()
        
        new_df = pd.DataFrame(new_data)
        logger.info(f"Dados novos disponíveis: {len(new_df)} registros")
        
        # Definir faixas de similaridade
        if include_high_similarity:
            similarity_ranges = [
                (0.95, 1.0),   # Alta similaridade - podem ser matches corretos
                (0.85, 0.95),  # Muito incertos
                (0.75, 0.85),  # Incertos
                (0.70, 0.75)   # Moderadamente incertos
            ]
        else:
            similarity_ranges = [(0.70, 0.95)]
        
        # Coletar dados de cada faixa
        all_validation_data = []
        
        for min_sim, max_sim in similarity_ranges:
            range_data = new_df[
                (new_df['similarity'] >= min_sim) & 
                (new_df['similarity'] <= max_sim)
            ].copy()
            
            if not range_data.empty:
                # Amostrar proporcionalmente
                range_sample_size = int(sample_size * 0.25)  # 25% para cada faixa
                if len(range_data) > range_sample_size:
                    range_sample = range_data.sample(n=range_sample_size, random_state=42)
                else:
                    range_sample = range_data.copy()
                
                all_validation_data.append(range_sample)
                logger.info(f"Faixa {min_sim}-{max_sim}: {len(range_sample)} novos casos")
        
        if not all_validation_data:
            logger.warning("Nenhum dado novo encontrado nas faixas especificadas!")
            return pd.DataFrame()
        
        # Combinar todos os dados
        validation_data = pd.concat(all_validation_data, ignore_index=True)
        
        # Embaralhar
        validation_data = validation_data.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Adicionar colunas para validação manual
        validation_data['manual_label'] = -1
        validation_data['validation_confidence'] = ''
        validation_data['validation_notes'] = ''
        validation_data['validated_by'] = ''
        validation_data['validation_date'] = ''
        
        logger.info(f"Novos dados preparados: {len(validation_data)} registros")
        
        return validation_data
    
    def extend_validation(self, include_high_similarity=True, sample_size=1000):
        """Estende a validação atual com novos dados, preservando validações anteriores"""
        
        logger.info("=== EXTENSÃO DA VALIDAÇÃO (ACUMULATIVA) ===")
        
        # Carregar validação atual
        current_validation = self.load_validation_data()
        
        if current_validation is None:
            logger.info("Nenhuma validação anterior encontrada. Criando nova...")
            # Se não há validação anterior, criar nova
            new_validation_data = self.load_new_validation_data(
                include_high_similarity=include_high_similarity,
                sample_size=sample_size
            )
        else:
            logger.info(f"Validação atual: {len(current_validation)} registros")
            
            # Fazer backup
            backup_path = self.backup_current_validation()
            if backup_path:
                logger.info("✅ Backup da validação atual criado")
            
            # Obter pares já validados
            existing_pairs = self.get_validated_pairs(current_validation)
            logger.info(f"Pares já validados: {len(existing_pairs)}")
            
            # Carregar novos dados excluindo já validados
            new_data = self.load_new_data_excluding_validated(
                existing_pairs, 
                include_high_similarity=include_high_similarity,
                sample_size=sample_size
            )
            
            if len(new_data) == 0:
                logger.warning("❌ Nenhum dado novo para adicionar!")
                return current_validation
            
            # Combinar validação atual com novos dados
            new_validation_data = pd.concat([current_validation, new_data], ignore_index=True)
            logger.info(f"Dados combinados: {len(current_validation)} anteriores + {len(new_data)} novos = {len(new_validation_data)} total")
        
        # Salvar dados estendidos
        self.save_validation_data(new_validation_data)
        
        # Atualizar progresso
        validated_count = len(new_validation_data[new_validation_data['manual_label'] != -1])
        progress = {
            'current_index': 0,  # Resetar índice para começar do primeiro não validado
            'total_records': len(new_validation_data),
            'validated_count': validated_count,
            'last_update': datetime.now().isoformat(),
            'completion_percentage': (validated_count / len(new_validation_data)) * 100,
            'extension_date': datetime.now().isoformat(),
            'include_high_similarity': include_high_similarity
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        logger.info("✅ Validação estendida com sucesso!")
        logger.info(f"Total de registros: {len(new_validation_data)}")
        logger.info(f"Já validados: {validated_count}")
        logger.info(f"Pendentes: {len(new_validation_data) - validated_count}")
        
        return new_validation_data
    
    def show_accumulated_statistics(self):
        """Mostra estatísticas acumuladas de todas as validações"""
        
        validation_data = self.load_validation_data()
        if validation_data is None:
            logger.info("❌ Nenhum dado de validação encontrado")
            return
        
        total = len(validation_data)
        validated = len(validation_data[validation_data['manual_label'] != -1])
        matches = len(validation_data[validation_data['manual_label'] == 1])
        false_positives = len(validation_data[validation_data['manual_label'] == 0])
        pending = total - validated
        
        logger.info("\n📊 ESTATÍSTICAS ACUMULADAS DA VALIDAÇÃO")
        logger.info(f"Total de registros: {total:,}")
        logger.info(f"Validados: {validated:,} ({validated/total*100:.1f}%)")
        logger.info(f"Pendentes: {pending:,} ({pending/total*100:.1f}%)")
        logger.info(f"Matches corretos: {matches:,}")
        logger.info(f"Falsos positivos: {false_positives:,}")
        
        if validated > 0:
            logger.info(f"Taxa de matches corretos: {matches/validated*100:.1f}%")
            logger.info(f"Taxa de falsos positivos: {false_positives/validated*100:.1f}%")
        
        # Estatísticas por faixa de similaridade
        if 'similarity' in validation_data.columns:
            logger.info("\n📈 Por faixa de similaridade:")
            bins = [0.7, 0.75, 0.85, 0.95, 1.0]
            labels = ['0.70-0.75', '0.75-0.85', '0.85-0.95', '0.95-1.0']
            validation_data['sim_range'] = pd.cut(validation_data['similarity'], bins=bins, labels=labels, include_lowest=True)
            
            for range_label in labels:
                range_data = validation_data[validation_data['sim_range'] == range_label]
                if len(range_data) > 0:
                    range_validated = len(range_data[range_data['manual_label'] != -1])
                    range_matches = len(range_data[range_data['manual_label'] == 1])
                    range_false = len(range_data[range_data['manual_label'] == 0])
                    range_pending = len(range_data) - range_validated
                    
                    logger.info(f"  {range_label}: {len(range_data):,} total")
                    logger.info(f"    Validados: {range_validated:,}, Pendentes: {range_pending:,}")
                    if range_validated > 0:
                        logger.info(f"    Matches: {range_matches:,} ({range_matches/range_validated*100:.1f}%)")
                        logger.info(f"    Falsos: {range_false:,} ({range_false/range_validated*100:.1f}%)")
        
        # Estatísticas para treinamento
        logger.info(f"\n🎯 DADOS PARA TREINAMENTO:")
        logger.info(f"Total de exemplos rotulados: {validated:,}")
        logger.info(f"Balanceamento: {matches:,} positivos / {false_positives:,} negativos")
        
        if validated >= 200:
            logger.info("✅ Dados suficientes para treinamento!")
        else:
            logger.info(f"⚠️ Recomendado pelo menos 200 exemplos (atual: {validated})")

def main():
    """Função principal"""
    
    validator = AccumulativeValidator()
    
    print("=== Extensão Acumulativa da Validação Manual ===")
    print("1. Estender validação (incluir alta similaridade 0.95-1.0)")
    print("2. Estender validação (apenas casos incertos 0.7-0.95)")
    print("3. Mostrar estatísticas acumuladas")
    print("4. Fazer backup da validação atual")
    print("5. Continuar validação")
    print("6. Sair")
    
    while True:
        choice = input("\nEscolha uma opção (1-6): ").strip()
        
        if choice == '1':
            print("\n📈 Estendendo validação com alta similaridade...")
            try:
                sample_size = input("Quantos novos casos adicionar? (padrão: 1000): ").strip()
                sample_size = int(sample_size) if sample_size else 1000
                
                extended_data = validator.extend_validation(
                    include_high_similarity=True, 
                    sample_size=sample_size
                )
                print(f"✅ Validação estendida! Total: {len(extended_data)} registros.")
                print("Execute 'python3 manual_validation.py' para continuar validando.")
                
            except Exception as e:
                print(f"❌ Erro durante extensão: {e}")
                
        elif choice == '2':
            print("\n📈 Estendendo validação apenas com casos incertos...")
            try:
                sample_size = input("Quantos novos casos adicionar? (padrão: 1000): ").strip()
                sample_size = int(sample_size) if sample_size else 1000
                
                extended_data = validator.extend_validation(
                    include_high_similarity=False, 
                    sample_size=sample_size
                )
                print(f"✅ Validação estendida! Total: {len(extended_data)} registros.")
                print("Execute 'python3 manual_validation.py' para continuar validando.")
                
            except Exception as e:
                print(f"❌ Erro durante extensão: {e}")
                
        elif choice == '3':
            print("\n📊 Mostrando estatísticas acumuladas...")
            validator.show_accumulated_statistics()
            
        elif choice == '4':
            print("\n💾 Fazendo backup...")
            backup_path = validator.backup_current_validation()
            if backup_path:
                print(f"✅ Backup salvo em: {backup_path}")
            else:
                print("❌ Nenhum dado para backup.")
                
        elif choice == '5':
            print("\n▶️ Continuando validação...")
            print("Execute 'python3 manual_validation.py' para continuar.")
            
        elif choice == '6':
            print("👋 Saindo...")
            break
            
        else:
            print("❌ Opção inválida. Escolha 1-6.")

if __name__ == "__main__":
    main()
