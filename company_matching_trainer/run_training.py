#!/usr/bin/env python3
"""
Script Principal para Executar o Treinamento
===========================================

Executa o pipeline completo de treinamento do modelo de matching de empresas.
"""

import sys
import logging
from pathlib import Path

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(str(Path(__file__).parent))

from company_matching_trainer import CompanyMatchingTrainer

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

def main():
    """Função principal para executar o treinamento"""
    
    logger.info("=== Company Matching Model Trainer ===")
    logger.info("Iniciando pipeline de treinamento com dados mais recentes do GEREM...")
    
    try:
        # Inicializar trainer
        trainer = CompanyMatchingTrainer()
        
        # Configurações otimizadas baseadas nos dados disponíveis
        # Com base no teste: média=0.732, min=0.650, max=1.000
        # Ajustar thresholds para ter mais dados rotulados
        
        logger.info("\n🚀 Executando pipeline completo de treinamento...")
        logger.info("Configurações otimizadas:")
        logger.info("  - High threshold: 0.95 (matches muito similares)")
        logger.info("  - Low threshold: 0.70 (matches pouco similares)")
        logger.info("  - Epochs: 3")
        logger.info("  - Batch size: 16")
        
        results = trainer.run_complete_training_pipeline(
            high_threshold=0.95,   # Mais conservador para matches corretos
            low_threshold=0.70,    # Mais dados como incorretos
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
            ("Microsoft", "Microsoft Corporation"),
            ("BASF", "Petrobras"),  # Deve ser negativo
            ("Apple", "Samsung")    # Deve ser negativo
        ]
        
        for text_a, text_b in test_cases:
            result = trainer.predict_match(text_a, text_b)
            match_status = "✅ MATCH" if result['match'] else "❌ NO MATCH"
            logger.info(f"'{text_a}' vs '{text_b}': {match_status} (confiança: {result['confidence']:.3f})")
        
        # Mostrar estatísticas finais
        final_report = results['final_report']
        logger.info("\n📊 Estatísticas Finais:")
        logger.info(f"  Total de registros: {final_report['data_summary']['total_records']:,}")
        logger.info(f"  Dados rotulados: {final_report['data_summary']['labeled_records']:,}")
        logger.info(f"  Matches positivos: {final_report['data_summary']['positive_matches']:,}")
        logger.info(f"  Matches negativos: {final_report['data_summary']['negative_matches']:,}")
        logger.info(f"  Precisam revisão: {final_report['data_summary']['needs_review']:,}")
        
        logger.info("\n🎯 Performance do Modelo:")
        eval_metrics = final_report['evaluation_results']
        logger.info(f"  Acurácia: {eval_metrics['accuracy']:.4f}")
        logger.info(f"  Precisão: {eval_metrics['precision']:.4f}")
        logger.info(f"  Recall: {eval_metrics['recall']:.4f}")
        logger.info(f"  F1-Score: {eval_metrics['f1']:.4f}")
        
        logger.info(f"\n📄 Relatório completo: models/company_matcher/final_training_report.json")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        logger.info("\n📋 Opções alternativas:")
        logger.info("1. Verificar se os dados estão em '../results'")
        logger.info("2. Ajustar thresholds se poucos dados rotulados")
        logger.info("3. Usar interface Streamlit para rotulação manual")
        
        # Opção 2: Apenas carregar e preparar dados (para debug)
        logger.info("\n🔍 Tentando apenas carregar dados...")
        try:
            training_data = trainer.load_latest_gerem_data(
                high_threshold=0.95,
                low_threshold=0.70
            )
            logger.info(f"Dados carregados: {len(training_data)} registros")
            
            # Mostrar estatísticas
            labeled_data = training_data[training_data['label'] != -1]
            logger.info(f"Dados rotulados: {len(labeled_data)}")
            logger.info(f"Matches positivos: {len(training_data[training_data['label'] == 1])}")
            logger.info(f"Matches negativos: {len(training_data[training_data['label'] == 0])}")
            logger.info(f"Precisam revisão: {len(training_data[training_data['label'] == -1])}")
            
            if len(labeled_data) < 100:
                logger.warning("⚠️ Poucos dados rotulados para treinamento!")
                logger.info("💡 Sugestões:")
                logger.info("  - Reduzir high_threshold para 0.90")
                logger.info("  - Reduzir low_threshold para 0.65")
                logger.info("  - Usar interface Streamlit para rotular manualmente")
            
        except Exception as e2:
            logger.error(f"Erro ao carregar dados: {e2}")
            logger.info("Verifique se os diretórios de resultados existem e contêm dados válidos.")

if __name__ == "__main__":
    main()
