# 🚀 Deploy Gratuito - GEREM Chain Analysis

Guia completo para fazer deploy **100% GRATUITO** do seu dashboard Streamlit.

## 🌟 **Opções de Deploy Gratuito**

### **1. Streamlit Community Cloud** ⭐ (Recomendado)

**✅ Totalmente Gratuito | ✅ Ilimitado | ✅ Deploy Automático**

#### **Passo a Passo:**

1. **Preparar Repositório**
   ```bash
   git init
   git add .
   git commit -m "Dashboard GEREM Chain Analysis"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/gerem-analysis
   git push -u origin main
   ```

2. **Deploy no Streamlit Cloud**
   - Acesse: https://share.streamlit.io/
   - Faça login com GitHub
   - Clique em "New app"
   - Selecione seu repositório
   - **Main file path**: `app.py`
   - Clique em "Deploy!"

3. **Configuração Automática**
   - O Streamlit Cloud detecta automaticamente:
     - `requirements.txt` → Dependências Python
     - `packages.txt` → Dependências do sistema
     - `.streamlit/config.toml` → Configurações

#### **URL Final**: `https://SEU_USUARIO-gerem-analysis-app-HASH.streamlit.app/`

---

### **2. Railway** 🚂

**✅ $5 Gratuitos/Mês | ✅ Suficiente para Streamlit | ✅ Deploy via GitHub**

#### **Passo a Passo:**

1. **Criar Conta**: https://railway.app/
2. **Deploy**:
   - Connect GitHub repository
   - Select your repo
   - Railway detecta Python automaticamente
3. **Configurar**:
   - Add environment variable: `PORT=8501`
   - Add start command: `streamlit run app.py --server.port=$PORT`

---

### **3. Render** 🎨

**✅ Plano Gratuito | ✅ 750 horas/mês | ✅ SSL Gratuito**

#### **Passo a Passo:**

1. **Criar Conta**: https://render.com/
2. **New Web Service**:
   - Connect GitHub repository
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
3. **Environment Variables**:
   - `PYTHON_VERSION=3.9.16`

---

## 📁 **Estrutura de Arquivos para Deploy**

```
geremTest/
├── app.py                    # ← Ponto de entrada principal
├── chain_analysis.py         # ← Dashboard original
├── requirements.txt          # ← Dependências Python
├── packages.txt             # ← Dependências sistema
├── .streamlit/
│   └── config.toml          # ← Configurações Streamlit
├── README_DEPLOY.md         # ← Este guia
└── data/                    # ← Dados de exemplo (opcional)
```

---

## 🔧 **Configurações Importantes**

### **requirements.txt** (Otimizado)
```txt
pandas>=1.5.0,<2.1.0
numpy>=1.24.0,<1.26.0
streamlit>=1.28.0,<1.30.0
plotly>=5.15.0,<5.18.0
sentence-transformers>=2.2.0,<2.4.0
scikit-learn>=1.3.0,<1.4.0
openpyxl>=3.1.0,<3.2.0
```

### **packages.txt** (Para Streamlit Cloud)
```txt
build-essential
python3-dev
libffi-dev
libssl-dev
```

### **.streamlit/config.toml**
```toml
[server]
port = 8501
headless = true
enableCORS = false

[theme]
primaryColor = "#1f4e79"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
```

---

## 📊 **Sobre os Dados das Planilhas**

### **Opção 1: Dados de Demonstração** 🎯
- ✅ **Incluído no app**: Dados sintéticos para demonstração
- ✅ **Deploy imediato**: Funciona sem arquivos externos
- ✅ **Gratuito**: Não requer armazenamento adicional

### **Opção 2: Upload de Arquivos** 📤
- ✅ **Interface de upload**: Usuários fazem upload dos próprios dados
- ✅ **Temporário**: Arquivos ficam apenas na sessão
- ✅ **Seguro**: Dados não são armazenados permanentemente

### **Opção 3: GitHub Repository** 📁 (Se dados não forem sensíveis)
- ✅ **Commit direto**: Incluir dados no repositório
- ✅ **Deploy automático**: Dados sempre disponíveis
- ⚠️ **Público**: Apenas para dados não confidenciais

---

## 🛡️ **Segurança e Privacidade**

### **Para Dados Sensíveis:**
1. **NÃO** commitar dados sensíveis no GitHub
2. **Use** o sistema de upload do app
3. **Configure** variáveis de ambiente para APIs
4. **Considere** autenticação se necessário

### **Para Dados Públicos:**
1. **Pode** incluir no repositório
2. **Estruture** em pasta `data/`
3. **Documente** origem e licença

---

## 🚀 **Deploy em 5 Minutos**

### **Quickstart - Streamlit Cloud:**

```bash
# 1. Preparar repositório
git init
git add .
git commit -m "Initial commit"

# 2. Enviar para GitHub
git remote add origin https://github.com/SEU_USUARIO/gerem-analysis
git push -u origin main

# 3. Deploy no Streamlit Cloud
# - Vá para https://share.streamlit.io/
# - Conecte seu repositório
# - Deploy automático!
```

### **URL de Exemplo:**
`https://seu-usuario-gerem-analysis-app-xyz123.streamlit.app/`

---

## 💡 **Dicas de Otimização**

### **Performance:**
- ✅ Use `@st.cache_data` para dados grandes
- ✅ Otimize imports (apenas o necessário)
- ✅ Versões específicas no requirements.txt

### **UX:**
- ✅ Dados de demonstração por padrão
- ✅ Upload drag-and-drop
- ✅ Indicadores de carregamento
- ✅ Mensagens de erro claras

### **Manutenção:**
- ✅ Versionamento semântico
- ✅ Logs de deploy
- ✅ Monitoramento de uso

---

## 🆘 **Troubleshooting**

### **Erro: Module not found**
```bash
# Verificar requirements.txt
pip install -r requirements.txt

# Adicionar dependência faltante
echo "nome_do_modulo==versao" >> requirements.txt
```

### **Erro: Memory limit**
```python
# Otimizar carregamento de dados
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")
```

### **Erro: Port binding**
```bash
# Para Railway/Render
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## 🎯 **Próximos Passos**

1. **✅ Deploy básico** usando Streamlit Cloud
2. **🔧 Customizar** domínio (opcional, pago)
3. **📊 Monitorar** uso e performance
4. **🚀 Otimizar** baseado no feedback
5. **📈 Escalar** se necessário

---

## 📞 **Suporte**

- **Streamlit Docs**: https://docs.streamlit.io/
- **Community Cloud**: https://docs.streamlit.io/streamlit-community-cloud
- **GitHub Issues**: Para problemas específicos

---

**🎉 Seu dashboard estará online em poucos minutos, totalmente gratuito!** 