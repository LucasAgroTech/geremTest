#!/usr/bin/env python3
"""
Script de Teste para o Modelo Personalizado
==========================================

Este script testa a integração do modelo personalizado treinado com o sistema principal.
"""

import os
import sys
import pandas as pd
from pathlib import Path

def test_custom_model_integration():
    """Testa a integração do modelo personalizado"""
    
    print("=== Teste de Integração do Modelo Personalizado ===")
    print()
    
    # 1. Verificar se o modelo existe
    print("1. Verificando se o modelo treinado existe...")
    model_path = Path('company_matching_trainer/models/manual_validated_matcher')
    
    if model_path.exists():
        print("✅ Modelo encontrado!")
        print(f"📁 Caminho: {model_path}")
        
        # Listar arquivos do modelo
        model_files = list(model_path.glob('*'))
        print("📋 Arquivos do modelo:")
        for file in model_files:
            print(f"   - {file.name}")
        print()
    else:
        print("❌ Modelo não encontrado!")
        print("⚠️ Execute o treinamento primeiro antes de testar a integração.")
        return False
    
    # 2. Testar importação do módulo de integração
    print("2. Testando importação do módulo de integração...")
    try:
        from custom_model_integration import CustomTrainedMatcher
        print("✅ Módulo de integração importado com sucesso!")
    except ImportError as e:
        print(f"❌ Erro ao importar módulo de integração: {e}")
        return False
    
    # 3. Testar carregamento do modelo
    print("3. Testando carregamento do modelo...")
    try:
        matcher = CustomTrainedMatcher({
            'model_path': str(model_path),
            'custom_threshold': 0.75
        })
        print("✅ Modelo carregado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        return False
    
    # 4. Testar predição simples
    print("4. Testando predição simples...")
    try:
        # Criar dados de teste simples
        test_data = [
            ("BASF", "BASF S.A."),
            ("Petrobras", "Petróleo Brasileiro S.A."),
            ("Vale", "Vale S.A."),
            ("Empresa ABC", "Empresa XYZ")
        ]
        
        print("📊 Testando pares de empresas:")
        for text_a, text_b in test_data:
            # Criar DataFrames de teste
            source_df = pd.DataFrame({'empresa': [text_a]})
            target_df = pd.DataFrame({'nome': [text_b]})
            
            # Executar matching
            results = matcher.custom_trained_matching(
                source_df, target_df, 'empresa', 'nome'
            )
            
            similarity = results['similarity'].iloc[0] if not results.empty else 0.0
            print(f"   - '{text_a}' vs '{text_b}': {similarity:.3f}")
        
        print("✅ Predições executadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro durante predições: {e}")
        return False
    
    # 5. Testar integração com MatchingAlgorithms
    print("5. Testando integração com MatchingAlgorithms...")
    try:
        from matching_algorithms import MatchingAlgorithms
        
        # Configuração de teste
        config = {
            'custom_trained': {
                'enabled': True,
                'threshold': 0.75,
                'model_path': str(model_path),
                'batch_size': 32,
                'max_length': 128
            }
        }
        
        # Inicializar algoritmos
        algorithms = MatchingAlgorithms(config)
        
        # Verificar se o método existe
        if hasattr(algorithms, 'custom_trained_matching'):
            print("✅ Método custom_trained_matching disponível!")
            
            # Testar com dados simples
            source_df = pd.DataFrame({
                'empresa': ['BASF', 'Petrobras'],
                'data': ['2024-01-01', '2024-02-01']
            })
            target_df = pd.DataFrame({
                'nome': ['BASF S.A.', 'Petróleo Brasileiro'],
                'data': ['2024-01-15', '2024-02-15']
            })
            
            results = algorithms.custom_trained_matching(
                source_df, target_df, 'empresa', 'nome', ('data', 'data')
            )
            
            print(f"✅ Matching executado! Encontrados {len(results)} matches.")
        else:
            print("❌ Método custom_trained_matching não encontrado!")
            return False
            
    except Exception as e:
        print(f"❌ Erro na integração com MatchingAlgorithms: {e}")
        return False
    
    # 6. Verificar configuração
    print("6. Verificando arquivo de configuração...")
    config_file = Path('config_custom_model.yaml')
    if config_file.exists():
        print("✅ Arquivo de configuração encontrado!")
        print(f"📁 Caminho: {config_file}")
    else:
        print("❌ Arquivo de configuração não encontrado!")
        return False
    
    print()
    print("🎉 Todos os testes passaram! O modelo personalizado está integrado corretamente.")
    print()
    print("📋 Próximos passos:")
    print("1. Execute o sistema principal com a nova configuração:")
    print("   python main.py --config config_custom_model.yaml --mode prospecoes")
    print()
    print("2. Ou teste com um modo específico:")
    print("   python main.py --config config_custom_model.yaml --mode negociacoes")
    print()
    print("3. Para ver apenas o modelo personalizado em ação, use:")
    print("   python main.py --config config_custom_model.yaml --mode all")
    
    return True

def show_model_info():
    """Mostra informações sobre o modelo treinado"""
    
    print("=== Informações do Modelo Personalizado ===")
    print()
    
    # Verificar resultados do treinamento
    results_file = Path('company_matching_trainer/models/manual_validated_matcher/training_results.json')
    if results_file.exists():
        import json
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print("📊 Métricas do Modelo:")
            print(f"   - Acurácia: {results.get('accuracy', 'N/A')}")
            print(f"   - F1-Score: {results.get('f1', 'N/A')}")
            print(f"   - Precisão: {results.get('precision', 'N/A')}")
            print(f"   - Recall: {results.get('recall', 'N/A')}")
            print()
        except Exception as e:
            print(f"⚠️ Erro ao ler resultados do treinamento: {e}")
    
    # Verificar dados de treinamento
    training_data = Path('company_matching_trainer/data/manual_training_data.csv')
    if training_data.exists():
        try:
            df = pd.read_csv(training_data)
            print("📈 Dados de Treinamento:")
            print(f"   - Total de exemplos: {len(df):,}")
            if 'label' in df.columns:
                print(f"   - Matches positivos: {(df['label'] == 1).sum():,}")
                print(f"   - Matches negativos: {(df['label'] == 0).sum():,}")
            print()
        except Exception as e:
            print(f"⚠️ Erro ao ler dados de treinamento: {e}")
    
    print("🔧 Configuração Recomendada:")
    print("   - Threshold: 0.75 (otimizado para alta precisão)")
    print("   - Batch size: 32 (balanceado para performance)")
    print("   - Max length: 128 (adequado para nomes de empresas)")

if __name__ == "__main__":
    print("🚀 Iniciando teste de integração do modelo personalizado...")
    print()
    
    # Mostrar informações do modelo
    show_model_info()
    print()
    
    # Executar testes
    success = test_custom_model_integration()
    
    if success:
        print()
        print("✅ Integração concluída com sucesso!")
        sys.exit(0)
    else:
        print()
        print("❌ Falha na integração. Verifique os erros acima.")
        sys.exit(1)
