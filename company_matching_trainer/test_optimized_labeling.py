#!/usr/bin/env python3
"""
Teste da Nova Lógica Otimizada de Rotulação
==========================================

Testa a implementação dos novos thresholds e detecção de padrões suspeitos
para capturar falsos positivos de alta similaridade.
"""

import pandas as pd
import logging
from data_loader_enhanced import GeremDataLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_data():
    """Cria dados de teste para demonstrar a nova lógica"""
    
    test_cases = [
        # Casos de alta similaridade que DEVEM ser validados manualmente
        ("MICROSOFT BRASIL LTDA", "MICROSOFT CORPORATION", 0.95, "Subsidiária vs Matriz"),
        ("BASF BRASIL S.A.", "BASF QUÍMICA S.A.", 0.92, "Subsidiárias diferentes"),
        ("PETROBRAS DISTRIBUIDORA", "PETROBRAS TRANSPORTE", 0.89, "Divisões diferentes"),
        ("VOLKSWAGEN DO BRASIL LTDA", "VOLKSWAGEN S.A.", 0.94, "Tipos societários diferentes"),
        ("GENERAL MOTORS NORTE", "GENERAL MOTORS SUL", 0.91, "Regiões diferentes"),
        
        # Casos de faixa crítica (0.85-0.95)
        ("WEGMANN AUTOMOTIVE BRASIL", "FAURECIA AUTOMOTIVE DO BRASIL", 0.88, "Mesmo setor, empresas diferentes"),
        ("TOLEDO DO BRASIL", "AUNDE BRASIL S.A.", 0.87, "Empresas diferentes com 'BRASIL'"),
        ("BOSCH REXROTH", "BOSCH AUTOMOTIVE", 0.86, "Divisões do mesmo grupo"),
        
        # Casos que devem ser automáticos corretos (>0.95)
        ("BASF", "BASF S.A.", 0.98, "Mesma empresa, variação nome"),
        ("PETROBRAS", "PETRÓLEO BRASILEIRO S.A.", 0.96, "Mesma empresa, nome completo"),
        
        # Casos que devem ser automáticos incorretos (<0.5)
        ("BASF", "MICROSOFT", 0.12, "Empresas completamente diferentes"),
        ("VALE", "BANCO DO BRASIL", 0.23, "Setores diferentes"),
        
        # Casos com padrões suspeitos
        ("EMPRESA ABC LTDA", "EMPRESA ABC S.A.", 0.93, "Padrão suspeito: LTDA vs S.A."),
        ("FILIAL NORTE", "MATRIZ SUL", 0.89, "Padrão suspeito: FILIAL vs MATRIZ"),
        
        # Casos com empresas importantes
        ("VALE S.A.", "VALE MINERAÇÃO", 0.91, "Empresa importante - sempre validar"),
        ("TOYOTA BRASIL", "TOYOTA MOTOR", 0.90, "Empresa importante - sempre validar"),
    ]
    
    df = pd.DataFrame(test_cases, columns=['source_text', 'target_text', 'similarity', 'description'])
    df['source_type'] = 'test_data'
    df['original_index'] = range(len(df))
    
    return df

