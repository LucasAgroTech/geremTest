#!/usr/bin/env python3
"""
Demo Completo do Workflow de Treinamento
========================================

Script que demonstra como usar o projeto completo de treinamento
do modelo de matching de empresas.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

def create_sample_data():
    """Cria dados de exemplo para demonstração"""
    
    print("🔧 Criando dados de exemplo...")
    
    # Dados de exemplo baseados no seu sistema GEREM
    sample_data = {
        'source_text': [
            'BASF',
            'Petrobras',
            'Vale S.A.',
            'Embraer',
            'JBS S.A.',
            'Banco do Brasil',
            'Itaú Unibanco',
            'Magazine Luiza',
            'Ambev',
            'Weg S.A.',
            'CSN',
            'Gerdau',
            'Suzano',
            'Klabin',
            'CCR',
            'Localiza',
            'B3',
            'StoneCo',
            'XP Inc.',
            'Natura'
        ],
        'target_text': [
            'BASF S.A.',
            'Petróleo Brasileiro S.A.',
            'Vale',
            'Embraer S.A.',
            'JBS',
            'Banco do Brasil S.A.',
            'Itaú Unibanco Holding S.A.',
            'Magazine Luiza S.A.',
            'Ambev S.A.',
            'WEG',
            'Companhia Siderúrgica Nacional',
            'Gerdau S.A.',
            'Suzano S.A.',
            'Klabin S.A.',
            'CCR S.A.',
            'Localiza Rent a Car',
            'B3 S.A.',
            'Stone Pagamentos',
            'XP Investimentos',
            'Natura &Co'
        ]
    }
    
    # Adicionar matches incorretos para treinar o modelo
    incorrect_matches = {
        'source_text': [
            'BASF', 'Petrobras', 'Vale S.A.', 'Embraer', 'JBS S.A.',
            'Banco do Brasil', 'Itaú Unibanco', 'Magazine Luiza', 'Ambev', 'Weg S.A.'
        ],
        'target_text': [
            'Vale', 'BASF S.A.', 'Petróleo Brasileiro S.A.', 'JBS', 'Embraer S.A.',
            'Itaú Unibanco Holding S.A.', 'Banco do Brasil S.A.', 'Ambev S.A.', 'Magazine Luiza S.A.', 'Suzano S.A.'
        ]
    }
    
    # Combinar dados corretos e incorretos
    all_source = sample_data['source_text'] + incorrect_matches['source_text']
    all_target = sample_data['target_text'] + incorrect_matches['target_text']
    
    # Simular similaridades
    np.random.seed(42)
    correct_similarities = np.random.uniform(0.85, 0.98, len(sample_data['source_text']))
    incorrect_similarities = np.random.uniform(0.25, 0.65, len(incorrect_matches['source_text']))
    
    all_similarities = np.concatenate([correct_similarities, incorrect_similarities])
    
    # Criar DataFrame
    df = pd.DataFrame({
        'source_text': all_source,
        'target_text': all_target,
        'similarity': all_similarities
    })
    
    # Salvar dados de exemplo
    sample_file = 'data/sample_matching_results.csv'
    os.makedirs('data', exist_ok=True)
    df.to_csv(sample_file, index=False)
    
    print(f"✅ Dados de exemplo criados: {sample_file}")
    print(f"   - Total de registros: {len(df)}")
    print(f"   - Similaridade média: {df['similarity'].mean():.3f}")
    
    return sample_file

def demo_complete_workflow():
    """Demonstra o workflow completo do projeto"""
    
    print("🚀 DEMO: Workflow Completo de Treinamento de Modelo")
    print("=" * 60)
    
    # 1. Criar dados de exemplo
    sample_file = create_sample_data()
    
    # 2. Demonstrar carregamento e preparação
    print("\n📊 Carregando e preparando dados...")
    
    try:
        from company_matching_trainer import CompanyMatchingTrainer
        
        # Inicializar trainer
        trainer = CompanyMatchingTrainer()
        
        # Carregar dados
        df = trainer.load_matching_results(sample_file)
        print(f"✅ Carregados {len(df)} registros")
        
        # Criar dados de treinamento
        training_df = trainer.create_training_data(df)
        print(f"✅ Dados de treinamento preparados")
        
        # Mostrar estatísticas
        labeled_count = len(training_df[training_df['label'] != -1])
        correct_count = len(training_df[training_df['label'] == 1])
        incorrect_count = len(training_df[training_df['label'] == 0])
        needs_review = len(training_df[training_df['label'] == -1])
        
        print(f"   - Registros rotulados automaticamente: {labeled_count}")
        print(f"   - Marcados como corretos: {correct_count}")
        print(f"   - Marcados como incorretos: {incorrect_count}")
        print(f"   - Necessitam revisão manual: {needs_review}")
        
        # 3. Preparar datasets (se houver dados rotulados suficientes)
        if labeled_count >= 10:
            print("\n🎯 Preparando datasets para treinamento...")
            
            try:
                train_dataset, val_dataset, test_dataset = trainer.prepare_datasets(training_df)
                print(f"✅ Datasets preparados:")
                print(f"   - Treino: {len(train_dataset)} exemplos")
                print(f"   - Validação: {len(val_dataset)} exemplos") 
                print(f"   - Teste: {len(test_dataset)} exemplos")
                
                # 4. Treinar modelo (versão simplificada para demo)
                print("\n🤖 Iniciando treinamento do modelo...")
                print("   (Para demo completa, descomente as linhas de treinamento)")
                
                # Treinamento real (descomente para executar)
                # train_result = trainer.train_model(
                #     train_dataset, val_dataset,
                #     num_epochs=1,  # Reduzido para demo
                #     batch_size=8   # Reduzido para demo
                # )
                # print("✅ Modelo treinado!")
                
                # eval_result = trainer.evaluate_model(test_dataset)
                # print("✅ Modelo avaliado!")
                
                print("   ⏭️ Pulando treinamento real para demo...")
                
            except Exception as e:
                print(f"⚠️ Erro na preparação de datasets: {e}")
                print("   Pode ser necessário mais dados rotulados")
        
        else:
            print(f"⚠️ Poucos dados rotulados ({labeled_count}). Mínimo recomendado: 100")
            print("   Use a interface de rotulação para adicionar mais exemplos")
        
        # 5. Demonstrar uso da interface de rotulação
        print("\n🏷️ Interface de Rotulação:")
        print("   Execute: streamlit run streamlit_labeler.py")
        print("   - Carregue o arquivo: data/training_data_for_review.csv")
        print("   - Rotule os casos duvidosos manualmente")
        print("   - Salve os dados rotulados")
        
        # 6. Demonstrar integração
        print("\n🔗 Integração com Sistema Existente:")
        print("   1. Treine o modelo com dados suficientes")
        print("   2. Use o integration_script.py")
        print("   3. Adicione ao matching_algorithms.py do seu sistema GEREM")
        
        # 7. Criar exemplo de predição
        print("\n🎯 Exemplo de Predição:")
        print("   Após o treinamento, você pode usar:")
        print("   ```python")
        print("   from integration_script import CustomMatchingAlgorithm")
        print("   ")
        print("   algo = CustomMatchingAlgorithm('models/company_matcher')")
        print("   result = algo.predict_single('BASF', 'BASF S.A.')")
        print("   print(f'Match: {result[\"is_match\"]}, Confidence: {result[\"confidence\"]:.3f}')")
        print("   ```")
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("   Instale as dependências: pip install -r requirements.txt")
    
    except Exception as e:
        print(f"❌ Erro durante demo: {e}")

def create_project_structure():
    """Cria a estrutura de diretórios do projeto"""
    
    print("📁 Criando estrutura do projeto...")
    
    directories = [
        'data',
        'models', 
        'results',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Criado diretório: {directory}/")

def generate_project_files():
    """Gera todos os arquivos necessários do projeto"""
    
    print("📄 Gerando arquivos do projeto...")
    
    # Config.yaml
    config_content = """# Configuração do Projeto
