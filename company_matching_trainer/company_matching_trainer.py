#!/usr/bin/env python3
"""
Company Matching Model Trainer
==============================

Projeto para treinar um modelo personalizado de matching de empresas
baseado nos resultados do sistema GEREM existente.

Funcionalidades:
- Carrega dados de matching existentes
- Interface para classificar matches como corretos/incorretos
- Treina modelo transformer personalizado
- Avalia performance do modelo
- Exporta modelo treinado para uso em produção
"""

import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    Trainer, TrainingArguments,
    EarlyStoppingCallback
)
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import json
from datetime import datetime
from pathlib import Path
import logging

# Importar o carregador de dados aprimorado
from data_loader_enhanced import GeremDataLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompanyMatchingDataset(Dataset):
    """Dataset personalizado para treinamento do modelo de matching"""
    
    def __init__(self, texts_a, texts_b, labels, tokenizer, max_length=128):
        self.texts_a = texts_a
        self.texts_b = texts_b
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts_a)
    
    def __getitem__(self, idx):
        text_a = str(self.texts_a[idx])
        text_b = str(self.texts_b[idx])
        label = self.labels[idx]
        
        # Tokenizar os dois textos juntos
        encoding = self.tokenizer(
            text_a,
            text_b,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class CompanyMatchingModel(torch.nn.Module):
    """Modelo personalizado para matching de empresas"""
    
    def __init__(self, model_name='neuralmind/bert-base-portuguese-cased', num_labels=2):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.dropout = torch.nn.Dropout(0.3)
        self.classifier = torch.nn.Linear(self.bert.config.hidden_size, num_labels)
        
    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        loss = None
        if labels is not None:
            loss_fct = torch.nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))
        
        return {'loss': loss, 'logits': logits}

