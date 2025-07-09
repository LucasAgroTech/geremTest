#!/usr/bin/env python3
"""
Configuração de Banco de Dados PostgreSQL para GEREM Analysis
=============================================================

Módulo para gerenciar conexão e operações com PostgreSQL
"""

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, Optional
import logging

class PostgreSQLManager:
    """Gerenciador de conexão PostgreSQL para GEREM Analysis"""
    
    def __init__(self):
        """Inicializa o gerenciador de PostgreSQL"""
        self.connection = None
        self.cursor = None
        
    def connect(self, host: str, database: str, user: str, password: str, port: int = 5432) -> bool:
        """
        Conecta ao PostgreSQL
        
        Args:
            host: Endereço do servidor
            database: Nome do banco
            user: Usuário
            password: Senha
            port: Porta (padrão 5432)
            
        Returns:
            True se conectado com sucesso
        """
        try:
            self.connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
            
        except psycopg2.Error as e:
            st.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Cria as tabelas necessárias para GEREM Analysis"""
        try:
            # Tabela para resultados de prospecções
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS gerem_prospecoes (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(255) NOT NULL,
                    target_id VARCHAR(255) NOT NULL,
                    similarity FLOAT NOT NULL,
                    source_text TEXT,
                    target_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para resultados de negociações
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS gerem_negociacoes (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(255) NOT NULL,
                    target_id VARCHAR(255) NOT NULL,
                    similarity FLOAT NOT NULL,
                    source_text TEXT,
                    target_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela para resultados de projetos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS gerem_projetos (
                    id SERIAL PRIMARY KEY,
                    source_id VARCHAR(255) NOT NULL,
                    target_id VARCHAR(255) NOT NULL,
                    similarity FLOAT NOT NULL,
                    source_text TEXT,
                    target_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_prospecoes_similarity ON gerem_prospecoes(similarity)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_negociacoes_similarity ON gerem_negociacoes(similarity)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_projetos_similarity ON gerem_projetos(similarity)")
            
            self.connection.commit()
            return True
            
        except psycopg2.Error as e:
            st.error(f"❌ Erro ao criar tabelas: {e}")
            self.connection.rollback()
            return False
    
    def upload_dataframe(self, df: pd.DataFrame, table_name: str) -> bool:
        """
        Faz upload de DataFrame para PostgreSQL
        
        Args:
            df: DataFrame com dados
            table_name: Nome da tabela (gerem_prospecoes, gerem_negociacoes, gerem_projetos)
            
        Returns:
            True se upload bem-sucedido
        """
        try:
            # Limpar tabela existente
            self.cursor.execute(f"TRUNCATE TABLE {table_name}")
            
            # Inserir dados
            for _, row in df.iterrows():
                self.cursor.execute(f"""
                    INSERT INTO {table_name} (source_id, target_id, similarity, source_text, target_text)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    row.get('source_id', ''),
                    row.get('target_id', ''),
                    row.get('similarity', 0.0),
                    row.get('source_text', ''),
                    row.get('target_text', '')
                ))
            
            self.connection.commit()
            return True
            
        except psycopg2.Error as e:
            st.error(f"❌ Erro ao fazer upload: {e}")
            self.connection.rollback()
            return False
    
    def load_data(self, table_name: str, similarity_threshold: float = 0.0) -> pd.DataFrame:
        """
        Carrega dados do PostgreSQL
        
        Args:
            table_name: Nome da tabela
            similarity_threshold: Threshold mínimo de similaridade
            
        Returns:
            DataFrame com dados
        """
        try:
            query = f"""
                SELECT source_id, target_id, similarity, source_text, target_text
                FROM {table_name}
                WHERE similarity >= %s
                ORDER BY similarity DESC
            """
            
            self.cursor.execute(query, (similarity_threshold,))
            rows = self.cursor.fetchall()
            
            # Converter para DataFrame
            df = pd.DataFrame(rows)
            return df
            
        except psycopg2.Error as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            return pd.DataFrame()
    
    def get_statistics(self, table_name: str) -> Dict:
        """
        Obtém estatísticas da tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            self.cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_records,
                    MIN(similarity) as min_similarity,
                    MAX(similarity) as max_similarity,
                    AVG(similarity) as avg_similarity,
                    COUNT(DISTINCT source_id) as unique_sources
                FROM {table_name}
            """)
            
            result = self.cursor.fetchone()
            return dict(result) if result else {}
            
        except psycopg2.Error as e:
            st.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def close(self):
        """Fecha conexão com PostgreSQL"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

def render_postgresql_config():
    """Renderiza interface de configuração PostgreSQL"""
    st.sidebar.markdown("### 🐘 Configuração PostgreSQL")
    
    # Configurações de conexão
    with st.sidebar.expander("🔧 Configurar Conexão", expanded=False):
        host = st.text_input("Host", value="localhost", help="Endereço do servidor PostgreSQL")
        database = st.text_input("Database", value="gerem_analysis", help="Nome do banco de dados")
        user = st.text_input("Usuário", value="postgres", help="Usuário do PostgreSQL")
        password = st.text_input("Senha", type="password", help="Senha do PostgreSQL")
        port = st.number_input("Porta", value=5432, help="Porta do PostgreSQL")
    
    # Testar conexão
    if st.sidebar.button("🔌 Testar Conexão", use_container_width=True):
        pg_manager = PostgreSQLManager()
        if pg_manager.connect(host, database, user, password, port):
            st.sidebar.success("✅ Conexão bem-sucedida!")
            
            # Criar tabelas se não existirem
            if pg_manager.create_tables():
                st.sidebar.success("✅ Tabelas criadas/verificadas!")
            
            # Salvar configuração na sessão
            st.session_state.pg_config = {
                'host': host, 'database': database, 'user': user, 
                'password': password, 'port': port
            }
            st.session_state.pg_connected = True
            
            pg_manager.close()
        else:
            st.session_state.pg_connected = False
    
    return st.session_state.get('pg_connected', False)

def upload_to_postgresql(files_data: Dict[str, pd.DataFrame]) -> bool:
    """
    Faz upload dos dados para PostgreSQL
    
    Args:
        files_data: Dicionário com DataFrames {tipo: dataframe}
        
    Returns:
        True se upload bem-sucedido
    """
    if 'pg_config' not in st.session_state:
        st.error("❌ Configuração PostgreSQL não encontrada")
        return False
    
    config = st.session_state.pg_config
    pg_manager = PostgreSQLManager()
    
    if not pg_manager.connect(**config):
        return False
    
    try:
        # Mapping de tipos para tabelas
        table_mapping = {
            'gerem_prospecoes': 'gerem_prospecoes',
            'gerem_negociacoes': 'gerem_negociacoes', 
            'gerem_projetos': 'gerem_projetos'
        }
        
        for data_type, df in files_data.items():
            if data_type in table_mapping and not df.empty:
                table_name = table_mapping[data_type]
                
                if pg_manager.upload_dataframe(df, table_name):
                    st.success(f"✅ {data_type}: {len(df)} registros enviados para PostgreSQL")
                else:
                    st.error(f"❌ Falha ao enviar {data_type}")
                    return False
        
        return True
        
    finally:
        pg_manager.close()

def load_from_postgresql() -> Dict[str, pd.DataFrame]:
    """
    Carrega dados do PostgreSQL
    
    Returns:
        Dicionário com DataFrames carregados
    """
    if 'pg_config' not in st.session_state:
        st.error("❌ Configuração PostgreSQL não encontrada")
        return {}
    
    config = st.session_state.pg_config
    pg_manager = PostgreSQLManager()
    
    if not pg_manager.connect(**config):
        return {}
    
    try:
        results = {}
        tables = ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos']
        
        for table in tables:
            df = pg_manager.load_data(table)
            if not df.empty:
                results[table] = df
                
                # Mostrar estatísticas
                stats = pg_manager.get_statistics(table)
                st.sidebar.info(f"""
                **{table.replace('gerem_', '').title()}:**
                - Total: {stats.get('total_records', 0):,}
                - Similaridade: {stats.get('min_similarity', 0):.3f} - {stats.get('max_similarity', 0):.3f}
                - Média: {stats.get('avg_similarity', 0):.3f}
                """)
        
        return results
        
    finally:
        pg_manager.close() 