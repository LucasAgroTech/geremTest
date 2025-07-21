#!/usr/bin/env python3
"""
Reset e Continuação da Validação Manual
======================================

Script para resetar a validação e carregar novos dados, incluindo casos de alta similaridade.
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

class ExtendedValidator(ManualValidator):
    """Validador estendido com opções de reset e novos dados"""
    
    def __init__(self):
        super().__init__()
        self.backup_file = "data/manual_validation_backup.csv"
        
    def backup_current_validation(self):
        """Faz backup da validação atual"""
        validation_data = self.load_validation_data()
        if validation_data is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/manual_validation_backup_{timestamp}.csv"
            validation_data.to_csv(backup_path, index=False)
            logger.info(f"Backup salvo em: {backup_path}")
            return backup_path
        return None
    
    def load_new_validation_data(self, include_high_similarity=True, sample_size=1000, 
                                similarity_ranges=None):
        """Carrega novos dados para validação, incluindo alta similaridade"""
        
        logger.info("Carregando novos dados para validação...")
        
        # Carregar todos os dados
        combined_data = self.data_loader.load_all_latest_data()
        
        if similarity_ranges is None:
            if include_high_similarity:
                # Incluir casos de alta similaridade (0.95-1.0) e casos incertos (0.7-0.95)
                similarity_ranges = [
                    (0.95, 1.0),   # Alta similaridade - podem ser matches corretos
                    (0.85, 0.95),  # Muito incertos
                    (0.75, 0.85),  # Incertos
                    (0.70, 0.75)   # Moderadamente incertos
                ]
            else:
                # Apenas casos incertos
                similarity_ranges = [(0.70, 0.95)]
        
        # Coletar dados de cada faixa
        all_validation_data = []
        
        for min_sim, max_sim in similarity_ranges:
            range_data = combined_data[
                (combined_data['similarity'] >= min_sim) & 
                (combined_data['similarity'] <= max_sim)
            ].copy()
            
            if not range_data.empty:
                # Amostrar proporcionalmente
                range_sample_size = int(sample_size * 0.25)  # 25% para cada faixa
                if len(range_data) > range_sample_size:
                    range_sample = range_data.sample(n=range_sample_size, random_state=42)
                else:
                    range_sample = range_data.copy()
                
                all_validation_data.append(range_sample)
                logger.info(f"Faixa {min_sim}-{max_sim}: {len(range_sample)} casos selecionados")
        
        if not all_validation_data:
            raise ValueError("Nenhum dado encontrado nas faixas especificadas!")
        
        # Combinar todos os dados
        validation_data = pd.concat(all_validation_data, ignore_index=True)
        
        # Embaralhar para misturar as faixas
        validation_data = validation_data.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Adicionar colunas para validação manual
        validation_data['manual_label'] = -1  # -1 = não validado
        validation_data['validation_confidence'] = ''
        validation_data['validation_notes'] = ''
        validation_data['validated_by'] = ''
        validation_data['validation_date'] = ''
        
        logger.info(f"Total de novos dados preparados: {len(validation_data)} registros")
        
        # Mostrar distribuição por similaridade
        logger.info("Distribuição por faixas de similaridade:")
        bins = [0.7, 0.75, 0.85, 0.95, 1.0]
        labels = ['0.70-0.75', '0.75-0.85', '0.85-0.95', '0.95-1.0']
        validation_data['sim_range'] = pd.cut(validation_data['similarity'], bins=bins, labels=labels, include_lowest=True)
        
        for range_label, count in validation_data['sim_range'].value_counts().sort_index().items():
            logger.info(f"  {range_label}: {count} casos")
        
        return validation_data
    
    def reset_validation(self, include_high_similarity=True, sample_size=1000):
        """Reseta a validação e carrega novos dados"""
        
        logger.info("=== RESET DA VALIDAÇÃO ===")
        
        # Fazer backup da validação atual
        backup_path = self.backup_current_validation()
        if backup_path:
            logger.info(f"✅ Backup da validação anterior salvo")
        
        # Carregar novos dados
        new_validation_data = self.load_new_validation_data(
            include_high_similarity=include_high_similarity,
            sample_size=sample_size
        )
        
        # Salvar novos dados
        self.save_validation_data(new_validation_data)
        
        # Resetar progresso
        progress = {
            'current_index': 0,
            'total_records': len(new_validation_data),
            'validated_count': 0,
            'last_update': datetime.now().isoformat(),
            'completion_percentage': 0.0,
            'reset_date': datetime.now().isoformat(),
            'include_high_similarity': include_high_similarity
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        logger.info("✅ Validação resetada com sucesso!")
        logger.info(f"Novos dados: {len(new_validation_data)} registros")
        
        return new_validation_data
    
    def show_validation_statistics(self):
        """Mostra estatísticas detalhadas da validação"""
        
        validation_data = self.load_validation_data()
        if validation_data is None:
            logger.info("❌ Nenhum dado de validação encontrado")
            return
        
        total = len(validation_data)
        validated = len(validation_data[validation_data['manual_label'] != -1])
        matches = len(validation_data[validation_data['manual_label'] == 1])
        false_positives = len(validation_data[validation_data['manual_label'] == 0])
        
        logger.info("\n📊 ESTATÍSTICAS DETALHADAS DA VALIDAÇÃO")
        logger.info(f"Total de registros: {total}")
        logger.info(f"Validados: {validated} ({validated/total*100:.1f}%)")
        logger.info(f"Matches corretos: {matches}")
        logger.info(f"Falsos positivos: {false_positives}")
        
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
                    
                    logger.info(f"  {range_label}: {len(range_data)} total, {range_validated} validados")
                    if range_validated > 0:
                        logger.info(f"    Matches: {range_matches} ({range_matches/range_validated*100:.1f}%)")
                        logger.info(f"    Falsos: {range_false} ({range_false/range_validated*100:.1f}%)")

def main():
    """Função principal"""
    
    validator = ExtendedValidator()
    
    print("=== Reset e Continuação da Validação Manual ===")
    print("1. Resetar validação (incluir alta similaridade 0.95-1.0)")
    print("2. Resetar validação (apenas casos incertos 0.7-0.95)")
    print("3. Continuar validação atual")
    print("4. Mostrar estatísticas detalhadas")
    print("5. Fazer backup da validação atual")
    print("6. Sair")
    
    while True:
        choice = input("\nEscolha uma opção (1-6): ").strip()
        
        if choice == '1':
            print("\n🔄 Resetando validação com alta similaridade...")
            try:
                sample_size = input("Quantos casos carregar? (padrão: 1000): ").strip()
                sample_size = int(sample_size) if sample_size else 1000
                
                new_data = validator.reset_validation(
                    include_high_similarity=True, 
                    sample_size=sample_size
                )
                print(f"✅ Reset concluído! {len(new_data)} novos casos carregados.")
                print("Execute 'python3 manual_validation.py' para começar a validação.")
                
            except Exception as e:
                print(f"❌ Erro durante reset: {e}")
                
        elif choice == '2':
            print("\n🔄 Resetando validação apenas com casos incertos...")
            try:
                sample_size = input("Quantos casos carregar? (padrão: 1000): ").strip()
                sample_size = int(sample_size) if sample_size else 1000
                
                new_data = validator.reset_validation(
                    include_high_similarity=False, 
                    sample_size=sample_size
                )
                print(f"✅ Reset concluído! {len(new_data)} novos casos carregados.")
                print("Execute 'python3 manual_validation.py' para começar a validação.")
                
            except Exception as e:
                print(f"❌ Erro durante reset: {e}")
                
        elif choice == '3':
            print("\n▶️ Continuando validação atual...")
            print("Execute 'python3 manual_validation.py' para continuar.")
            
        elif choice == '4':
            print("\n📊 Mostrando estatísticas...")
            validator.show_validation_statistics()
            
        elif choice == '5':
            print("\n💾 Fazendo backup...")
            backup_path = validator.backup_current_validation()
            if backup_path:
                print(f"✅ Backup salvo em: {backup_path}")
            else:
                print("❌ Nenhum dado para backup.")
                
        elif choice == '6':
            print("👋 Saindo...")
            break
            
        else:
            print("❌ Opção inválida. Escolha 1-6.")

if __name__ == "__main__":
    main()