class CompanyMatchingTrainer:
    """Classe principal para treinamento do modelo"""
    
    def __init__(self, model_name='neuralmind/bert-base-portuguese-cased', results_base_path='../results'):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = None
        self.trainer = None
        self.data_loader = GeremDataLoader(results_base_path)
        
        # Criar diretórios necessários
        Path('models').mkdir(exist_ok=True)
        Path('data').mkdir(exist_ok=True)
        Path('results').mkdir(exist_ok=True)
        
    def load_matching_results(self, results_path):
        """Carrega resultados de matching existentes"""
        logger.info(f"Carregando dados de: {results_path}")
        
        # Detectar formato do arquivo
        if results_path.endswith('.xlsx'):
            df = pd.read_excel(results_path)
        elif results_path.endswith('.csv'):
            df = pd.read_csv(results_path)
        else:
            raise ValueError("Formato de arquivo não suportado. Use .xlsx ou .csv")
        
        # Verificar colunas necessárias
        required_cols = ['source_text', 'target_text', 'similarity']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Colunas faltando: {missing_cols}")
        
        logger.info(f"Carregados {len(df)} registros de matching")
        return df
    
    def create_training_data(self, df, labeled_data_path=None):
        """Cria dados de treinamento com base nos resultados"""
        
        if labeled_data_path and os.path.exists(labeled_data_path):
            # Carregar dados já rotulados
            logger.info("Carregando dados já rotulados...")
            labeled_df = pd.read_csv(labeled_data_path)
            return labeled_df
        
        # Criar dados de treinamento automático baseado em similarity
        logger.info("Criando dados de treinamento automático...")
        
        # Estratégia automática de rotulação
        # Alta similaridade (>0.9) = Match correto (1)
        # Baixa similaridade (<0.5) = Match incorreto (0)
        # Média similaridade (0.5-0.9) = Revisar manualmente
        
        training_data = []
        
        # Matches claramente corretos
        high_sim = df[df['similarity'] > 0.9].copy()
        high_sim['label'] = 1
        high_sim['confidence'] = 'high'
        training_data.append(high_sim[['source_text', 'target_text', 'similarity', 'label', 'confidence']])
        
        # Matches claramente incorretos
        low_sim = df[df['similarity'] < 0.5].copy()
        low_sim['label'] = 0
        low_sim['confidence'] = 'high'
        training_data.append(low_sim[['source_text', 'target_text', 'similarity', 'label', 'confidence']])
        
        # Dados para revisão manual
        medium_sim = df[(df['similarity'] >= 0.5) & (df['similarity'] <= 0.9)].copy()
        medium_sim['label'] = -1  # Não rotulado
        medium_sim['confidence'] = 'needs_review'
        training_data.append(medium_sim[['source_text', 'target_text', 'similarity', 'label', 'confidence']])
        
        result_df = pd.concat(training_data, ignore_index=True)
        
        # Salvar para revisão
        review_path = 'data/training_data_for_review.csv'
        result_df.to_csv(review_path, index=False)
        logger.info(f"Dados salvos para revisão em: {review_path}")
        
        return result_df
    
    def prepare_datasets(self, df, test_size=0.2, val_size=0.1):
        """Prepara datasets para treinamento"""
        
        # Filtrar apenas dados rotulados
        labeled_df = df[df['label'] != -1].copy()
        
        if len(labeled_df) == 0:
            raise ValueError("Nenhum dado rotulado encontrado!")
        
        logger.info(f"Preparando datasets com {len(labeled_df)} exemplos rotulados")
        
        # Dividir dados
        train_texts_a, temp_texts_a, train_texts_b, temp_texts_b, train_labels, temp_labels = train_test_split(
            labeled_df['source_text'].tolist(),
            labeled_df['target_text'].tolist(),
            labeled_df['label'].tolist(),
            test_size=test_size + val_size,
            random_state=42,
            stratify=labeled_df['label'].tolist()
        )
        
        val_texts_a, test_texts_a, val_texts_b, test_texts_b, val_labels, test_labels = train_test_split(
            temp_texts_a, temp_texts_b, temp_labels,
            test_size=test_size / (test_size + val_size),
            random_state=42,
            stratify=temp_labels
        )
        
        # Criar datasets
        train_dataset = CompanyMatchingDataset(train_texts_a, train_texts_b, train_labels, self.tokenizer)
        val_dataset = CompanyMatchingDataset(val_texts_a, val_texts_b, val_labels, self.tokenizer)
        test_dataset = CompanyMatchingDataset(test_texts_a, test_texts_b, test_labels, self.tokenizer)
        
        logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")
        
        return train_dataset, val_dataset, test_dataset
    
    def train_model(self, train_dataset, val_dataset, output_dir='models/company_matcher', 
                   num_epochs=3, batch_size=16, learning_rate=2e-5):
        """Treina o modelo"""
        
        logger.info("Iniciando treinamento do modelo...")
        
        # Inicializar modelo
        self.model = CompanyMatchingModel(self.model_name)
        
        # Configurar argumentos de treinamento
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            logging_dir=f'{output_dir}/logs',
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=50,
            save_strategy="steps",
            save_steps=100,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,
            seed=42
        )
        
        # Métricas personalizadas
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            
            precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
            accuracy = accuracy_score(labels, predictions)
            
            return {
                'accuracy': accuracy,
                'f1': f1,
                'precision': precision,
                'recall': recall
            }
        
        # Configurar trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
        )
        
        # Treinar
        train_result = self.trainer.train()
        
        # Salvar modelo
        self.trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        # Salvar métricas de treinamento
        with open(f'{output_dir}/training_results.json', 'w') as f:
            json.dump(train_result.metrics, f, indent=2)
        
        logger.info("Treinamento concluído!")
        return train_result
    
    def evaluate_model(self, test_dataset, output_dir='models/company_matcher'):
        """Avalia o modelo"""
        
        logger.info("Avaliando modelo...")
        
        # Avaliar
        eval_result = self.trainer.evaluate(test_dataset)
        
        # Predições detalhadas
        predictions = self.trainer.predict(test_dataset)
        y_pred = np.argmax(predictions.predictions, axis=1)
        y_true = predictions.label_ids
        
        # Matriz de confusão
        cm = confusion_matrix(y_true, y_pred)
        
        # Salvar resultados
        results = {
            'evaluation_metrics': eval_result,
            'confusion_matrix': cm.tolist(),
            'detailed_metrics': {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_recall_fscore_support(y_true, y_pred, average='weighted')[0],
                'recall': precision_recall_fscore_support(y_true, y_pred, average='weighted')[1],
                'f1': precision_recall_fscore_support(y_true, y_pred, average='weighted')[2]
            }
        }
        
        with open(f'{output_dir}/evaluation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Acurácia: {results['detailed_metrics']['accuracy']:.4f}")
        logger.info(f"F1-Score: {results['detailed_metrics']['f1']:.4f}")
        
        return results
    
    def load_latest_gerem_data(self, high_threshold=0.9, low_threshold=0.5):
        """Carrega automaticamente os dados de embedding mais recentes do GEREM"""
        logger.info("=== Carregando dados de embedding mais recentes do GEREM ===")
        
        try:
            # Carregar todos os dados mais recentes
            combined_data = self.data_loader.load_all_latest_data()
            
            # Criar labels automáticos
            training_data = self.data_loader.create_training_labels(
                combined_data, 
                high_threshold=high_threshold, 
                low_threshold=low_threshold
            )
            
            # Salvar dados preparados
            output_path = self.data_loader.save_training_data(training_data)
            
            logger.info(f"✅ Dados carregados e preparados com sucesso!")
            logger.info(f"Total de registros: {len(training_data)}")
            logger.info(f"Dados salvos em: {output_path}")
            
            return training_data
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do GEREM: {e}")
            raise
    
    def run_complete_training_pipeline(self, high_threshold=0.9, low_threshold=0.5, 
                                     num_epochs=3, batch_size=16, learning_rate=2e-5):
        """Executa o pipeline completo de treinamento usando dados mais recentes do GEREM"""
        logger.info("=== Iniciando Pipeline Completo de Treinamento ===")
        
        try:
            # 1. Carregar dados mais recentes
            training_data = self.load_latest_gerem_data(high_threshold, low_threshold)
            
            # 2. Verificar se há dados suficientes para treinamento
            labeled_data = training_data[training_data['label'] != -1]
            if len(labeled_data) < 100:
                logger.warning(f"Poucos dados rotulados ({len(labeled_data)}). Considere ajustar os thresholds.")
                
            # 3. Preparar datasets
            train_dataset, val_dataset, test_dataset = self.prepare_datasets(training_data)
            
            # 4. Treinar modelo
            train_result = self.train_model(
                train_dataset, val_dataset, 
                num_epochs=num_epochs, 
                batch_size=batch_size, 
                learning_rate=learning_rate
            )
            
            # 5. Avaliar modelo
            eval_result = self.evaluate_model(test_dataset)
            
            # 6. Salvar relatório final
            final_report = {
                'data_summary': {
                    'total_records': len(training_data),
                    'labeled_records': len(labeled_data),
                    'positive_matches': len(training_data[training_data['label'] == 1]),
                    'negative_matches': len(training_data[training_data['label'] == 0]),
                    'needs_review': len(training_data[training_data['label'] == -1])
                },
                'training_config': {
                    'high_threshold': high_threshold,
                    'low_threshold': low_threshold,
                    'num_epochs': num_epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate
                },
                'training_results': train_result.metrics,
                'evaluation_results': eval_result['detailed_metrics']
            }
            
            with open('models/company_matcher/final_training_report.json', 'w') as f:
                json.dump(final_report, f, indent=2)
            
            logger.info("=== Pipeline de Treinamento Concluído com Sucesso! ===")
            logger.info(f"Acurácia Final: {eval_result['detailed_metrics']['accuracy']:.4f}")
            logger.info(f"F1-Score Final: {eval_result['detailed_metrics']['f1']:.4f}")
            logger.info("Relatório completo salvo em: models/company_matcher/final_training_report.json")
            
            return {
                'training_data': training_data,
                'train_result': train_result,
                'eval_result': eval_result,
                'final_report': final_report
            }
            
        except Exception as e:
            logger.error(f"Erro durante o pipeline de treinamento: {e}")
            raise
    
    def predict_match(self, text_a, text_b, model_path='models/company_matcher'):
        """Prediz se dois textos são um match"""
        
        if self.model is None:
            # Carregar modelo treinado
            self.model = CompanyMatchingModel()
            self.model.load_state_dict(torch.load(f'{model_path}/pytorch_model.bin'))
            self.model.eval()
        
        # Tokenizar
        encoding = self.tokenizer(
            text_a, text_b,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        # Predição
        with torch.no_grad():
            outputs = self.model(**encoding)
            probabilities = torch.softmax(outputs['logits'], dim=-1)
            prediction = torch.argmax(probabilities, dim=-1)
            confidence = torch.max(probabilities, dim=-1)[0]
        
        return {
            'match': bool(prediction.item()),
            'confidence': float(confidence.item()),
            'probabilities': {
                'no_match': float(probabilities[0][0].item()),
                'match': float(probabilities[0][1].item())
            }
        }

def main():
    """Função principal - Pipeline completo de treinamento"""
    logger.info("=== Company Matching Model Trainer ===")
    logger.info("Iniciando pipeline de treinamento com dados mais recentes do GEREM...")
    
    try:
        # Inicializar trainer
        trainer = CompanyMatchingTrainer()
        
        # Opção 1: Pipeline completo automático (recomendado)
        logger.info("\n🚀 Executando pipeline completo de treinamento...")
        results = trainer.run_complete_training_pipeline(
            high_threshold=0.9,    # Matches com similaridade > 0.9 = corretos
            low_threshold=0.5,     # Matches com similaridade < 0.5 = incorretos
            num_epochs=3,          # Número de épocas de treinamento
            batch_size=16,         # Tamanho do batch
            learning_rate=2e-5     # Taxa de aprendizado
        )
        
        logger.info("\n✅ Treinamento concluído com sucesso!")
        logger.info("Modelo salvo em: models/company_matcher/")
        
        # Testar o modelo treinado
        logger.info("\n🧪 Testando modelo treinado...")
        test_cases = [
            ("BASF", "BASF S.A."),
            ("Petrobras", "Petróleo Brasileiro S.A."),
            ("Vale", "Vale S.A."),
            ("Embraer", "Empresa Brasileira de Aeronáutica"),
            ("BASF", "Petrobras")  # Deve ser negativo
        ]
        
        for text_a, text_b in test_cases:
            result = trainer.predict_match(text_a, text_b)
            logger.info(f"'{text_a}' vs '{text_b}': {result['match']} (confiança: {result['confidence']:.3f})")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        logger.info("\n📋 Opções alternativas:")
        logger.info("1. Verificar se os dados estão em '../results'")
        logger.info("2. Ajustar thresholds se poucos dados rotulados")
        logger.info("3. Usar interface Streamlit para rotulação manual")
        
        # Opção 2: Apenas carregar e preparar dados (para debug)
        logger.info("\n🔍 Tentando apenas carregar dados...")
        try:
            training_data = trainer.load_latest_gerem_data()
            logger.info(f"Dados carregados: {len(training_data)} registros")
            
            # Mostrar estatísticas
            labeled_data = training_data[training_data['label'] != -1]
            logger.info(f"Dados rotulados: {len(labeled_data)}")
            logger.info(f"Matches positivos: {len(training_data[training_data['label'] == 1])}")
            logger.info(f"Matches negativos: {len(training_data[training_data['label'] == 0])}")
            logger.info(f"Precisam revisão: {len(training_data[training_data['label'] == -1])}")
            
        except Exception as e2:
            logger.error(f"Erro ao carregar dados: {e2}")
            logger.info("Verifique se os diretórios de resultados existem e contêm dados válidos.")

if __name__ == "__main__":
    main()
