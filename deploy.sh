#!/bin/bash

# 🚀 Deploy Script - GEREM Chain Analysis
# ========================================

echo "🚀 Iniciando deploy do GEREM Chain Analysis..."

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para print colorido
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos em um repositório git
if [ ! -d ".git" ]; then
    print_status "Inicializando repositório Git..."
    git init
    print_success "Repositório Git inicializado!"
fi

# Verificar arquivos necessários
print_status "Verificando arquivos necessários..."

required_files=("app.py" "requirements.txt" "README_DEPLOY.md")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file encontrado"
    else
        print_error "✗ $file não encontrado!"
        exit 1
    fi
done

# Criar README.md se não existir
if [ ! -f "README.md" ]; then
    print_status "Criando README.md..."
    cat > README.md << 'EOF'
# 🎯 GEREM Chain Analysis Dashboard

Dashboard profissional para análise da cadeia de conversão GEREM utilizando algoritmos de embedding.

## 🚀 Deploy

Este dashboard está deployado no Streamlit Community Cloud e pode ser acessado por qualquer pessoa.

## 📊 Funcionalidades

- **Upload de Arquivos**: Faça upload dos seus dados de embedding
- **PostgreSQL**: Conecte a uma base de dados PostgreSQL
- **Análise Profissional**: KPIs, funil de conversão, insights automáticos
- **Visualizações Interativas**: Gráficos profissionais com Plotly
- **Exportação**: Relatórios em JSON e texto

## 🔧 Como Usar

1. Acesse o link do dashboard
2. Selecione "📤 Upload de Arquivos" 
3. Faça upload dos 3 arquivos de embedding:
   - Prospecções
   - Negociações  
   - Projetos
4. Configure os thresholds
5. Execute a análise

## 🛠️ Tecnologias

- **Streamlit**: Interface web
- **Plotly**: Visualizações interativas
- **PostgreSQL**: Base de dados (opcional)
- **Pandas**: Manipulação de dados
- **Sentence Transformers**: Embeddings

## 📈 Análises Disponíveis

- Taxa de conversão por etapa
- Funil de conversão interativo
- Métricas de qualidade
- Insights automáticos
- Relatórios executivos

---

**Desenvolvido para análise profissional da cadeia GEREM**
EOF
    print_success "README.md criado!"
fi

# Verificar se há mudanças para commit
if [ -n "$(git status --porcelain)" ]; then
    print_status "Adicionando arquivos ao Git..."
    git add .
    
    print_status "Fazendo commit..."
    commit_message="Deploy: GEREM Chain Analysis Dashboard $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$commit_message"
    print_success "Commit realizado: $commit_message"
else
    print_warning "Nenhuma mudança detectada para commit"
fi

# Verificar se há remote configurado
if ! git remote get-url origin &> /dev/null; then
    print_warning "Remote 'origin' não configurado!"
    print_status "Configure o remote do GitHub:"
    echo "  git remote add origin https://github.com/SEU_USUARIO/gerem-analysis"
    echo "  git push -u origin main"
    echo ""
    print_status "Depois acesse:"
    echo "  🌐 https://share.streamlit.io/"
    echo "  📁 Conecte seu repositório"
    echo "  🚀 Deploy automático!"
else
    print_status "Fazendo push para GitHub..."
    
    # Verificar se a branch main existe
    if ! git show-ref --verify --quiet refs/heads/main; then
        print_status "Criando branch main..."
        git branch -M main
    fi
    
    # Push para GitHub
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        print_success "Push realizado com sucesso!"
        echo ""
        print_success "🎉 Repositório atualizado no GitHub!"
        echo ""
        print_status "Próximos passos:"
        echo "  1. 🌐 Acesse: https://share.streamlit.io/"
        echo "  2. 🔐 Faça login com sua conta GitHub"
        echo "  3. 📁 Clique em 'New app'"
        echo "  4. 📂 Selecione seu repositório"
        echo "  5. 📄 Main file path: app.py"
        echo "  6. 🚀 Clique em 'Deploy!'"
        echo ""
        print_success "Seu dashboard ficará disponível em:"
        echo "  🔗 https://SEU_USUARIO-NOME_REPO-app-HASH.streamlit.app/"
    else
        print_error "Falha no push para GitHub!"
        print_status "Verifique se:"
        echo "  - Você tem permissões no repositório"
        echo "  - O remote está configurado corretamente"
        echo "  - Sua autenticação GitHub está funcionando"
    fi
fi

print_success "Script de deploy concluído!" 