# 🌐 Deploy Guide - Dashboard Público

Guia completo para colocar seu dashboard online e acessível para qualquer pessoa via link.

## 🚀 **Opção 1: Streamlit Community Cloud** ⭐ (Recomendado)

**✅ 100% Gratuito | ✅ Ilimitado | ✅ Domínio .streamlit.app**

### **Passo a Passo:**

#### **1. Preparar Repositório GitHub**
```bash
# Execute o script automático
./deploy.sh

# OU faça manualmente:
git init
git add .
git commit -m "GEREM Dashboard - Deploy inicial"
git remote add origin https://github.com/SEU_USUARIO/gerem-analysis
git push -u origin main
```

#### **2. Deploy no Streamlit Community Cloud**
1. **Acesse:** https://share.streamlit.io/
2. **Login:** Com sua conta GitHub
3. **New app:** Clique no botão
4. **Repository:** Selecione `SEU_USUARIO/gerem-analysis`
5. **Branch:** `main`
6. **Main file path:** `app.py`
7. **Advanced settings** (opcional):
   - **Python version:** 3.9
   - **App URL:** Customizar se desejar
8. **Deploy!** 🚀

#### **3. URL Final:**
```
https://seu-usuario-gerem-analysis-app-abc123.streamlit.app/
```

### **Tempo de Deploy:** 2-5 minutos ⚡

---

## 🚂 **Opção 2: Railway**

**✅ $5 Gratuitos/Mês | ✅ Domínio Customizado | ✅ Deploy Rápido**

### **Passo a Passo:**

#### **1. Criar Conta:**
- Acesse: https://railway.app/
- Login com GitHub

#### **2. Deploy:**
```bash
# 1. New Project → Deploy from GitHub repo
# 2. Selecionar seu repositório
# 3. Railway detecta Python automaticamente
```

#### **3. Configurar:**
```bash
# Adicionar variáveis de ambiente:
PORT=8501
PYTHONPATH=/app

# Comando de start (caso necessário):
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

#### **4. URL Final:**
```
https://seu-projeto.up.railway.app/
```

---

## 🎨 **Opção 3: Render**

**✅ Plano Gratuito | ✅ 750 horas/mês | ✅ SSL Automático**

### **Passo a Passo:**

#### **1. Criar Conta:**
- Acesse: https://render.com/
- Login com GitHub

#### **2. New Web Service:**
```bash
# 1. Connect GitHub repository
# 2. Name: gerem-analysis
# 3. Environment: Python 3
# 4. Build Command: pip install -r requirements.txt
# 5. Start Command: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

#### **3. Environment Variables:**
```bash
PYTHON_VERSION=3.9.16
PORT=10000
```

#### **4. URL Final:**
```
https://gerem-analysis.onrender.com/
```

---

## 🔐 **Deploy com PostgreSQL**

### **Para PostgreSQL na Nuvem:**

#### **1. Supabase (Gratuito):**
```bash
# 1. https://supabase.com/ → New Project
# 2. Copiar Database URL
# 3. Configurar no Streamlit Secrets
```

#### **2. Railway PostgreSQL:**
```bash
# 1. No projeto Railway → Add Service → PostgreSQL
# 2. Copiar CONNECTION_URL
# 3. Usar como variável de ambiente
```

#### **3. Render PostgreSQL:**
```bash
# 1. New → PostgreSQL
# 2. Copiar External Database URL
# 3. Configurar como variável
```

### **Configurar Secrets no Streamlit:**

Criar arquivo `.streamlit/secrets.toml` (NÃO commit):
```toml
[postgresql]
host = "sua-url.supabase.co"
database = "postgres"
username = "postgres"
password = "sua-senha"
port = 5432

# Ou como URL completa
DATABASE_URL = "postgresql://user:pass@host:port/db"
```

### **Modificar Código para Usar Secrets:**
```python
# Em database_config.py
import streamlit as st

# Usar secrets do Streamlit
if "postgresql" in st.secrets:
    pg_config = st.secrets["postgresql"]
    host = pg_config["host"]
    database = pg_config["database"]
    # etc...
```

---

## 📊 **Gerenciamento de Dados**

