#!/bin/bash
echo "🚀 Iniciando Análise de Cadeia GEREM..."
echo

# Verificar se o ambiente virtual está ativo
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  ATENÇÃO: Recomenda-se ativar o ambiente virtual primeiro"
    echo "   Execute: source venv/bin/activate"
    echo
    read -p "Continuar mesmo assim? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Execução cancelada"
        exit 1
    fi
fi

# Verificar se os resultados de matching existem
if [ ! -d "results/gerem_prospecoes" ] && [ ! -d "results/gerem_negociacoes" ] && [ ! -d "results/gerem_projetos" ]; then
    echo "⚠️  ATENÇÃO: Nenhum resultado de matching encontrado em 'results/'"
    echo "   Execute primeiro o matching principal com: python main.py"
    echo
    read -p "Continuar mesmo assim? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Execução cancelada"  
        exit 1
    fi
fi

# Lançar a aplicação Streamlit
echo "📊 Abrindo interface web da análise de cadeia..."
echo "   URL: http://localhost:8501"
echo "   Pressione Ctrl+C para parar"
echo
streamlit run chain_analysis.py
