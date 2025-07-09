# 🐘 PostgreSQL Setup - GEREM Analysis

Guia completo para configurar PostgreSQL com o dashboard GEREM Chain Analysis.

## 🚀 **Instalação PostgreSQL**

### **Windows:**
```bash
# Baixar e instalar do site oficial
https://www.postgresql.org/download/windows/

# Ou via Chocolatey
choco install postgresql
```

### **macOS:**
```bash
# Via Homebrew
brew install postgresql
brew services start postgresql

# Criar banco de dados
createdb gerem_analysis
```

### **Linux (Ubuntu/Debian):**
```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Iniciar serviço
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar usuário e banco
sudo -u postgres psql
CREATE DATABASE gerem_analysis;
CREATE USER gerem_user WITH ENCRYPTED PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE gerem_analysis TO gerem_user;
\q
```

## 🔧 **Configuração no Dashboard**

### **1. Instalar Dependência Python:**
```bash
pip install psycopg2-binary
```

### **2. Configurar Conexão:**
No dashboard Streamlit:
- **Host:** `localhost` (ou IP do servidor)
- **Database:** `gerem_analysis`
- **Usuário:** `postgres` (ou usuário criado)
- **Senha:** (sua senha PostgreSQL)
- **Porta:** `5432` (padrão)

### **3. Testar Conexão:**
1. Clique em "🔌 Testar Conexão"
2. Se bem-sucedida, as tabelas serão criadas automaticamente

## 📊 **Fluxo de Trabalho**

### **Opção 1: Upload → PostgreSQL**
1. Selecione "📤 Upload de Arquivos"
2. Faça upload dos 3 arquivos de embedding
3. Marque "📤 Enviar para PostgreSQL"
4. Clique "🚀 Enviar para BD"

### **Opção 2: Direto do PostgreSQL**
1. Selecione "🐘 PostgreSQL"
2. Configure a conexão
3. Clique "📥 Carregar do PostgreSQL"

## 🛠️ **Estrutura do Banco**

### **Tabelas Criadas:**
```sql
-- Resultados GEREM → Prospecções
gerem_prospecoes (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(255),
    target_id VARCHAR(255),
    similarity FLOAT,
    source_text TEXT,
    target_text TEXT,
    created_at TIMESTAMP
)

-- Resultados GEREM → Negociações
gerem_negociacoes (...)

-- Resultados GEREM → Projetos
gerem_projetos (...)
```

### **Índices para Performance:**
```sql
CREATE INDEX idx_prospecoes_similarity ON gerem_prospecoes(similarity);
CREATE INDEX idx_negociacoes_similarity ON gerem_negociacoes(similarity);
CREATE INDEX idx_projetos_similarity ON gerem_projetos(similarity);
```

## 🌟 **Vantagens do PostgreSQL**

### **✅ Benefícios:**
- **Performance Superior:** Consultas mais rápidas
- **Dados Persistentes:** Não precisa recarregar a cada sessão
- **Controle de Versão:** Histórico de dados com timestamps
- **Escalabilidade:** Suporta grandes volumes de dados
- **Backup Automático:** Dados seguros e recuperáveis
- **Multi-usuário:** Vários usuários podem acessar simultaneamente

### **📈 Casos de Uso Ideais:**
- **Produção:** Ambiente corporativo
- **Grandes Datasets:** > 100k registros
- **Análises Recorrentes:** Dados usados frequentemente
- **Colaboração:** Múltiplos analistas
- **Auditoria:** Rastreabilidade necessária

## 🚀 **Deploy em Produção**

### **1. PostgreSQL na Nuvem:**

#### **Render (Gratuito):**
```bash
# Criar banco PostgreSQL gratuito
https://render.com/ → New → PostgreSQL
```

#### **Supabase (Gratuito):**
```bash
# PostgreSQL gratuito com interface web
https://supabase.com/ → New Project
```

#### **Railway (Gratuito):**
```bash
# PostgreSQL com $5 gratuitos
https://railway.app/ → New → PostgreSQL
```

### **2. Configurar Variáveis de Ambiente:**
```bash
# Para deploy seguro
DATABASE_URL=postgresql://user:pass@host:port/db
```

### **3. Modificar Código para Produção:**
```python
# Em database_config.py
import os

# Usar variáveis de ambiente
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Parse connection string
    # Usar para conexão automática
```

## 🔒 **Segurança**

### **Boas Práticas:**
```sql
-- Criar usuário específico com permissões limitadas
CREATE USER gerem_readonly WITH PASSWORD 'senha_forte';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gerem_readonly;

-- Para análise apenas leitura
CREATE USER analyst WITH PASSWORD 'senha_analista';
GRANT SELECT ON gerem_prospecoes, gerem_negociacoes, gerem_projetos TO analyst;
```

### **Backup Regular:**
```bash
# Backup automático
pg_dump gerem_analysis > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql gerem_analysis < backup_20250109.sql
```

## 🆘 **Troubleshooting**

### **Erro: Connection refused**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar porta
netstat -ln | grep 5432

# Reiniciar serviço
sudo systemctl restart postgresql
```

### **Erro: Authentication failed**
```bash
# Resetar senha postgres
sudo -u postgres psql
ALTER USER postgres PASSWORD 'nova_senha';
\q
```

### **Erro: Database does not exist**
```bash
# Criar banco manualmente
sudo -u postgres createdb gerem_analysis
```

### **Erro: Permission denied**
```bash
# Dar permissões completas
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE gerem_analysis TO seu_usuario;
\q
```

## 📋 **Comandos Úteis**

### **Monitoramento:**
```sql
-- Ver tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';

-- Ver estatísticas das tabelas
SELECT 
    tablename,
    n_tup_ins as inserted,
    n_tup_upd as updated,
    n_tup_del as deleted
FROM pg_stat_user_tables;
```

### **Manutenção:**
```sql
-- Analisar tabelas para otimizar performance
ANALYZE gerem_prospecoes;
ANALYZE gerem_negociacoes;
ANALYZE gerem_projetos;

-- Vacuum para limpeza
VACUUM ANALYZE;
```

## 🎯 **Próximos Passos**

1. **✅ Instalar PostgreSQL** localmente
2. **🔧 Configurar** conexão no dashboard
3. **📤 Testar upload** de dados
4. **📊 Executar análises** 
5. **🚀 Considerar deploy** em nuvem
6. **🔄 Automatizar backups**

---

**💡 Dica:** Comece local e migre para nuvem quando estiver satisfeito com o funcionamento! 