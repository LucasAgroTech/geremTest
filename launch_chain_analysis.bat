@echo off
echo 🚀 Iniciando Análise de Cadeia GEREM...
echo.

REM Verificar se o ambiente virtual está ativo
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  ATENÇÃO: Recomenda-se ativar o ambiente virtual primeiro
    echo    Execute: venv\Scripts\activate
    echo.
    pause
)

REM Verificar se os resultados de matching existem  
if not exist "results\gerem_prospecoes" if not exist "results\gerem_negociacoes" if not exist "results\gerem_projetos" (
    echo ⚠️  ATENÇÃO: Nenhum resultado de matching encontrado em 'results\'
    echo    Execute primeiro o matching principal com: python main.py
    echo.
    pause
)

REM Lançar a aplicação Streamlit
echo 📊 Abrindo interface web da análise de cadeia...
echo    URL: http://localhost:8501
echo    Pressione Ctrl+C para parar
echo.
streamlit run chain_analysis.py

pause
