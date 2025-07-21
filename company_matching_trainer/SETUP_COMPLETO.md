# 🚀 Company Matching Trainer - Setup Completo

## ✅ Status: Sistema Configurado e Pronto para Uso

O sistema foi configurado com sucesso para usar os dados de embeddings mais recentes do GEREM. Todos os componentes estão funcionando corretamente.

## 📊 Dados Carregados

- **Total de registros**: 276.036
- **Fontes de dados**:
  - gerem_prospecoes: 184.195 registros
  - gerem_negociacoes: 67.531 registros  
  - gerem_projetos: 24.310 registros
- **Estatísticas de similaridade**:
  - Média: 0.732
  - Mínima: 0.650
  - Máxima: 1.000

## 🎯 Como Usar

### 1. Treinamento Rápido (Recomendado)

```bash
cd company_matching_trainer
python3 run_training.py
```

Este script:
- Carrega automaticamente os dados mais recentes
- Configura thresholds otimizados (high=0.95, low=0.70)
- Treina o modelo transformer
- Avalia a performance
- Testa com exemplos práticos

### 2. Teste de Carregamento de Dados

```bash
cd company_matching_trainer
python3 test_data_loading.py
```

Para verificar se os dados estão sendo carregados corretamente.

### 3. Treinamento Personalizado

```python
from company_matching_trainer import CompanyMatchingTrainer

# Inicializar
trainer = CompanyMatchingTrainer()

# Pipeline completo com configurações personalizadas
results = trainer.run_complete_training_pipeline(
    high_threshold=0.95,  # Ajustar conforme necessário
    low_threshold=0.70,   # Ajustar conforme necessário
    num_epochs=3,
    batch_size=16,
    learning_rate=2e-5
)
```

## 📁 Arquivos Principais

- **`company_matching_trainer.py`**: Core do sistema de treinamento
- **`data_loader_enhanced.py`**: Carregador otimizado para dados do GEREM
- **`run_training.py`**: Script principal para execução
- **`test_data_loading.py`**: Teste de carregamento de dados

## ⚙️ Configurações Otimizadas

Baseado na análise dos dados disponíveis:

```python
# Thresholds otimizados
high_threshold = 0.95  # Matches com similaridade ≥ 0.95 = corretos
low_threshold = 0.70   # Matches com similaridade ≤ 0.70 = incorretos
# Entre 0.70-0.95 = precisam revisão manual

# Parâmetros de treinamento
num_epochs = 3
batch_size = 16
learning_rate = 2e-5
```

## 🎯 Resultados Esperados

Com os thresholds otimizados, você deve ter:
- **Matches corretos**: ~1.000-2.000 exemplos
- **Matches incorretos**: ~50.000-100.000 exemplos
- **Precisam revisão**: ~170.000-220.000 exemplos

## 📈 Próximos Passos

### 1. Após o Primeiro Treinamento

1. Verificar métricas de performance
2. Testar com casos reais
3. Ajustar thresholds se necessário

### 2. Melhorias Contínuas

1. **Rotulação Manual**: Use `streamlit_labeler.py` para rotular casos duvidosos
2. **Retreinamento**: Execute mensalmente com novos dados
3. **Integração**: Use `integration_script.py` para integrar ao sistema GEREM

### 3. Monitoramento

- Acompanhar acurácia em produção
- Coletar feedback dos usuários
- Ajustar modelo conforme necessário

## 🔧 Troubleshooting

### Problema: Poucos dados rotulados
```python
# Reduzir thresholds
high_threshold = 0.90
low_threshold = 0.65
```

### Problema: Modelo não converge
```python
# Ajustar parâmetros
num_epochs = 5
batch_size = 8
learning_rate = 3e-5
```

### Problema: Erro de memória
```python
# Reduzir batch size
batch_size = 4
```

## 📊 Estrutura de Dados

Os dados são automaticamente padronizados para:

```python
{
    'source_text': str,      # Texto da empresa no GEREM
    'target_text': str,      # Texto da empresa na base comparada
    'similarity': float,     # Score de similaridade (0-1)
    'source_type': str,      # Fonte dos dados
    'label': int,           # 0=incorreto, 1=correto, -1=revisar
    'confidence': str       # 'high' ou 'needs_review'
}
```

## 🎉 Sistema Pronto!

O sistema está completamente configurado e pronto para uso. Execute `python3 run_training.py` para começar o treinamento com os dados mais recentes do GEREM.

---

**Desenvolvido para otimizar o sistema GEREM de matching de empresas** 🚀
