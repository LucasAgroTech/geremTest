#!/usr/bin/env python3
"""
Interface Streamlit para Rotulação de Dados
==========================================

Interface visual para rotular dados de matching como corretos ou incorretos.
Usado para criar dataset de treinamento de alta qualidade.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime

# Configurar página
st.set_page_config(
    page_title="Company Matching Labeler",
    page_icon="🏷️",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .match-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    
    .correct-match {
        border-left: 4px solid #28a745;
        background: #f8fff9;
    }
    
    .incorrect-match {
        border-left: 4px solid #dc3545;
        background: #fff8f8;
    }
    
    .similarity-high {
        color: #28a745;
        font-weight: bold;
    }
    
    .similarity-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .similarity-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class MatchingLabeler:
    def __init__(self):
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
    def load_data(self, file_path):
        """Carrega dados para rotulação"""
        if file_path.name.endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.name.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            st.error("Formato não suportado. Use .xlsx ou .csv")
            return None
    
    def save_labeled_data(self, df, filename):
        """Salva dados rotulados"""
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        return output_path
    
    def get_similarity_color_class(self, similarity):
        """Retorna classe CSS baseada na similaridade"""
        if similarity > 0.8:
            return "similarity-high"
        elif similarity > 0.5:
            return "similarity-medium"
        else:
            return "similarity-low"
    
    def render_match_card(self, row, key_prefix):
        """Renderiza um card de match para rotulação"""
        similarity = row['similarity']
        source_text = row['source_text']
        target_text = row['target_text']
        
        # Determinar cor baseada na similaridade
        sim_class = self.get_similarity_color_class(similarity)
        
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            st.markdown(f"**Texto Origem:**")
            st.markdown(f"`{source_text}`")
        
        with col2:
            st.markdown(f"**Texto Destino:**")
            st.markdown(f"`{target_text}`")
        
        with col3:
            st.markdown(f"**Similaridade:**")
            st.markdown(f'<span class="{sim_class}">{similarity:.3f}</span>', unsafe_allow_html=True)
            
            # Botões de rotulação
            col_correct, col_incorrect = st.columns(2)
            with col_correct:
                if st.button("✅ Correto", key=f"{key_prefix}_correct"):
                    return 1
            with col_incorrect:
                if st.button("❌ Incorreto", key=f"{key_prefix}_incorrect"):
                    return 0
        
        return None

def main():
    st.title("🏷️ Company Matching Data Labeler")
    st.markdown("Interface para rotular dados de matching como corretos ou incorretos")
    
    labeler = MatchingLabeler()
    
    # Sidebar para controles
    st.sidebar.header("📁 Configurações")
    
    # Upload de arquivo
    uploaded_file = st.sidebar.file_uploader(
        "Upload arquivo de matching",
        type=['csv', 'xlsx'],
        help="Arquivo com colunas: source_text, target_text, similarity"
    )
    
    if uploaded_file is not None:
        # Carregar dados
        df = labeler.load_data(uploaded_file)
        
        if df is not None:
            # Verificar colunas necessárias
            required_cols = ['source_text', 'target_text', 'similarity']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Arquivo deve conter as colunas: {required_cols}")
                return
            
            # Inicializar coluna de label se não existir
            if 'label' not in df.columns:
                df['label'] = -1  # -1 = não rotulado
            
            if 'labeled_by' not in df.columns:
                df['labeled_by'] = ""
            
            if 'labeled_at' not in df.columns:
                df['labeled_at'] = ""
            
            # Estatísticas
            st.sidebar.markdown("### 📊 Estatísticas")
            total_records = len(df)
            labeled_records = len(df[df['label'] != -1])
            unlabeled_records = total_records - labeled_records
            
            st.sidebar.metric("Total de Registros", total_records)
            st.sidebar.metric("Rotulados", labeled_records)
            st.sidebar.metric("Não Rotulados", unlabeled_records)
            
            if labeled_records > 0:
                correct_labels = len(df[df['label'] == 1])
                incorrect_labels = len(df[df['label'] == 0])
                st.sidebar.metric("Corretos", correct_labels)
                st.sidebar.metric("Incorretos", incorrect_labels)
            
            # Progresso
            progress = labeled_records / total_records if total_records > 0 else 0
            st.sidebar.progress(progress)
            st.sidebar.markdown(f"**Progresso:** {progress:.1%}")
            
            # Filtros
            st.sidebar.markdown("### 🔍 Filtros")
            
            # Filtro por status
            status_filter = st.sidebar.selectbox(
                "Status",
                ["Todos", "Não Rotulados", "Rotulados", "Corretos", "Incorretos"]
            )
            
            # Filtro por similaridade
            sim_range = st.sidebar.slider(
                "Faixa de Similaridade",
                min_value=0.0,
                max_value=1.0,
                value=(0.0, 1.0),
                step=0.01
            )
            
            # Aplicar filtros
            filtered_df = df.copy()
            
            # Filtro de status
            if status_filter == "Não Rotulados":
                filtered_df = filtered_df[filtered_df['label'] == -1]
            elif status_filter == "Rotulados":
                filtered_df = filtered_df[filtered_df['label'] != -1]
            elif status_filter == "Corretos":
                filtered_df = filtered_df[filtered_df['label'] == 1]
            elif status_filter == "Incorretos":
                filtered_df = filtered_df[filtered_df['label'] == 0]
            
            # Filtro de similaridade
            filtered_df = filtered_df[
                (filtered_df['similarity'] >= sim_range[0]) & 
                (filtered_df['similarity'] <= sim_range[1])
            ]
            
            # Ordenação
            sort_by = st.sidebar.selectbox(
                "Ordenar por",
                ["Similaridade (Desc)", "Similaridade (Asc)", "Índice"]
            )
            
            if sort_by == "Similaridade (Desc)":
                filtered_df = filtered_df.sort_values('similarity', ascending=False)
            elif sort_by == "Similaridade (Asc)":
                filtered_df = filtered_df.sort_values('similarity', ascending=True)
            
            # Paginação
            records_per_page = st.sidebar.number_input(
                "Registros por página",
                min_value=5,
                max_value=100,
                value=20
            )
            
            total_pages = (len(filtered_df) + records_per_page - 1) // records_per_page
            
            if total_pages > 0:
                page = st.sidebar.number_input(
                    "Página",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )
                
                start_idx = (page - 1) * records_per_page
                end_idx = start_idx + records_per_page
                page_df = filtered_df.iloc[start_idx:end_idx].reset_index()
                
                # Nome do usuário
                username = st.sidebar.text_input("Seu nome", value="Usuário")
                
                # Área principal
                st.header(f"📋 Rotulação - Página {page}/{total_pages}")
                st.markdown(f"Mostrando {len(page_df)} de {len(filtered_df)} registros filtrados")
                
                # Rotular registros
                for idx, row in page_df.iterrows():
                    st.markdown("---")
                    
                    # Status atual
                    current_label = row['label']
                    status_emoji = "❓" if current_label == -1 else ("✅" if current_label == 1 else "❌")
                    
                    st.markdown(f"### {status_emoji} Registro {start_idx + idx + 1}")
                    
                    # Card de match
                    col1, col2, col3 = st.columns([4, 4, 2])
                    
                    with col1:
                        st.markdown("**📝 Texto Origem:**")
                        st.info(row['source_text'])
                    
                    with col2:
                        st.markdown("**🎯 Texto Destino:**")
                        st.info(row['target_text'])
                    
                    with col3:
                        st.markdown("**📊 Similaridade:**")
                        sim_value = row['similarity']
                        if sim_value > 0.8:
                            st.success(f"{sim_value:.3f}")
                        elif sim_value > 0.5:
                            st.warning(f"{sim_value:.3f}")
                        else:
                            st.error(f"{sim_value:.3f}")
                        
                        # Botões de ação
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("✅ Correto", key=f"correct_{start_idx + idx}"):
                                original_idx = row['index']
                                df.loc[original_idx, 'label'] = 1
                                df.loc[original_idx, 'labeled_by'] = username
                                df.loc[original_idx, 'labeled_at'] = datetime.now().isoformat()
                                st.success("Marcado como correto!")
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("❌ Incorreto", key=f"incorrect_{start_idx + idx}"):
                                original_idx = row['index']
                                df.loc[original_idx, 'label'] = 0
                                df.loc[original_idx, 'labeled_by'] = username
                                df.loc[original_idx, 'labeled_at'] = datetime.now().isoformat()
                                st.error("Marcado como incorreto!")
                                st.rerun()
                    
                    # Mostrar informações adicionais se já rotulado
                    if current_label != -1:
                        st.caption(f"Rotulado por: {row.get('labeled_by', 'N/A')} em {row.get('labeled_at', 'N/A')}")
                
                # Ações em lote
                st.markdown("---")
                st.header("🔧 Ações em Lote")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Marcar Todos como Corretos"):
                        for idx, row in page_df.iterrows():
                            original_idx = row['index']
                            df.loc[original_idx, 'label'] = 1
                            df.loc[original_idx, 'labeled_by'] = username
                            df.loc[original_idx, 'labeled_at'] = datetime.now().isoformat()
                        st.success(f"Marcados {len(page_df)} registros como corretos!")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Marcar Todos como Incorretos"):
                        for idx, row in page_df.iterrows():
                            original_idx = row['index']
                            df.loc[original_idx, 'label'] = 0
                            df.loc[original_idx, 'labeled_by'] = username
                            df.loc[original_idx, 'labeled_at'] = datetime.now().isoformat()
                        st.error(f"Marcados {len(page_df)} registros como incorretos!")
                        st.rerun()
                
                with col3:
                    if st.button("❓ Limpar Rótulos da Página"):
                        for idx, row in page_df.iterrows():
                            original_idx = row['index']
                            df.loc[original_idx, 'label'] = -1
                            df.loc[original_idx, 'labeled_by'] = ""
                            df.loc[original_idx, 'labeled_at'] = ""
                        st.warning(f"Rótulos limpos para {len(page_df)} registros!")
                        st.rerun()
                
                # Visualização de distribuição
                st.markdown("---")
                st.header("📈 Análise dos Dados")
                
                # Gráfico de distribuição de similaridade por label
                labeled_data = df[df['label'] != -1]
                if len(labeled_data) > 0:
                    fig = px.histogram(
                        labeled_data,
                        x='similarity',
                        color='label',
                        barmode='overlay',
                        title="Distribuição de Similaridade por Rótulo",
                        labels={'label': 'Rótulo', 'similarity': 'Similaridade'},
                        color_discrete_map={0: 'red', 1: 'green'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Salvar dados
                st.markdown("---")
                st.header("💾 Salvar Dados")
                
                output_filename = st.text_input(
                    "Nome do arquivo de saída",
                    value=f"labeled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                
                if st.button("💾 Salvar Dados Rotulados"):
                    output_path = labeler.save_labeled_data(df, output_filename)
                    st.success(f"Dados salvos em: {output_path}")
                    
                    # Estatísticas finais
                    final_labeled = len(df[df['label'] != -1])
                    final_correct = len(df[df['label'] == 1])
                    final_incorrect = len(df[df['label'] == 0])
                    
                    st.info(f"""
                    **Estatísticas Finais:**
                    - Total de registros: {len(df)}
                    - Registros rotulados: {final_labeled}
                    - Marcados como corretos: {final_correct}
                    - Marcados como incorretos: {final_incorrect}
                    """)
            else:
                st.warning("Nenhum registro encontrado com os filtros aplicados.")
    else:
        st.info("👆 Faça upload de um arquivo para começar a rotulação")
        
        # Mostrar exemplo de formato esperado
        st.markdown("### 📋 Formato do Arquivo Esperado")
        
        example_data = {
            'source_text': ['BASF', 'Petrobras', 'Vale S.A.'],
            'target_text': ['BASF S.A.', 'Petróleo Brasileiro S.A.', 'Vale'],
            'similarity': [0.95, 0.87, 0.92]
        }
        
        st.dataframe(pd.DataFrame(example_data))

if __name__ == "__main__":
    main()