model:
  name: "neuralmind/bert-base-portuguese-cased"
  max_length: 128
  num_labels: 2

training:
  batch_size: 16
  learning_rate: 2e-5
  num_epochs: 3
  weight_decay: 0.01
  
data:
  test_size: 0.2
  val_size: 0.1
  auto_labeling:
    high_similarity_threshold: 0.9
    low_similarity_threshold: 0.5

thresholds:
  default: 0.7
  conservative: 0.8
  liberal: 0.6
"""
    
    # Requirements.txt  
    requirements_content = """torch>=1.13.0
transformers>=4.21.0
datasets>=2.0.0
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.1.0
streamlit>=1.25.0
plotly>=5.15.0
tqdm>=4.64.0
PyYAML>=6.0
safetensors>=0.3.0
"""
    
    # Criar arquivos
    files = {
        'config.yaml': config_content,
        'requirements.txt': requirements_content
    }
    
    for filename, content in files.items():
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Criado: {filename}")

def show_next_steps():
    """Mostra os próximos passos para o usuário"""
    
    print("\n" + "=" * 60)
    print("🎯 PRÓXIMOS PASSOS")
    print("=" * 60)
    
    steps = [
        "1. 📦 Instalar dependências:",
        "   pip install -r requirements.txt",
        "",
        "2. 📊 Preparar seus dados reais:",
        "   - Exporte resultados do seu sistema GEREM atual",
        "   - Use arquivos .xlsx ou .csv com colunas: source_text, target_text, similarity",
        "",
        "3. 🏷️ Rotular dados:",
        "   streamlit run streamlit_labeler.py",
        "   - Carregue seus dados de resultado", 
        "   - Rotule matches como corretos/incorretos",
        "   - Salve os dados rotulados",
        "",
        "4. 🎯 Treinar modelo:",
        "   python company_matching_trainer.py",
        "   - Ou use o pipeline automático:",
        "   python training_pipeline.py --input seus_dados.csv",
        "",
        "5. 🔗 Integrar no sistema GEREM:",
        "   - Copie o integration_script.py para seu projeto GEREM",
        "   - Adicione o código de integração ao matching_algorithms.py",
        "   - Configure o novo algoritmo no config.py",
        "",
        "6. 📈 Monitorar e melhorar:",
        "   - Avalie a performance em dados reais",
        "   - Colete mais exemplos de treino",
        "   - Retreine periodicamente"
    ]
    
    for step in steps:
        print(step)

def main():
    """Função principal que executa todo o setup"""
    
    print("🚀 SETUP COMPLETO: Company Matching Model Trainer")
    print("=" * 60)
    
    # 1. Criar estrutura
    create_project_structure()
    
    # 2. Gerar arquivos
    generate_project_files()
    
    # 3. Executar demo
    demo_complete_workflow()
    
    # 4. Mostrar próximos passos
    show_next_steps()
    
    print("\n✅ Setup completo! Projeto pronto para uso.")

if __name__ == "__main__":
    main()