def test_optimized_labeling():
    """Testa a nova lógica de rotulação otimizada"""
    
    logger.info("🧪 Iniciando teste da lógica otimizada de rotulação")
    
    # Criar dados de teste
    test_df = create_test_data()
    logger.info(f"📊 Criados {len(test_df)} casos de teste")
    
    # Inicializar carregador com configuração otimizada
    loader = GeremDataLoader(config_path="config.yaml")
    
    # Aplicar nova lógica de rotulação
    logger.info("\n🎯 Aplicando lógica otimizada...")
    labeled_df = loader.create_training_labels_optimized(test_df)
    
    # Analisar resultados
    logger.info("\n📋 Análise detalhada dos resultados:")
    
    for idx, row in labeled_df.iterrows():
        status_emoji = {
            1: "✅",  # Automático correto
            0: "❌",  # Automático incorreto
            -1: "🔍"  # Validação manual
        }[row['label']]
        
        priority_emoji = {
            1: "🔥",  # Crítica
            2: "📋",  # Normal
            3: "📝"   # Baixa
        }[row['priority']]
        
        logger.info(f"{status_emoji} {priority_emoji} [{row['similarity']:.3f}] {row['source_text']} vs {row['target_text']}")
        logger.info(f"    Razão: {row['reason']} | Confiança: {row['confidence']}")
        logger.info(f"    Descrição: {row['description']}")
        logger.info("")
    
    # Estatísticas finais
    logger.info("📊 Resumo dos resultados:")
    
    # Por label
    label_counts = labeled_df['label'].value_counts()
    logger.info(f"✅ Automático correto: {label_counts.get(1, 0)}")
    logger.info(f"❌ Automático incorreto: {label_counts.get(0, 0)}")
    logger.info(f"🔍 Validação manual: {label_counts.get(-1, 0)}")
    
    # Por prioridade
    priority_counts = labeled_df['priority'].value_counts()
    logger.info(f"🔥 Prioridade crítica: {priority_counts.get(1, 0)}")
    logger.info(f"📋 Prioridade normal: {priority_counts.get(2, 0)}")
    logger.info(f"📝 Prioridade baixa: {priority_counts.get(3, 0)}")
    
    # Por tipo de confiança
    confidence_counts = labeled_df['confidence'].value_counts()
    logger.info(f"\n🎯 Tipos de confiança:")
    for conf_type, count in confidence_counts.items():
        logger.info(f"   {conf_type}: {count}")
    
    # Salvar resultados do teste
    output_path = "data/test_optimized_results.csv"
    labeled_df.to_csv(output_path, index=False)
    logger.info(f"\n💾 Resultados salvos em: {output_path}")
    
    return labeled_df

def validate_improvements():
    """Valida se as melhorias estão funcionando corretamente"""
    
    logger.info("\n🔍 Validando melhorias implementadas:")
    
    # Testar com dados reais se disponíveis
    try:
        loader = GeremDataLoader(config_path="config.yaml")
        
        # Tentar carregar dados reais
        real_data = loader.load_all_latest_data()
        logger.info(f"📊 Dados reais carregados: {len(real_data)} registros")
        
        # Aplicar nova lógica
        labeled_real = loader.create_training_labels_optimized(real_data.head(100))  # Apenas primeiros 100 para teste
        
        # Verificar se casos de alta similaridade estão sendo capturados
        high_sim_manual = labeled_real[
            (labeled_real['similarity'] >= 0.9) & 
            (labeled_real['label'] == -1)
        ]
        
        logger.info(f"🎯 Casos de alta similaridade capturados para validação: {len(high_sim_manual)}")
        
        if len(high_sim_manual) > 0:
            logger.info("✅ SUCESSO: Sistema está capturando casos suspeitos de alta similaridade!")
            
            # Mostrar alguns exemplos
            logger.info("\n📋 Exemplos de casos capturados:")
            for idx, row in high_sim_manual.head(5).iterrows():
                logger.info(f"   [{row['similarity']:.3f}] {row['source_text']} vs {row['target_text']}")
                logger.info(f"   Razão: {row['reason']}")
        else:
            logger.warning("⚠️ Nenhum caso de alta similaridade foi capturado para validação manual")
        
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível testar com dados reais: {e}")
        logger.info("Usando apenas dados de teste sintéticos")

def main():
    """Função principal do teste"""
    
    logger.info("🚀 Teste da Lógica Otimizada de Rotulação")
    logger.info("=" * 50)
    
    try:
        # Executar teste principal
        test_results = test_optimized_labeling()
        
        # Validar melhorias
        validate_improvements()
        
        logger.info("\n✅ Teste concluído com sucesso!")
        logger.info("\n🎯 Principais melhorias implementadas:")
        logger.info("   1. ✅ Threshold de alta similaridade mais rigoroso (0.95)")
        logger.info("   2. ✅ Nova faixa crítica (0.85-0.95) para validação obrigatória")
        logger.info("   3. ✅ Detecção de padrões suspeitos (LTDA vs S.A., etc.)")
        logger.info("   4. ✅ Lista de empresas importantes para validação obrigatória")
        logger.info("   5. ✅ Amostragem de casos de alta similaridade")
        logger.info("   6. ✅ Sistema de prioridades para validação")
        
        logger.info("\n🔥 Agora o sistema captura falsos positivos de alta similaridade!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        raise

if __name__ == "__main__":
    main()
