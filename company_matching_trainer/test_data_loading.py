#!/usr/bin/env python3
"""
Script de Teste para Carregamento de Dados
==========================================

Testa o carregamento dos dados de embedding mais recentes do GEREM.
"""

import sys
import logging
from pathlib import Path

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(str(Path(__file__).parent))

from data_loader_enhanced import GeremDataLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_loading():
    """Testa o carregamento de dados"""
    
    logger.info("=== Teste de Carregamento de Dados ===")
    
    try:
        # Inicializar carregador
        loader = GeremDataLoader(results_base_path="../results")
        
        # 1. Encontrar resultados mais recentes
        logger.info("1. Procurando resultados mais recentes...")
        latest_results = loader.find_latest_results()
        
        if not latest_results:
            logger.error("❌ Nenhum resultado encontrado!")
            return False
        
        logger.info("✅ Resultados encontrados:")
        for source, path in latest_results.items():
            logger.info(f"  {source}: {path}")
        
        # 2. Carregar dados de embedding
        logger.info("\n2. Carregando dados de embedding...")
        all_data = []
        
        for source_type, source_path in latest_results.items():
            logger.info(f"Carregando {source_type}...")
            df = loader.load_embedding_data(source_path)
            
            if df is not None and not df.empty:
                logger.info(f"  ✅ {len(df)} registros carregados")
                logger.info(f"  Colunas: {list(df.columns)}")
                
                # Padronizar dados
                standardized_df = loader.standardize_embedding_data(df, source_type)
                if not standardized_df.empty:
                    all_data.append(standardized_df)
                    logger.info(f"  ✅ {len(standardized_df)} registros padronizados")
                else:
                    logger.warning(f"  ⚠️ Falha na padronização de {source_type}")
            else:
                logger.warning(f"  ⚠️ Nenhum dado carregado para {source_type}")
        
        if not all_data:
            logger.error("❌ Nenhum dado válido foi carregado!")
            return False
        
        # 3. Combinar dados
        logger.info("\n3. Combinando dados...")
        import pandas as pd
        combined_df = pd.concat(all_data, ignore_index=True)
        
        logger.info(f"✅ Total combinado: {len(combined_df)} registros")
        logger.info("Distribuição por fonte:")
        for source, count in combined_df['source_type'].value_counts().items():
            logger.info(f"  {source}: {count} registros")
        
        # 4. Estatísticas de similaridade
        logger.info("\n4. Estatísticas de similaridade:")
        logger.info(f"  Média: {combined_df['similarity'].mean():.3f}")
        logger.info(f"  Mínima: {combined_df['similarity'].min():.3f}")
        logger.info(f"  Máxima: {combined_df['similarity'].max():.3f}")
        logger.info(f"  Mediana: {combined_df['similarity'].median():.3f}")
        
        # 5. Criar labels automáticos
        logger.info("\n5. Criando labels automáticos...")
        training_data = loader.create_training_labels(combined_df)
        
        # 6. Salvar dados
        logger.info("\n6. Salvando dados preparados...")
        output_path = loader.save_training_data(training_data)
        
        logger.info(f"\n✅ Teste concluído com sucesso!")
        logger.info(f"Dados salvos em: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = test_data_loading()
    
    if success:
        logger.info("\n🎉 Todos os testes passaram!")
        logger.info("O sistema está pronto para treinamento.")
    else:
        logger.error("\n💥 Falha nos testes!")
        logger.error("Verifique os logs acima para identificar problemas.")
        
        # Sugestões de solução
        logger.info("\n💡 Possíveis soluções:")
        logger.info("1. Verificar se o diretório '../results' existe")
        logger.info("2. Verificar se há arquivos 'embedding_matches.xlsx' nos subdiretórios")
        logger.info("3. Verificar se os arquivos não estão corrompidos")
        logger.info("4. Executar o sistema GEREM principal para gerar novos resultados")

if __name__ == "__main__":
    main()