### **Opção 1: Upload Público** 
- ✅ **Usuários fazem upload** dos próprios dados
- ✅ **Dados temporários** (sessão)
- ✅ **Seguro** para informações sensíveis

### **Opção 2: PostgreSQL Público**
- ✅ **Dados persistentes** compartilhados
- ⚠️ **Apenas dados não sensíveis**
- ✅ **Performance superior**

### **Opção 3: Demo + Upload**
- ✅ **Dados demo** por padrão
- ✅ **Upload opcional** para dados reais
- ✅ **Melhor experiência** do usuário

---

## 🛡️ **Segurança & Privacidade**

### **Para Dashboard Público:**

#### **Dados Seguros:**
```python
# ✅ Fazer
- Upload temporário (por sessão)
- Dados demo para demonstração
- Validação de formatos de arquivo
- Limpeza automática de sessão

# ❌ Evitar  
- Commit dados sensíveis no repo
- Hardcode senhas/conexões
- Logs com informações pessoais
```

#### **PostgreSQL Público:**
```sql
-- ✅ Criar usuário apenas leitura
CREATE USER public_readonly WITH PASSWORD 'senha_publica';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO public_readonly;

-- ✅ Usar dados anonimizados
UPDATE tabela SET texto_sensivel = 'ANONIMIZADO';
```

#### **Variáveis de Ambiente:**
```bash
# No deploy, usar sempre variáveis de ambiente para:
- Senhas de banco
- URLs de conexão  
- Tokens de API
- Chaves secretas
```

---

## 🎯 **Deploy Recomendado**

### **Para Dashboard Público Simples:**
```bash
# 1. Streamlit Community Cloud
# 2. Upload de arquivos
# 3. Dados demo incluídos
# 4. URL: https://usuario-gerem-analysis-app-hash.streamlit.app/
```

### **Para Dashboard Corporativo:**
```bash
# 1. Railway ou Render
# 2. PostgreSQL na nuvem
# 3. Domínio customizado
# 4. Autenticação (se necessário)
```

---

## 🚀 **Deploy em 2 Minutos**

### **Método Rápido:**
```bash
# 1. Executar script
./deploy.sh

# 2. Ir para Streamlit Cloud
https://share.streamlit.io/

# 3. Connect repository + Deploy
# 4. ✅ Dashboard online!
```

### **URL de Exemplo:**
```
🔗 https://lucaspinheiro-gerem-analysis-app-xyz123.streamlit.app/
```

---

## 📱 **Compartilhamento**

### **Como Compartilhar:**
```bash
# ✅ Enviar link direto
"Acesse nosso dashboard: https://seu-dashboard.streamlit.app/"

# ✅ QR Code para mobile
# Gerar QR code do link

# ✅ Embed em site
<iframe src="https://seu-dashboard.streamlit.app/?embedded=true" width="100%" height="800"></iframe>

# ✅ Social media
"📊 Dashboard GEREM Analysis disponível: [link]"
```

### **Funcionalidades Públicas:**
- ✅ **Upload de arquivos** (qualquer usuário)
- ✅ **Análise em tempo real**
- ✅ **Exportação de relatórios**
- ✅ **Responsivo** (mobile + desktop)
- ✅ **Sem necessidade** de login/cadastro

---

## 🆘 **Troubleshooting**

### **Deploy Failed:**
```bash
# Verificar logs no Streamlit Cloud
# Comum: requirements.txt incorreto

# Solução:
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Fix requirements"
git push
```

### **App Não Carrega:**
```bash
# Verificar se app.py é o arquivo principal
# Verificar se não há imports circulares
# Verificar se todas as dependências estão no requirements.txt
```

### **Dados Não Aparecem:**
```bash
# Verificar se upload está funcionando
# Verificar se PostgreSQL está conectado
# Verificar logs de erro no dashboard
```

---

## 🎉 **Próximos Passos**

1. **✅ Execute** `./deploy.sh`
2. **🌐 Acesse** Streamlit Community Cloud
3. **🚀 Faça** deploy em 2 cliques
4. **📱 Compartilhe** o link com todos
5. **📊 Monitore** uso e performance
6. **🔧 Customize** domínio (opcional)

---

**🎊 Em poucos minutos seu dashboard estará online e acessível para qualquer pessoa no mundo!** 