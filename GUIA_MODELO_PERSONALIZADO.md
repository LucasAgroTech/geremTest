# Guia do Modelo Personalizado - Sistema GEREM

## 🎯 Visão Geral

Você treinou com sucesso um modelo personalizado com **99.50% de acurácia** e **99.25% de F1-Score**! Este guia mostra como usar esse modelo no sistema principal para gerar novos matches de embeddings.

## 📋 Arquivos Criados

### 1. Configuração
- `config_custom_model.yaml` - Configuração específica para usar seu modelo treinado

### 2. Integração
- `custom_model_integration.py` - Módulo que integra seu modelo ao sistema
- `matching_algorithms.py` - Modificado para incluir o algoritmo personalizado
- `main.py` - Atualizado para suportar o modelo personalizado

### 3. Teste
- `test_custom_model.py` - Script para testar a integração

## 🚀 Como Usar Seu Modelo

### Opção 1: Teste Rápido
```bash
# Testar se tudo está funcionando
python test_custom_model.py
```

### Opção 2: Executar Matching Completo
```bash
# Usar apenas seu modelo personalizado para prospecções
python main.py --config config_custom_model.yaml --mode prospecoes

# Usar para negociações
python main.py --config config_custom_model.yaml --mode negociacoes

# Usar para projetos
python main.py --config config_custom_model.yaml --mode projetos

# Executar todos os tipos de matching
python main.py --config config_custom_model.yaml --mode all
```

### Opção 3: Configuração Personalizada
Você pode modificar o arquivo `config_custom_model.yaml` para ajustar:

```yaml
matching:
  algorithms:
    custom_trained:
      enabled: true
      threshold: 0.75  # Ajuste conforme necessário (0.7-0.9)
      model_path: company_matching_trainer/models/manual_validated_matcher
      batch_size: 32   # Aumente para mais velocidade (se tiver RAM)
      max_length: 128  # Tamanho máximo do texto
```

## 📊 Vantagens do Seu Modelo

### Comparação com Algoritmos Tradicionais:

| Algoritmo | Acurácia Típica | Seu Modelo |
|-----------|----------------|------------|
| Levenshtein | ~70-80% | **99.50%** |
| Jaro-Winkler | ~75-85% | **99.50%** |
| Embeddings Padrão | ~80-90% | **99.50%** |

### Benefícios:
- ✅ **Alta Precisão**: 99.50% de acurácia
- ✅ **Treinado Especificamente**: Para seus dados de empresas
- ✅ **Otimizado**: Para o contexto brasileiro
- ✅ **Validado Manualmente**: Com dados reais do sistema

## 🔧 Configurações Recomendadas

### Para Máxima Precisão:
```yaml
threshold: 0.80  # Mais restritivo, menos falsos positivos
```

### Para Máxima Cobertura:
```yaml
threshold: 0.70  # Menos restritivo, mais matches
```

### Para Balanceamento:
```yaml
threshold: 0.75  # Configuração padrão recomendada
```

## 📈 Monitoramento de Performance

### Logs do Sistema
O sistema irá mostrar:
```
🚀 Iniciando matching com modelo personalizado treinado
   - Origem: X registros
   - Destino: Y registros
   - Threshold: 0.75
🧠 Gerando embeddings...
🔍 Processando Z comparações...
✅ Matching concluído:
   - Comparações realizadas: Z
   - Matches encontrados: N
   - Similaridade média: 0.XXX
```

### Arquivos de Resultado
Os resultados serão salvos em:
- `results/gerem_[tipo]/[timestamp]/custom_trained_matches.xlsx`
- `results/gerem_[tipo]/[timestamp]/best_matches.xlsx` (se for o melhor algoritmo)

## 🛠️ Solução de Problemas

### Erro: "Modelo personalizado não disponível"
```bash
# Verificar se o modelo existe
ls -la company_matching_trainer/models/manual_validated_matcher/

# Se não existir, execute o treinamento novamente
cd company_matching_trainer
python run_training.py
```

### Erro: "Erro ao carregar modelo"
```bash
# Verificar dependências
pip install torch transformers safetensors

# Testar carregamento
python test_custom_model.py
```

### Performance Lenta
```yaml
# Reduzir batch_size se estiver com pouca RAM
batch_size: 16

# Ou aumentar se tiver RAM suficiente
batch_size: 64
```

## 📝 Exemplos de Uso

### Exemplo 1: Matching Simples
```python
from matching_algorithms import MatchingAlgorithms
import pandas as pd

# Configurar algoritmos
config = {
    'custom_trained': {
        'enabled': True,
        'threshold': 0.75,
        'model_path': 'company_matching_trainer/models/manual_validated_matcher'
    }
}

matcher = MatchingAlgorithms(config)

# Dados de exemplo
source_df = pd.DataFrame({'empresa': ['BASF', 'Petrobras']})
target_df = pd.DataFrame({'nome': ['BASF S.A.', 'Petróleo Brasileiro']})

# Executar matching
results = matcher.custom_trained_matching(
    source_df, target_df, 'empresa', 'nome'
)

print(f"Encontrados {len(results)} matches")
```

### Exemplo 2: Com Filtro de Data
```python
# Dados com datas
source_df = pd.DataFrame({
    'empresa': ['BASF', 'Petrobras'],
    'data_interacao': ['2024-01-01', '2024-02-01']
})

target_df = pd.DataFrame({
    'nome': ['BASF S.A.', 'Petróleo Brasileiro'],
    'data_prospeccao': ['2024-01-15', '2024-02-15']
})

# Matching com filtro de data
results = matcher.custom_trained_matching(
    source_df, target_df, 'empresa', 'nome', 
    ('data_interacao', 'data_prospeccao')
)
```

## 🎯 Próximos Passos

1. **Teste a Integração**:
   ```bash
   python test_custom_model.py
   ```

2. **Execute um Matching de Teste**:
   ```bash
   python main.py --config config_custom_model.yaml --mode prospecoes
   ```

3. **Analise os Resultados**:
   - Verifique os arquivos em `results/`
   - Compare com algoritmos anteriores
   - Ajuste o threshold se necessário

4. **Produção**:
   - Use a configuração otimizada
   - Monitore a performance
   - Documente os resultados

## 📞 Suporte

Se encontrar problemas:

1. Execute o teste: `python test_custom_model.py`
2. Verifique os logs do sistema
3. Consulte este guia
4. Verifique se todas as dependências estão instaladas

## 🏆 Parabéns!

Você agora tem um sistema de matching de empresas com **99.50% de acurácia** integrado ao seu pipeline principal. Isso representa uma melhoria significativa sobre os algoritmos tradicionais!

---

**Modelo Treinado**: `company_matching_trainer/models/manual_validated_matcher/`  
**Acurácia**: 99.50%  
**F1-Score**: 99.25%  
**Data de Treinamento**: 18/07/2025
