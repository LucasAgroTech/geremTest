#!/usr/bin/env python3
"""
Teste Final do Sistema Otimizado
===============================

Este script testa o sistema principal com as otimizações aplicadas para evitar travamentos.
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_data():
    """Cria dados de teste realistas para simular o problema original"""
    
    logger.info("📊 Criando dados de teste realistas...")
    
    # Dados GEREM (origem) - simulando interações
    gerem_companies = [
        'BASF S.A.', 'Petróleo Brasileiro S.A.', 'Vale S.A.', 'Embraer S.A.',
        'JBS S.A.', 'Suzano S.A.', 'Gerdau S.A.', 'CSN S.A.',
        'Braskem S.A.', 'Klabin S.A.', 'Ultrapar S.A.', 'Copel S.A.',
        'Cemig S.A.', 'Eletrobras S.A.', 'Sabesp S.A.', 'Telefônica Brasil S.A.'
    ]
    
    gerem_data = []
    for i, company in enumerate(gerem_companies):
        for j in range(50):  # 50 interações por empresa
            gerem_data.append({
                'nome_empresa': f"{company} - Interação {j+1}",
                'data_interacao': f"2024-{(i % 12) + 1:02d}-{(j % 28) + 1:02d}",
                'id_prospeccao': f"GEREM_{i}_{j}"
            })
    
    # Dados de Negociações (destino) - simulando negociações posteriores
    negociacoes_data = []
    neg_companies = [
        'BASF Química Ltda.', 'Petrobras Distribuidora S.A.', 'Vale Mineração S.A.', 'Embraer Defesa S.A.',
        'JBS Foods S.A.', 'Suzano Papel S.A.', 'Gerdau Aços S.A.', 'CSN Mineração S.A.',
        'Braskem Petroquímica S.A.', 'Klabin Papéis S.A.', 'Ultrapar Energia S.A.', 'Copel Energia S.A.',
        'Cemig Distribuição S.A.', 'Eletrobras Energia S.A.', 'Sabesp Saneamento S.A.', 'Telefônica Móvel S.A.'
    ]
    
    for i, company in enumerate(neg_companies):
        for j in range(75):  # 75 negociações por empresa
            negociacoes_data.append({
                'razao_social': f"{company} - Negociação {j+1}",
                'data_prim_ver_prop_tec': f"2024-{(i % 12) + 1:02d}-{((j % 28) + 15):02d}",  # Datas posteriores
                'codigo_negociacao': f"NEG_{i}_{j}",
                'cnpj': f"{i:02d}.{j:03d}.{(i+j):03d}/0001-{(i*j) % 100:02d}"
            })
    
    gerem_df = pd.DataFrame(gerem_data)
    negociacoes_df = pd.DataFrame(negociacoes_data)
    
    logger.info(f"   - GEREM: {len(gerem_df)} registros")
    logger.info(f"   - Negociações: {len(negociacoes_df)} registros")
    logger.info(f"   - Comparações potenciais: {len(gerem_df) * len(negociacoes_df):,}")
    
    return gerem_df, negociacoes_df

def test_optimized_custom_model():
    """Testa o modelo personalizado otimizado"""
    
    logger.info("=== TESTE DO MODELO PERSONALIZADO OTIMIZADO ===")
    
    try:
        # Importar componentes do sistema
        from matching_algorithms import MatchingAlgorithms
        from config import load_config
        
        # Carregar configuração otimizada
        config = load_config('config_custom_model.yaml')
        
        # Criar dados de teste
        gerem_df, negociacoes_df = create_test_data()
        
        # Inicializar algoritmos de matching
        logger.info("🔧 Inicializando algoritmos de matching...")
        matcher = MatchingAlgorithms(config['matching'])
        
        # Configurar colunas para matching
        source_col = 'nome_empresa'
        target_col = 'razao_social'
        date_cols = ('data_interacao', 'data_prim_ver_prop_tec')
        
        # Executar matching com modelo personalizado
        logger.info("🚀 Executando matching com modelo personalizado otimizado...")
        start_time = time.time()
        
        results = matcher.custom_trained_matching(
            gerem_df, negociacoes_df, source_col, target_col, date_cols
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Analisar resultados
        logger.info(f"✅ Matching concluído em {execution_time:.1f}s!")
        logger.info(f"   - Matches encontrados: {len(results):,}")
        
        if not results.empty:
            logger.info(f"   - Similaridade média: {results['similarity'].mean():.3f}")
            logger.info(f"   - Similaridade máxima: {results['similarity'].max():.3f}")
            logger.info(f"   - Similaridade mínima: {results['similarity'].min():.3f}")
            
            # Mostrar top 10 matches
            logger.info("🏆 Top 10 matches:")
            for idx, row in results.head(10).iterrows():
                logger.info(f"   {row['source_text'][:50]}... → {row['target_text'][:50]}... ({row['similarity']:.3f})")
            
            # Salvar resultados
            output_file = f"test_final_custom_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            results.to_excel(output_file, index=False)
            logger.info(f"💾 Resultados salvos em: {output_file}")
            
            # Verificar se não houve travamento
            if execution_time < 300:  # Menos de 5 minutos
                logger.info("✅ SUCESSO: Não houve travamento!")
                return True
            else:
                logger.warning("⚠️ Execução demorou mais que o esperado")
                return False
        else:
            logger.warning("⚠️ Nenhum match encontrado")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_system_integration():
    """Testa a integração completa do sistema"""
    
    logger.info("=== TESTE DE INTEGRAÇÃO COMPLETA ===")
    
    try:
        # Testar importações
        logger.info("1. Testando importações...")
        from matching_algorithms import MatchingAlgorithms, CUSTOM_MODEL_AVAILABLE
        from custom_model_integration import CustomTrainedMatcher
        from config import load_config
        
        if CUSTOM_MODEL_AVAILABLE:
            logger.info("✅ Modelo personalizado disponível")
        else:
            logger.error("❌ Modelo personalizado não disponível")
            return False
        
        # Testar carregamento de configuração
        logger.info("2. Testando carregamento de configuração...")
        config = load_config('config_custom_model.yaml')
        logger.info("✅ Configuração carregada")
        
        # Testar inicialização de componentes
        logger.info("3. Testando inicialização de componentes...")
        matcher = MatchingAlgorithms(config['matching'])
        logger.info("✅ MatchingAlgorithms inicializado")
        
        # Testar carregamento do modelo personalizado
        logger.info("4. Testando carregamento do modelo personalizado...")
        matcher._load_custom_matcher()
        logger.info("✅ Modelo personalizado carregado")
        
        # Testar com dados pequenos
        logger.info("5. Testando com dados pequenos...")
        small_gerem = pd.DataFrame({
            'nome_empresa': ['BASF S.A.', 'Petrobras S.A.'],
            'data_interacao': ['2024-01-01', '2024-02-01']
        })
        
        small_neg = pd.DataFrame({
            'razao_social': ['BASF Química Ltda.', 'Petrobras Distribuidora S.A.'],
            'data_prim_ver_prop_tec': ['2024-01-15', '2024-02-15']
        })
        
        small_results = matcher.custom_trained_matching(
            small_gerem, small_neg, 'nome_empresa', 'razao_social', 
            ('data_interacao', 'data_prim_ver_prop_tec')
        )
        
        logger.info(f"✅ Teste pequeno concluído: {len(small_results)} matches")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na integração: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal"""
    
    logger.info("🚀 Iniciando teste final do sistema otimizado...")
    logger.info("="*60)
    
    # Teste 1: Integração do sistema
    logger.info("TESTE 1: Integração do Sistema")
    integration_success = test_system_integration()
    
    if not integration_success:
        logger.error("❌ Falha na integração do sistema")
        return False
    
    logger.info("✅ Integração do sistema OK")
    logger.info("")
    
    # Teste 2: Modelo personalizado otimizado
    logger.info("TESTE 2: Modelo Personalizado Otimizado")
    model_success = test_optimized_custom_model()
    
    if not model_success:
        logger.error("❌ Falha no teste do modelo personalizado")
        return False
    
    logger.info("✅ Modelo personalizado OK")
    logger.info("")
    
    # Resumo final
    logger.info("="*60)
    logger.info("🎉 TODOS OS TESTES PASSARAM!")
    logger.info("")
    logger.info("📋 RESUMO DAS OTIMIZAÇÕES APLICADAS:")
    logger.info("1. ✅ Filtro de data aplicado ANTES dos embeddings")
    logger.info("2. ✅ Processamento em lotes pequenos (2000 comparações)")
    logger.info("3. ✅ Limite de segurança (20.000 comparações máximas)")
    logger.info("4. ✅ Salvamento de resultados parciais")
    logger.info("5. ✅ Limpeza de memória otimizada")
    logger.info("6. ✅ Batch size reduzido (16 em vez de 32)")
    logger.info("7. ✅ Modo memory_efficient habilitado")
    logger.info("")
    logger.info("🚀 SISTEMA PRONTO PARA USO EM PRODUÇÃO!")
    logger.info("")
    logger.info("📝 COMANDOS PARA EXECUTAR:")
    logger.info("   python main.py --config config_custom_model.yaml --mode negociacoes")
    logger.info("   python main.py --config config_custom_model.yaml --mode prospecoes")
    logger.info("   python main.py --config config_custom_model.yaml --mode projetos")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("\n✅ Teste final concluído com SUCESSO!")
        sys.exit(0)
    else:
        logger.error("\n❌ Teste final FALHOU!")
        sys.exit(1)
