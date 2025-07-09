#!/usr/bin/env python3
"""
GEREM Chain Analysis Dashboard
=============================

Análise Profissional da Cadeia de Conversão GEREM
Interface corporativa para análise de resultados de matching por embedding

Funcionalidades:
- Dashboard executivo com KPIs principais
- Análise da cadeia: GEREM → Prospecções → Negociações → Projetos
- Visualizações interativas e profissionais
- Relatórios detalhados para tomada de decisão
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from datetime import datetime, timedelta
import json
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="GEREM Chain Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para design profissional
st.markdown("""
<style>
    /* Paleta de cores corporativa */
    :root {
        --primary-color: #1f4e79;
        --secondary-color: #2e6da4;
        --accent-color: #4a90b8;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --danger-color: #dc3545;
        --light-bg: #f8f9fa;
        --dark-text: #2c3e50;
    }
    
    /* Header personalizado */
    .main-header {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Cards KPI */
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: var(--dark-text);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
    
    .kpi-change {
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    /* Sidebar customização */
    .sidebar .sidebar-content {
        background: var(--light-bg);
    }
    
    /* Botões personalizados */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: var(--secondary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Métricas Streamlit customizadas */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--light-bg);
        border-radius: 5px;
    }
    
    /* Alertas personalizados */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Sidebar title */
    .sidebar-title {
        color: var(--primary-color);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-success { background-color: var(--success-color); }
    .status-warning { background-color: var(--warning-color); }
    .status-danger { background-color: var(--danger-color); }
    
    /* Section dividers */
    .section-divider {
        border-top: 2px solid var(--primary-color);
        margin: 2rem 0;
        opacity: 0.3;
    }
</style>
""", unsafe_allow_html=True)

class ProfessionalChainAnalyzer:
    def __init__(self):
        """Inicializa o analisador profissional de cadeia de conversão"""
        self.results_base_path = "results"
        self.algorithm = "embedding"  # Foco apenas em embedding
        self.data_cache = {}
        
        # Configurações padrão
        self.default_thresholds = {
            'prospecoes': 0.75,
            'negociacoes': 0.70,
            'projetos': 0.75
        }
        
    def load_embedding_results(self):
        """Carrega apenas os resultados de embedding"""
        with st.spinner("🔄 Carregando dados de embedding..."):
            results = {}
            match_types = ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos']
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, match_type in enumerate(match_types):
                status_text.text(f"Carregando {match_type}...")
                progress_bar.progress((i + 1) / len(match_types))
                
                type_path = os.path.join(self.results_base_path, match_type)
                if not os.path.exists(type_path):
                    st.error(f"❌ Diretório não encontrado: {type_path}")
                    continue
                
                # Encontrar a pasta mais recente
                folders = [f for f in os.listdir(type_path) if os.path.isdir(os.path.join(type_path, f))]
                if not folders:
                    st.warning(f"⚠️ Nenhuma pasta de resultados encontrada em: {type_path}")
                    continue
                
                latest_folder = sorted(folders)[-1]
                folder_path = os.path.join(type_path, latest_folder)
                
                # Procurar arquivo de embedding
                possible_files = [
                    'embedding_matches.xlsx',
                    'embedding_matches.csv',
                    'embedding.xlsx',
                    'embedding.csv'
                ]
                
                file_loaded = False
                for file_name in possible_files:
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.exists(file_path):
                        try:
                            if file_name.endswith('.xlsx'):
                                df = pd.read_excel(file_path)
                            else:
                                df = pd.read_csv(file_path)
                            
                            # Verificar colunas essenciais
                            required_cols = ['similarity', 'source_id', 'target_id']
                            if all(col in df.columns for col in required_cols):
                                results[match_type] = df
                                file_loaded = True
                                break
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar {file_path}: {e}")
                
                if not file_loaded:
                    st.warning(f"⚠️ Arquivo de embedding não encontrado para {match_type}")
            
            progress_bar.empty()
            status_text.empty()
            
            return results
    
    def apply_intelligent_thresholds(self, df, base_threshold):
        """Aplica threshold inteligente baseado na distribuição dos dados"""
        if df.empty or 'similarity' not in df.columns:
            return df
        
        # Análise estatística da distribuição
        Q1 = df['similarity'].quantile(0.25)
        Q3 = df['similarity'].quantile(0.75)
        median = df['similarity'].median()
        mean = df['similarity'].mean()
        std = df['similarity'].std()
        
        # Threshold adaptativo
        adaptive_threshold = max(base_threshold, Q3 - (0.5 * std))
        adaptive_threshold = min(adaptive_threshold, mean + std)
        
        return df[df['similarity'] >= adaptive_threshold].copy()
    
    def analyze_conversion_chain(self, results, thresholds, show_details=False):
        """Análise profissional da cadeia de conversão"""
        
        analysis = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'algorithm': self.algorithm,
                'thresholds': thresholds
            },
            'raw_data': {
                'prospecoes': len(results.get('gerem_prospecoes', pd.DataFrame())),
                'negociacoes': len(results.get('gerem_negociacoes', pd.DataFrame())),
                'projetos': len(results.get('gerem_projetos', pd.DataFrame()))
            },
            'filtered_data': {},
            'conversions': {},
            'kpis': {},
            'insights': []
        }
        
        # Processar cada etapa
        stages = {
            'prospecoes': ('gerem_prospecoes', 'Interações → Prospecções'),
            'negociacoes': ('gerem_negociacoes', 'Interações → Negociações'),
            'projetos': ('gerem_projetos', 'Interações → Projetos')
        }
        
        total_gerem_interactions = 0
        filtered_results = {}
        
        for stage, (key, label) in stages.items():
            if key in results and not results[key].empty:
                df = results[key]
                threshold = thresholds[stage]
                
                # Aplicar threshold
                filtered_df = self.apply_intelligent_thresholds(df, threshold)
                filtered_results[stage] = filtered_df
                
                # Estatísticas
                analysis['filtered_data'][stage] = {
                    'total_matches': len(filtered_df),
                    'avg_similarity': filtered_df['similarity'].mean() if not filtered_df.empty else 0,
                    'min_similarity': filtered_df['similarity'].min() if not filtered_df.empty else 0,
                    'max_similarity': filtered_df['similarity'].max() if not filtered_df.empty else 0,
                    'unique_gerem_ids': len(filtered_df['source_id'].unique()) if not filtered_df.empty else 0,
                    'threshold_used': threshold
                }
                
                # Atualizar total de interações GEREM
                if not df.empty:
                    total_gerem_interactions = max(total_gerem_interactions, len(df['source_id'].unique()))
        
        # Calcular KPIs principais
        analysis['kpis'] = {
            'total_gerem_interactions': total_gerem_interactions,
            'conversion_to_prospects': analysis['filtered_data'].get('prospecoes', {}).get('unique_gerem_ids', 0),
            'conversion_to_negotiations': analysis['filtered_data'].get('negociacoes', {}).get('unique_gerem_ids', 0),
            'conversion_to_projects': analysis['filtered_data'].get('projetos', {}).get('unique_gerem_ids', 0)
        }
        
        # Taxas de conversão
        if total_gerem_interactions > 0:
            analysis['kpis']['conversion_rate_prospects'] = (analysis['kpis']['conversion_to_prospects'] / total_gerem_interactions) * 100
            analysis['kpis']['conversion_rate_negotiations'] = (analysis['kpis']['conversion_to_negotiations'] / total_gerem_interactions) * 100
            analysis['kpis']['conversion_rate_projects'] = (analysis['kpis']['conversion_to_projects'] / total_gerem_interactions) * 100
        else:
            analysis['kpis']['conversion_rate_prospects'] = 0
            analysis['kpis']['conversion_rate_negotiations'] = 0
            analysis['kpis']['conversion_rate_projects'] = 0
        
        # Insights automáticos
        self._generate_insights(analysis)
        
        return analysis
    
    def _generate_insights(self, analysis):
        """Gera insights automáticos baseados nos dados"""
        insights = []
        kpis = analysis['kpis']
        
        # Insight sobre taxa de conversão geral
        if kpis['conversion_rate_projects'] > 15:
            insights.append({
                'type': 'success',
                'title': 'Alta Taxa de Conversão',
                'message': f"A taxa de conversão para projetos de {kpis['conversion_rate_projects']:.1f}% está acima da média esperada."
            })
        elif kpis['conversion_rate_projects'] < 5:
            insights.append({
                'type': 'warning',
                'title': 'Baixa Taxa de Conversão',
                'message': f"A taxa de conversão para projetos de {kpis['conversion_rate_projects']:.1f}% pode indicar necessidade de otimização."
            })
        
        # Insight sobre qualidade dos matches
        project_quality = analysis['filtered_data'].get('projetos', {}).get('avg_similarity', 0)
        if project_quality > 0.85:
            insights.append({
                'type': 'success',
                'title': 'Alta Qualidade dos Matches',
                'message': f"Similaridade média de {project_quality:.3f} indica matches de alta qualidade para projetos."
            })
        
        # Insight sobre eficiência do funil
        if kpis['conversion_rate_prospects'] > 0 and kpis['conversion_rate_projects'] > 0:
            efficiency = (kpis['conversion_rate_projects'] / kpis['conversion_rate_prospects']) * 100
            if efficiency > 50:
                insights.append({
                    'type': 'success',
                    'title': 'Funil Eficiente',
                    'message': f"Alta eficiência de conversão: {efficiency:.1f}% das prospecções chegam a projeto."
                })
        
        analysis['insights'] = insights

def render_header():
    """Renderiza o cabeçalho profissional"""
    st.markdown("""
    <div class="main-header">
        <h1>🎯 GEREM Chain Analysis</h1>
        <p>Dashboard Executivo de Análise da Cadeia de Conversão</p>
        <p><em>Powered by Advanced Embedding Analysis</em></p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(analyzer):
    """Renderiza a sidebar com configurações"""
    st.sidebar.markdown('<p class="sidebar-title">⚙️ Configurações</p>', unsafe_allow_html=True)
    
    # Carregar dados
    if st.sidebar.button("🔄 Carregar Dados", use_container_width=True):
        st.session_state.results = analyzer.load_embedding_results()
        st.session_state.data_loaded = True
        st.sidebar.success("✅ Dados carregados!")
    
    st.sidebar.markdown("---")
    
    # Status dos dados
    if 'data_loaded' in st.session_state and st.session_state.data_loaded:
        st.sidebar.markdown("**📊 Status dos Dados**")
        results = st.session_state.get('results', {})
        
        for stage, label in [('gerem_prospecoes', 'Prospecções'), 
                           ('gerem_negociacoes', 'Negociações'), 
                           ('gerem_projetos', 'Projetos')]:
            if stage in results and not results[stage].empty:
                count = len(results[stage])
                st.sidebar.markdown(f'<span class="status-indicator status-success"></span>{label}: {count:,} registros', unsafe_allow_html=True)
            else:
                st.sidebar.markdown(f'<span class="status-indicator status-danger"></span>{label}: Sem dados', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Configurações de threshold
    st.sidebar.markdown("**🎯 Thresholds de Similaridade**")
    st.sidebar.markdown("*Configurações para algoritmo de embedding*")
    
    thresholds = {}
    
    thresholds['prospecoes'] = st.sidebar.slider(
        "🎯 Prospecções",
        min_value=0.50,
        max_value=0.95,
        value=0.75,
        step=0.05,
        help="Threshold mínimo para considerar match válido entre GEREM e Prospecções"
    )
    
    thresholds['negociacoes'] = st.sidebar.slider(
        "🤝 Negociações",
        min_value=0.50,
        max_value=0.95,
        value=0.70,
        step=0.05,
        help="Threshold mínimo para considerar match válido entre GEREM e Negociações"
    )
    
    thresholds['projetos'] = st.sidebar.slider(
        "🚀 Projetos",
        min_value=0.50,
        max_value=0.95,
        value=0.75,
        step=0.05,
        help="Threshold mínimo para considerar match válido entre GEREM e Projetos"
    )
    
    st.sidebar.markdown("---")
    
    # Opções de análise
    st.sidebar.markdown("**🔍 Opções de Análise**")
    
    auto_update = st.sidebar.checkbox("🔄 Atualização Automática", value=True)
    show_details = st.sidebar.checkbox("📋 Mostrar Detalhes", value=False)
    
    return thresholds, auto_update, show_details

def render_kpi_cards(analysis):
    """Renderiza cards KPI profissionais"""
    st.markdown("## 📈 Indicadores Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    kpis = analysis['kpis']
    
    with col1:
        st.metric(
            label="📊 Total de Interações",
            value=f"{kpis['total_gerem_interactions']:,}",
            help="Total de interações GEREM analisadas"
        )
    
    with col2:
        st.metric(
            label="🎯 Taxa para Prospecções",
            value=f"{kpis['conversion_rate_prospects']:.1f}%",
            delta=f"{kpis['conversion_to_prospects']:,} conversões",
            help="Percentual de interações que resultaram em prospecções"
        )
    
    with col3:
        st.metric(
            label="🤝 Taxa para Negociações", 
            value=f"{kpis['conversion_rate_negotiations']:.1f}%",
            delta=f"{kpis['conversion_to_negotiations']:,} conversões",
            help="Percentual de interações que resultaram em negociações"
        )
    
    with col4:
        st.metric(
            label="🚀 Taxa para Projetos",
            value=f"{kpis['conversion_rate_projects']:.1f}%",
            delta=f"{kpis['conversion_to_projects']:,} conversões",
            help="Percentual de interações que resultaram em projetos"
        )

def render_insights(analysis):
    """Renderiza insights automáticos"""
    if analysis['insights']:
        st.markdown("## 💡 Insights Automáticos")
        
        for insight in analysis['insights']:
            if insight['type'] == 'success':
                st.success(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'warning':
                st.warning(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'info':
                st.info(f"**{insight['title']}**: {insight['message']}")

def render_conversion_funnel(analysis):
    """Renderiza funil de conversão profissional"""
    st.markdown("## 🔀 Funil de Conversão")
    
    kpis = analysis['kpis']
    
    # Dados do funil
    stages = ['Interações GEREM', 'Prospecções', 'Negociações', 'Projetos']
    values = [
        kpis['total_gerem_interactions'],
        kpis['conversion_to_prospects'],
        kpis['conversion_to_negotiations'],
        kpis['conversion_to_projects']
    ]
    
    colors = ['#1f4e79', '#2e6da4', '#4a90b8', '#28a745']
    
    # Gráfico de funil com Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Funnel(
        y=stages,
        x=values,
        texttemplate="%{label}<br>%{value:,}<br>(%{percentInitial})",
        textposition="inside",
        textfont=dict(size=14, color="white"),
        marker=dict(
            color=colors,
            line=dict(width=2, color="white")
        ),
        connector=dict(line=dict(color="rgb(63, 63, 63)", dash="dot", width=3))
    ))
    
    fig.update_layout(
        title={
            'text': "Funil de Conversão GEREM → Projetos",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        height=500,
        font=dict(family="Arial", size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_detailed_analysis(analysis):
    """Renderiza análise detalhada"""
    st.markdown("## 📊 Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - conversões por etapa
        stages = ['Prospecções', 'Negociações', 'Projetos']
        conversions = [
            analysis['kpis']['conversion_to_prospects'],
            analysis['kpis']['conversion_to_negotiations'],
            analysis['kpis']['conversion_to_projects']
        ]
        
        fig_bar = px.bar(
            x=stages,
            y=conversions,
            title="Conversões por Etapa",
            labels={'x': 'Etapa', 'y': 'Número de Conversões'},
            color=conversions,
            color_continuous_scale='Blues'
        )
        
        fig_bar.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Gráfico de pizza - distribuição de conversões
        labels = ['Não Convertidas', 'Prospecções', 'Negociações', 'Projetos']
        
        total = analysis['kpis']['total_gerem_interactions']
        not_converted = total - analysis['kpis']['conversion_to_prospects']
        
        values = [
            not_converted,
            analysis['kpis']['conversion_to_prospects'] - analysis['kpis']['conversion_to_negotiations'],
            analysis['kpis']['conversion_to_negotiations'] - analysis['kpis']['conversion_to_projects'],
            analysis['kpis']['conversion_to_projects']
        ]
        
        fig_pie = px.pie(
            values=values,
            names=labels,
            title="Distribuição de Conversões",
            color_discrete_sequence=['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
        )
        
        fig_pie.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

def render_quality_metrics(analysis):
    """Renderiza métricas de qualidade"""
    st.markdown("## 🎯 Métricas de Qualidade")
    
    col1, col2, col3 = st.columns(3)
    
    stages = ['prospecoes', 'negociacoes', 'projetos']
    labels = ['Prospecções', 'Negociações', 'Projetos']
    
    for i, (stage, label) in enumerate(zip(stages, labels)):
        with [col1, col2, col3][i]:
            if stage in analysis['filtered_data']:
                data = analysis['filtered_data'][stage]
                
                st.markdown(f"### {label}")
                st.metric("Avg. Similaridade", f"{data['avg_similarity']:.3f}")
                st.metric("Total Matches", f"{data['total_matches']:,}")
                st.metric("Threshold Usado", f"{data['threshold_used']:.2f}")
                
                # Mini gráfico de qualidade
                quality_score = data['avg_similarity'] * 100
                color = '#2ecc71' if quality_score > 80 else '#f39c12' if quality_score > 60 else '#e74c3c'
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=quality_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Qualidade"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0, 60], 'color': "lightgray"},
                            {'range': [60, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "lightgreen"}
                        ]
                    }
                ))
                
                fig_gauge.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

def render_export_section(analysis):
    """Renderiza seção de exportação"""
    st.markdown("## 💾 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with col1:
        if st.button("📊 Exportar Dashboard (JSON)", use_container_width=True):
            filename = f"gerem_analysis_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
            st.success(f"✅ Dashboard exportado: {filename}")
    
    with col2:
        if st.button("📈 Relatório Executivo (Excel)", use_container_width=True):
            filename = f"gerem_executive_report_{timestamp}.xlsx"
            
            # Criar relatório executivo
            executive_summary = {
                'KPI': ['Total de Interações', 'Taxa de Conversão para Projetos', 'Qualidade Média', 'Algoritmo Usado'],
                'Valor': [
                    f"{analysis['kpis']['total_gerem_interactions']:,}",
                    f"{analysis['kpis']['conversion_rate_projects']:.1f}%",
                    f"{np.mean([analysis['filtered_data'][s]['avg_similarity'] for s in analysis['filtered_data']]):.3f}",
                    "Embedding"
                ]
            }
            
            df_summary = pd.DataFrame(executive_summary)
            df_summary.to_excel(filename, index=False, sheet_name='Executive Summary')
            
            st.success(f"✅ Relatório executivo: {filename}")
    
    with col3:
        if st.button("📋 Dados Detalhados (CSV)", use_container_width=True):
            st.info("Funcionalidade em desenvolvimento")

def main():
    """Função principal da aplicação"""
    render_header()
    
    # Inicializar analisador
    analyzer = ProfessionalChainAnalyzer()
    
    # Renderizar sidebar
    thresholds, auto_update, show_details = render_sidebar(analyzer)
    
    # Verificar se dados foram carregados
    if 'data_loaded' not in st.session_state:
        st.info("👈 Use a barra lateral para carregar os dados e começar a análise")
        st.markdown("### 🎯 Sobre este Dashboard")
        st.markdown("""
        Este dashboard foi desenvolvido para análise profissional da cadeia de conversão GEREM:
        
        - **🔬 Foco em Embedding**: Utiliza apenas algoritmos de embedding para máxima precisão
        - **📊 KPIs Executivos**: Métricas essenciais para tomada de decisão
        - **🎯 Análise Inteligente**: Thresholds adaptativos baseados na distribuição dos dados
        - **💡 Insights Automáticos**: Detecção automática de padrões e oportunidades
        - **📈 Visualizações Profissionais**: Gráficos corporativos e interativos
        """)
        return
    
    results = st.session_state.results
    
    # Verificar se há dados carregados
    if not results:
        st.error("❌ Nenhum dado foi carregado. Verifique se os arquivos de embedding estão disponíveis.")
        return
    
    # Verificar mudanças nos parâmetros
    current_params = {'thresholds': thresholds, 'show_details': show_details}
    
    # Executar análise
    should_analyze = False
    if 'last_params' not in st.session_state:
        should_analyze = True
    elif st.session_state.last_params != current_params:
        should_analyze = True if auto_update else False
    
    # Botão manual de análise
    if st.sidebar.button("🚀 Executar Análise", use_container_width=True):
        should_analyze = True
    
    if should_analyze:
        with st.spinner("🔄 Analisando cadeia de conversão..."):
            analysis = analyzer.analyze_conversion_chain(results, thresholds, show_details)
            st.session_state.analysis = analysis
            st.session_state.last_params = current_params
            
            if auto_update:
                st.sidebar.success("✅ Análise atualizada!")
    
    # Mostrar resultados
    if 'analysis' in st.session_state:
        analysis = st.session_state.analysis
        
        # Renderizar componentes principais
        render_kpi_cards(analysis)
        render_insights(analysis)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        render_conversion_funnel(analysis)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        render_detailed_analysis(analysis)
        render_quality_metrics(analysis)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        render_export_section(analysis)
        
        # Mostrar detalhes se solicitado
        if show_details:
            with st.expander("🔍 Detalhes Técnicos", expanded=False):
                st.json(analysis)
    
    else:
        st.info("Configure os parâmetros e execute a análise para ver os resultados.")

if __name__ == "__main__":
    main()