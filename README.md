# EMBRAPII Matching Algorithm Evaluation

Este projeto implementa uma avaliação comparativa de algoritmos de matching para relacionar dados de interações GEREM com prospecções, negociações e projetos. O sistema foi projetado para permitir testes fáceis com diferentes planilhas e avaliar qual algoritmo produz os melhores resultados.

## Algoritmos Implementados

O projeto implementa três algoritmos de matching:

1. **Levenshtein Distance otimizado**: Calcula o número mínimo de edições necessárias entre duas strings. Utilizamos `python-Levenshtein`, que é mais rápido que `fuzzywuzzy`.

2. **Jaro-Winkler**: Favorece similaridades no início da string, ideal para nomes comerciais. Implementado com `jellyfish.jaro_winkler_similarity`.

3. **Embedding de Texto (via IA)**: Transforma os nomes em vetores semânticos e calcula distância vetorial. Utilizamos `sentence-transformers`, ideal para casos mais complexos.

## Estrutura do Projeto

```
embrapii-matching/
├── data/                 # Diretório para dados locais
├── temp/                 # Arquivos temporários
├── results/              # Resultados de matching
│   ├── gerem_prospecoes/ # Resultados de matching GEREM-Prospecções
│   ├── gerem_negociacoes/ # Resultados de matching GEREM-Negociações
│   └── gerem_projetos/   # Resultados de matching GEREM-Projetos
├── logs/                 # Logs de execução
├── evaluation/           # Resultados de avaliação
├── visualization/        # Visualizações geradas
├── data_loader.py        # Carregador de dados do SharePoint
├── matching_algorithms.py # Implementação dos algoritmos
├── evaluation.py         # Métricas de avaliação
├── visualization.py      # Visualização de resultados
├── config.py             # Configurações do projeto
├── main.py               # Script principal
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```

## Requisitos

- Python 3.8 ou superior
- Bibliotecas listadas em `requirements.txt`

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/embrapii-matching.git
cd embrapii-matching
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
```

3. Ative o ambiente virtual:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Configure suas credenciais do SharePoint:

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
sharepoint_email=seu.email@embrapii.org.br
sharepoint_password=sua_senha
sharepoint_url_site=https://embrapii.sharepoint.com/sites/GEPES
```

## Uso

### Executando todos os testes de matching

```bash
python main.py
```

### Executando apenas um tipo de matching

```bash
python main.py --mode prospecoes  # Apenas matching GEREM-Prospecções
python main.py --mode negociacoes  # Apenas matching GEREM-Negociações
python main.py --mode projetos  # Apenas matching GEREM-Projetos
```

### Definindo credenciais na linha de comando

```bash
python main.py --email seu.email@embrapii.org.br --password sua_senha
```

### Desativando visualizações

```bash
python main.py --no-vis
```

### Usando um arquivo de configuração personalizado

```bash
python main.py --config minha_configuracao.yaml
```

## Configuração

O arquivo `config.py` contém as configurações padrão. Você pode sobrescrever essas configurações criando um arquivo YAML personalizado.

Exemplo de configuração YAML:

```yaml
sharepoint:
  site: https://embrapii.sharepoint.com/sites/GEPES
  data_path:
    gerem_interacoes: General/Lucas Pinheiro/scriptGerem/apuracao_resultados_2024.xlsx
    prospeccoes: DWPII/srinfo/prospeccao_prospeccao.xlsx

matching:
  algorithms:
    levenshtein:
      enabled: true
      threshold: 0.75
    jaro_winkler:
      enabled: true
      threshold: 0.85
    embedding:
      enabled: true
      threshold: 0.65
      model: paraphrase-multilingual-MiniLM-L12-v2
```

## Resultados

Após a execução, os resultados são salvos nos seguintes diretórios:

- `results/gerem_prospecoes/`: Resultados de matching GEREM-Prospecções
- `results/gerem_negociacoes/`: Resultados de matching GEREM-Negociações
- `results/gerem_projetos/`: Resultados de matching GEREM-Projetos

Cada diretório contém:

- Arquivos Excel com os matches encontrados por cada algoritmo
- Métricas de avaliação
- Matriz de concordância entre algoritmos
- Resultados de comparação de thresholds
- Visualizações (gráficos)
- O melhor resultado de matching baseado no critério escolhido

## Visualizações

As visualizações incluem:

- Contagem de matches por algoritmo
- Distribuição de scores de similaridade
- Mapa de calor de concordância entre algoritmos
- Exemplos de matches
- Comparação de thresholds
- Rede comparativa de matches

## Avaliação

O sistema avalia os algoritmos com base em:

- Número total de matches
- Número de registros únicos de origem com match
- Número de registros únicos de destino com match
- Média de similaridade
- Concordância entre algoritmos

O melhor algoritmo é selecionado com base no critério configurado (padrão: `match_count`).

## Licença

[Especifique a licença do projeto]

## Contato

[Seus dados de contato]