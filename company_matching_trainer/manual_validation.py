#!/usr/bin/env python3
"""
Sistema de Validação Manual para Company Matching
================================================

Interface para validar manualmente matches e treinar modelo com base na validação.
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
from company_matching_trainer import CompanyMatchingTrainer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManualValidator:
    """Sistema de validação manual de matches"""
    
    def __init__(self):
        self.data_loader = GeremDataLoader(results_base_path="../results")
        self.trainer = CompanyMatchingTrainer()
        self.validation_file = "data/manual_validation.csv"
        self.progress_file = "data/validation_progress.json"
        
        # Criar diretórios
        Path("data").mkdir(exist_ok=True)
        
    def load_data_for_validation(self, sample_size=1000, focus_on_uncertain=True):
        """Carrega dados priorizando casos incertos para validação manual"""
        
        logger.info("Carregando dados para validação manual...")
        
        # Carregar todos os dados
        combined_data = self.data_loader.load_all_latest_data()
        
        if focus_on_uncertain:
            # Focar em casos incertos (similaridade entre 0.7-0.95)
            uncertain_data = combined_data[
                (combined_data['similarity'] >= 0.70) & 
                (combined_data['similarity'] <= 0.95)
            ].copy()
            
            logger.info(f"Casos incertos encontrados: {len(uncertain_data)}")
            
            # Amostrar casos incertos
            if len(uncertain_data) > sample_size:
                validation_data = uncertain_data.sample(n=sample_size, random_state=42)
            else:
                validation_data = uncertain_data.copy()
                
        else:
            # Amostra aleatória de todos os dados
            validation_data = combined_data.sample(n=min(sample_size, len(combined_data)), random_state=42)
        
        # Adicionar colunas para validação manual
        validation_data['manual_label'] = -1  # -1 = não validado, 0 = falso, 1 = verdadeiro
        validation_data['validation_confidence'] = ''  # baixa, média, alta
        validation_data['validation_notes'] = ''
        validation_data['validated_by'] = ''
        validation_data['validation_date'] = ''
        
        # Ordenar por similaridade (mais incertos primeiro)
        validation_data = validation_data.sort_values('similarity', ascending=False)
        validation_data = validation_data.reset_index(drop=True)
        
        logger.info(f"Dados preparados para validação: {len(validation_data)} registros")
        
        return validation_data
    
    def save_validation_data(self, df):
        """Salva dados de validação"""
        df.to_csv(self.validation_file, index=False)
        logger.info(f"Dados de validação salvos em: {self.validation_file}")
        
    def load_validation_data(self):
        """Carrega dados de validação existentes"""
        if Path(self.validation_file).exists():
            return pd.read_csv(self.validation_file)
        return None
    
    def save_progress(self, current_index, total_records, validated_count):
        """Salva progresso da validação"""
        progress = {
            'current_index': current_index,
            'total_records': total_records,
            'validated_count': validated_count,
            'last_update': datetime.now().isoformat(),
            'completion_percentage': (validated_count / total_records) * 100
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def load_progress(self):
        """Carrega progresso da validação"""
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return None
    
    def interactive_validation(self, start_index=0, batch_size=50):
        """Interface interativa para validação manual"""
        
        # Carregar ou criar dados de validação
        validation_data = self.load_validation_data()
        
        if validation_data is None:
            logger.info("Criando novo conjunto de dados para validação...")
            validation_data = self.load_data_for_validation(sample_size=1000)
            self.save_validation_data(validation_data)
        
        total_records = len(validation_data)
        current_index = start_index
        
        logger.info(f"=== Validação Manual de Matches ===")
        logger.info(f"Total de registros: {total_records}")
        logger.info(f"Iniciando do índice: {current_index}")
        logger.info("\nInstruções:")
        logger.info("  1 = MATCH CORRETO (mesma empresa)")
        logger.info("  0 = FALSO POSITIVO (empresas diferentes)")
        logger.info("  s = PULAR este registro")
        logger.info("  q = SAIR e salvar progresso")
        logger.info("  r = RELATÓRIO de progresso")
        logger.info("-" * 60)
        
        validated_count = len(validation_data[validation_data['manual_label'] != -1])
        
        try:
            while current_index < total_records:
                row = validation_data.iloc[current_index]
                
                # Mostrar informações do match
                print(f"\n📊 Registro {current_index + 1}/{total_records}")
                print(f"Similaridade: {row['similarity']:.3f}")
                print(f"Fonte: {row['source_type']}")
                print("-" * 40)
                print(f"EMPRESA A: {row['source_text']}")
                print(f"EMPRESA B: {row['target_text']}")
                print("-" * 40)
                
                # Verificar se já foi validado
                if row['manual_label'] != -1:
                    status = "MATCH CORRETO" if row['manual_label'] == 1 else "FALSO POSITIVO"
                    print(f"✅ JÁ VALIDADO: {status}")
                    current_index += 1
                    continue
                
                # Solicitar validação
                while True:
                    response = input("É o mesmo empresa? (1=sim, 0=não, s=pular, q=sair, r=relatório): ").strip().lower()
                    
                    if response == 'q':
                        print("Saindo e salvando progresso...")
                        self.save_validation_data(validation_data)
                        self.save_progress(current_index, total_records, validated_count)
                        return validation_data
                    
                    elif response == 'r':
                        self.show_progress_report(validation_data)
                        continue
                    
                    elif response == 's':
                        print("⏭️ Pulando registro...")
                        break
                    
                    elif response in ['0', '1']:
                        # Validar o registro
                        label = int(response)
                        validation_data.loc[current_index, 'manual_label'] = label
                        validation_data.loc[current_index, 'validation_date'] = datetime.now().isoformat()
                        validation_data.loc[current_index, 'validated_by'] = 'manual'
                        
                        # Solicitar confiança (opcional)
                        confidence = input("Confiança na decisão (a=alta, m=média, b=baixa, enter=pular): ").strip().lower()
                        if confidence in ['a', 'm', 'b']:
                            conf_map = {'a': 'alta', 'm': 'média', 'b': 'baixa'}
                            validation_data.loc[current_index, 'validation_confidence'] = conf_map[confidence]
                        
                        # Notas opcionais
                        notes = input("Notas (opcional, enter=pular): ").strip()
                        if notes:
                            validation_data.loc[current_index, 'validation_notes'] = notes
                        
                        validated_count += 1
                        status = "✅ MATCH CORRETO" if label == 1 else "❌ FALSO POSITIVO"
                        print(f"{status} - Registrado!")
                        
                        # Salvar a cada 10 validações
                        if validated_count % 10 == 0:
                            self.save_validation_data(validation_data)
                            self.save_progress(current_index, total_records, validated_count)
                            print(f"💾 Progresso salvo ({validated_count} validações)")
                        
                        break
                    
                    else:
                        print("❌ Resposta inválida. Use: 1, 0, s, q, ou r")
                
                current_index += 1
                
                # Relatório a cada batch
                if current_index % batch_size == 0:
                    self.show_progress_report(validation_data)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrompido pelo usuário. Salvando progresso...")
            self.save_validation_data(validation_data)
            self.save_progress(current_index, total_records, validated_count)
        
        return validation_data
    
    def show_progress_report(self, validation_data):
        """Mostra relatório de progresso"""
        total = len(validation_data)
        validated = len(validation_data[validation_data['manual_label'] != -1])
        matches = len(validation_data[validation_data['manual_label'] == 1])
        false_positives = len(validation_data[validation_data['manual_label'] == 0])
        
        print(f"\n📈 RELATÓRIO DE PROGRESSO")
        print(f"Total de registros: {total}")
        print(f"Validados: {validated} ({validated/total*100:.1f}%)")
        print(f"Matches corretos: {matches}")
        print(f"Falsos positivos: {false_positives}")
        if validated > 0:
            print(f"Taxa de falsos positivos: {false_positives/validated*100:.1f}%")
        print("-" * 40)
    
    def prepare_training_data(self):
        """Prepara dados de treinamento com validação manual"""
        
        validation_data = self.load_validation_data()
        if validation_data is None:
            raise ValueError("Nenhum dado de validação encontrado! Execute a validação manual primeiro.")
        
        # Filtrar apenas dados validados manualmente
        manually_validated = validation_data[validation_data['manual_label'] != -1].copy()
        
        if len(manually_validated) == 0:
            raise ValueError("Nenhum dado foi validado manualmente ainda!")
        
        logger.info(f"Dados validados manualmente: {len(manually_validated)}")
        
        # Preparar dados para treinamento
        training_data = manually_validated[['source_text', 'target_text', 'similarity', 'source_type']].copy()
        training_data['label'] = manually_validated['manual_label']
        training_data['confidence'] = 'manual_validation'
        
        # Adicionar dados automáticos de alta confiança se necessário
        if len(manually_validated) < 500:
            logger.info("Poucos dados validados manualmente. Adicionando dados automáticos de alta confiança...")
            
            # Carregar todos os dados
            all_data = self.data_loader.load_all_latest_data()
            
            # Adicionar matches muito similares (>0.98) como positivos
            high_confidence_positive = all_data[all_data['similarity'] > 0.98].copy()
            high_confidence_positive['label'] = 1
            high_confidence_positive['confidence'] = 'auto_high_similarity'
            
            # Adicionar matches pouco similares (<0.65) como negativos
            high_confidence_negative = all_data[all_data['similarity'] < 0.65].copy()
            high_confidence_negative['label'] = 0
            high_confidence_negative['confidence'] = 'auto_low_similarity'
            
            # Combinar dados
            auto_data = pd.concat([high_confidence_positive, high_confidence_negative], ignore_index=True)
            auto_data = auto_data[['source_text', 'target_text', 'similarity', 'source_type', 'label', 'confidence']]
            
            # Limitar dados automáticos
            if len(auto_data) > 2000:
                auto_data = auto_data.sample(n=2000, random_state=42)
            
            training_data = pd.concat([training_data, auto_data], ignore_index=True)
            logger.info(f"Dados automáticos adicionados: {len(auto_data)}")
        
        logger.info(f"Total de dados para treinamento: {len(training_data)}")
        
        # Estatísticas
        positive_count = len(training_data[training_data['label'] == 1])
        negative_count = len(training_data[training_data['label'] == 0])
        
        logger.info(f"Matches positivos: {positive_count}")
        logger.info(f"Matches negativos: {negative_count}")
        
        return training_data
    
    def train_with_manual_validation(self):
        """Treina modelo usando dados de validação manual"""
        
        logger.info("=== Treinamento com Validação Manual ===")
        
        # Preparar dados de treinamento
        training_data = self.prepare_training_data()
        
        # Salvar dados de treinamento
        training_path = "data/manual_training_data.csv"
        training_data.to_csv(training_path, index=False)
        logger.info(f"Dados de treinamento salvos em: {training_path}")
        
        # Treinar modelo
        train_dataset, val_dataset, test_dataset = self.trainer.prepare_datasets(training_data)
        
        # Configurações de treinamento
        train_result = self.trainer.train_model(
            train_dataset, val_dataset,
            output_dir='models/manual_validated_matcher',
            num_epochs=5,  # Mais épocas para dados manuais
            batch_size=16,
            learning_rate=2e-5
        )
        
        # Avaliar modelo
        eval_result = self.trainer.evaluate_model(test_dataset, output_dir='models/manual_validated_matcher')
        
        # Relatório final
        logger.info("=== Treinamento Concluído ===")
        logger.info(f"Acurácia: {eval_result['detailed_metrics']['accuracy']:.4f}")
        logger.info(f"F1-Score: {eval_result['detailed_metrics']['f1']:.4f}")
        logger.info("Modelo salvo em: models/manual_validated_matcher/")
        
        return {
            'training_data': training_data,
            'train_result': train_result,
            'eval_result': eval_result
        }

def main():
    """Função principal"""
    
    validator = ManualValidator()
    
    print("=== Sistema de Validação Manual ===")
    print("1. Validar matches manualmente")
    print("2. Treinar modelo com validação manual")
    print("3. Mostrar progresso atual")
    print("4. Sair")
    
    while True:
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == '1':
            print("\n🔍 Iniciando validação manual...")
            validator.interactive_validation()
            
        elif choice == '2':
            print("\n🚀 Treinando modelo com dados validados...")
            try:
                results = validator.train_with_manual_validation()
                print("✅ Treinamento concluído com sucesso!")
            except Exception as e:
                print(f"❌ Erro durante treinamento: {e}")
                
        elif choice == '3':
            validation_data = validator.load_validation_data()
            if validation_data is not None:
                validator.show_progress_report(validation_data)
            else:
                print("❌ Nenhum dado de validação encontrado.")
                
        elif choice == '4':
            print("👋 Saindo...")
            break
            
        else:
            print("❌ Opção inválida. Escolha 1-4.")

if __name__ == "__main__":
    main()
