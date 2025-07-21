# 🎯 Guia Completo de Validação Manual

## 📋 Visão Geral

Este guia explica como validar manualmente os matches e treinar o modelo com base na sua validação, identificando e corrigindo falsos positivos.

## 🚀 Processo Completo

### 1. Análise Inicial dos Dados

Primeiro, execute uma análise para entender os padrões nos dados:

```bash
cd company_matching_trainer
python3 analyze_matches.py
```

**O que esta análise faz:**
- Identifica padrões suspeitos de falsos positivos
- Sugere prioridades para validação
- Cria amostras estratégicas para validação
- Gera relatório detalhado

### 2. Validação Manual Interativa

Execute o sistema de validação manual:

```bash
python3 manual_validation.py
```

**Menu de opções:**
1. **Validar matches manualmente** - Interface interativa
2. **Treinar modelo com validação manual** - Usar dados validados
3. **Mostrar progresso atual** - Ver estatísticas
4. **Sair**

### 3. Interface de Validação

Quando escolher a opção 1, você verá:

```
📊 Registro 1/1000
Similaridade: 0.876
Fonte: gerem_negociacoes
----------------------------------------
EMPRESA A: BASF S.A.
EMPRESA B: BASF BRASIL LTDA
----------------------------------------
É o mesmo empresa? (1=sim, 0=não, s=pular, q=sair, r=relatório):
```

**Comandos disponíveis:**
- **1** = MATCH CORRETO (mesma empresa)
- **0** = FALSO POSITIVO (empresas diferentes)
- **s** = PULAR este registro
- **q** = SAIR e salvar progresso
- **r** = RELATÓRIO de progresso

## 🎯 Estratégia de Validação

### Prioridades Recomendadas

1. **Prioridade 1** (Similaridade 0.85-0.95): ~500 casos
   - Casos mais incertos e importantes
   - Maior impacto no treinamento

2. **Prioridade 2** (Similaridade 0.75-0.85): ~300 casos
   - Casos moderadamente incertos

3. **Prioridade 3** (Similaridade 0.65-0.75): ~200 casos
   - Casos com menor similaridade

### Meta Inicial

**Objetivo**: Validar pelo menos 200-500 casos antes do primeiro treinamento.

## 📊 Critérios de Validação

### ✅ MATCH CORRETO (1)

Marque como **1** quando:
- É claramente a mesma empresa
- Variações do mesmo nome: "BASF" vs "BASF S.A."
- Siglas vs nome completo: "USP" vs "Universidade de São Paulo"
- Pequenas diferenças de formatação

**Exemplos:**
- "Microsoft Corporation" vs "Microsoft Corp"
- "Petrobras" vs "Petróleo Brasileiro S.A."
- "Vale S.A." vs "Vale"

### ❌ FALSO POSITIVO (0)

Marque como **0** quando:
- São empresas claramente diferentes
- Mesmo setor mas empresas distintas
- Nomes similares mas organizações diferentes

**Exemplos:**
- "BASF" vs "Petrobras"
- "Microsoft" vs "Apple"
- "Banco do Brasil" vs "Banco Bradesco"

### 🤔 Casos Duvidosos

Para casos duvidosos:
1. **Pule (s)** se não tiver certeza
2. Use as **notas** para documentar dúvidas
3. Marque **confiança baixa** se decidir rotular

## 💾 Salvamento Automático

O sistema salva automaticamente:
- **A cada 10 validações**: Progresso salvo
- **Ao sair (q)**: Todos os dados salvos
- **Ctrl+C**: Salvamento de emergência

## 📈 Monitoramento do Progresso

Use **r** durante a validação para ver:
- Total de registros validados
- Matches corretos vs falsos positivos
- Taxa de falsos positivos atual
- Porcentagem de conclusão

## 🚀 Treinamento com Dados Validados

Após validar pelo menos 200 casos:

```bash
python3 manual_validation.py
# Escolha opção 2: Treinar modelo com validação manual
```

**O que acontece:**
1. Carrega seus dados validados manualmente
2. Adiciona dados automáticos de alta confiança (se necessário)
3. Treina modelo transformer especializado
4. Avalia performance
5. Salva modelo em `models/manual_validated_matcher/`

## 📁 Arquivos Gerados

### Durante a Validação
- `data/manual_validation.csv` - Dados com suas validações
- `data/validation_progress.json` - Progresso atual
- `data/priority1_sample.csv` - Amostra prioritária

### Após o Treinamento
- `data/manual_training_data.csv` - Dados finais de treinamento
- `models/manual_validated_matcher/` - Modelo treinado
- `training.log` - Log detalhado do treinamento

## 🔧 Dicas Práticas

### Para Validação Eficiente

1. **Foque na qualidade**: Melhor validar menos com certeza
2. **Use padrões**: Desenvolva critérios consistentes
3. **Documente dúvidas**: Use as notas para casos complexos
4. **Faça pausas**: Validação cansativa pode gerar erros

### Para Casos Específicos

**Siglas vs Nomes Completos:**
- "USP" vs "Universidade de São Paulo" = MATCH (1)
- "IBM" vs "International Business Machines" = MATCH (1)

**Subsidiárias:**
- "Microsoft Brasil" vs "Microsoft Corporation" = Depende do contexto
- Se for a mesma organização = MATCH (1)
- Se forem entidades legais diferentes = FALSO POSITIVO (0)

**Variações de Nome:**
- "Cia." vs "Companhia" = MATCH (1)
- "Ltda" vs "LTDA" vs "Limitada" = MATCH (1)

## 📊 Exemplo de Sessão

```
=== Validação Manual de Matches ===
Total de registros: 1000
Iniciando do índice: 0

📊 Registro 1/1000
Similaridade: 0.892
Fonte: gerem_negociacoes
----------------------------------------
EMPRESA A: BASF S.A.
EMPRESA B: BASF BRASIL LTDA
----------------------------------------
É o mesmo empresa? (1=sim, 0=não, s=pular, q=sair, r=relatório): 1
Confiança na decisão (a=alta, m=média, b=baixa, enter=pular): a
Notas (opcional, enter=pular): 
✅ MATCH CORRETO - Registrado!

📊 Registro 2/1000
Similaridade: 0.834
Fonte: gerem_prospecoes
----------------------------------------
EMPRESA A: Microsoft Corporation
EMPRESA B: Apple Inc.
----------------------------------------
É o mesmo empresa? (1=sim, 0=não, s=pular, q=sair, r=relatório): 0
Confiança na decisão (a=alta, m=média, b=baixa, enter=pular): a
Notas (opcional, enter=pular): Empresas diferentes do setor tech
❌ FALSO POSITIVO - Registrado!
```

## 🎯 Resultados Esperados

Após validar 200-500 casos e treinar:
- **Modelo personalizado** treinado nos seus critérios
- **Acurácia melhorada** vs algoritmos genéricos
- **Redução significativa** de falsos positivos
- **Base sólida** para melhorias futuras

## 🔄 Processo Iterativo

1. **Primeira rodada**: 200-500 validações → Primeiro modelo
2. **Teste em produção**: Coletar feedback
3. **Segunda rodada**: Mais 200-300 validações → Modelo refinado
4. **Melhoria contínua**: Validações mensais → Retreinamento

---

**💡 Lembre-se**: A qualidade da validação manual determina a qualidade do modelo final. Seja consistente e criterioso!
