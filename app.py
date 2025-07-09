#!/usr/bin/env python3
"""
GEREM Chain Analysis Dashboard - Cloud Version
==============================================

Versão para deploy em nuvem com upload de arquivos
Interface corporativa para análise de resultados de matching por embedding

Funcionalidades:
- Upload de arquivos de resultados
- Dashboard executivo com KPIs principais
- Análise da cadeia: GEREM → Prospecções → Negociações → Projetos
- Visualizações interativas e profissionais
- Dados de exemplo para demonstração
"""

import streamlit as st

# IMPORTANTE: st.set_page_config DEVE ser o primeiro comando Streamlit
st.set_page_config(
    page_title="GEREM Chain Analysis - Cloud",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agora podemos importar o resto
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import json
from datetime import datetime
import base64

# NÃO importar chain_analysis.py para evitar conflito com st.set_page_config()

# PostgreSQL opcional (desabilitado para Streamlit Cloud)
POSTGRESQL_AVAILABLE = False

# Função stub para PostgreSQL
def render_postgresql_config():
    return False

def upload_to_postgresql(data):
    return False

def load_from_postgresql():
    return {}

# CSS personalizado (mesmo do arquivo principal)
st.markdown("""
<style>
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
    
    .upload-section {
        background: var(--light-bg);
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px dashed var(--primary-color);
    }
    
    .demo-alert {
        background: linear-gradient(90deg, #e8f4f8, #f0f8ff);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid var(--accent-color);
        margin: 1rem 0;
    }
    
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
    
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Estilo do expander na sidebar */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        color: white !important;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background: var(--light-bg);
        border: 1px solid var(--primary-color);
        border-radius: 0 0 8px 8px;
        padding: 1rem;
        margin-top: -1px;
    }
</style>
""", unsafe_allow_html=True)

class CloudChainAnalyzer:
    """Versão cloud do analisador com upload de arquivos"""
    
    def __init__(self):
        self.results_base_path = "results"
        self.algorithm = "embedding"
        self.data_cache = {}
        self.demo_mode = True
        
        # Configurações padrão
        self.default_thresholds = {
            'prospecoes': 0.75,
            'negociacoes': 0.70,
            'projetos': 0.75
        }
    
    def create_sample_data(self):
        """Cria dados de exemplo para demonstração"""
        np.random.seed(42)  # Para reprodutibilidade
        
        sample_data = {}
        
        # Configurações para cada tipo
        configs = {
            'gerem_prospecoes': {'size': 150, 'sim_base': 0.75},
            'gerem_negociacoes': {'size': 80, 'sim_base': 0.70},
            'gerem_projetos': {'size': 45, 'sim_base': 0.78}
        }
        
        for data_type, config in configs.items():
            # Gerar similaridades com distribuição realista
            similarities = np.random.beta(3, 2, config['size']) * 0.4 + config['sim_base']
            similarities = np.clip(similarities, 0.5, 0.98)
            
            # Criar DataFrame
            df = pd.DataFrame({
                'source_id': [f"GEREM_{i+1:04d}" for i in range(config['size'])],
                'target_id': [f"{data_type.split('_')[1].upper()}_{i+1:04d}" for i in range(config['size'])],
                'similarity': similarities,
                'source_text': [f"Interação GEREM {i+1} - Exemplo de texto" for i in range(config['size'])],
                'target_text': [f"Texto {data_type.split('_')[1]} {i+1} - Exemplo" for i in range(config['size'])]
            })
            
            sample_data[data_type] = df
        
        return sample_data
    
    def load_uploaded_files(self, uploaded_files):
        """Carrega arquivos enviados pelo usuário"""
        results = {}
        
        expected_files = {
            'prospecoes': 'gerem_prospecoes',
            'negociacoes': 'gerem_negociacoes', 
            'projetos': 'gerem_projetos'
        }
        
        for uploaded_file in uploaded_files:
            # Identificar tipo do arquivo pelo nome
            file_type = None
            for key, value in expected_files.items():
                if key in uploaded_file.name.lower() or 'embedding' in uploaded_file.name.lower():
                    file_type = value
                    break
            
            if not file_type:
                st.warning(f"⚠️ Não foi possível identificar o tipo do arquivo: {uploaded_file.name}")
                continue
            
            try:
                # Ler arquivo
                if uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    st.error(f"❌ Formato não suportado: {uploaded_file.name}")
                    continue
                
                # Verificar colunas essenciais
                required_cols = ['similarity', 'source_id', 'target_id']
                if all(col in df.columns for col in required_cols):
                    results[file_type] = df
                    st.success(f"✅ Arquivo carregado: {uploaded_file.name} ({len(df)} registros)")
                else:
                    st.error(f"❌ Arquivo {uploaded_file.name} não possui as colunas necessárias: {required_cols}")
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar {uploaded_file.name}: {e}")
        
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

def render_file_upload():
    """Renderiza seção de upload de arquivos"""
    st.markdown("""
    <div class="upload-section">
        <h3>📂 Upload de Arquivos de Resultados</h3>
        <p>Faça upload dos arquivos de resultados de embedding (.xlsx ou .csv)</p>
        <p><strong>Arquivos esperados:</strong></p>
        <ul>
            <li>Arquivo com "prospecoes" no nome (resultados GEREM → Prospecções)</li>
            <li>Arquivo com "negociacoes" no nome (resultados GEREM → Negociações)</li>
            <li>Arquivo com "projetos" no nome (resultados GEREM → Projetos)</li>
        </ul>
        <p><em>Cada arquivo deve conter as colunas: similarity, source_id, target_id</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Selecione os arquivos de resultados",
        accept_multiple_files=True,
        type=['xlsx', 'csv'],
        help="Você pode selecionar múltiplos arquivos de uma vez"
    )
    
    return uploaded_files

def render_demo_mode():
    """Renderiza informações sobre o modo demo"""
    st.markdown("""
    <div class="demo-alert">
        <h4>🎯 Modo Demonstração Ativo</h4>
        <p>Você está visualizando dados de exemplo para demonstrar as funcionalidades do dashboard.</p>
        <p><strong>Para usar seus próprios dados:</strong> Faça upload dos arquivos de resultados de embedding na barra lateral.</p>
    </div>
    """, unsafe_allow_html=True)

def render_cloud_sidebar(analyzer):
    """Renderiza sidebar específica para versão cloud"""
    st.sidebar.markdown('<p style="color: #1f4e79; font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; text-align: left;">⚙️ Configurações</p>', unsafe_allow_html=True)
    
    # Seção de dados
    st.sidebar.markdown("### 📂 Fonte de Dados")
    
    # Opções de fonte de dados
    data_source = st.sidebar.radio(
        "Selecione a fonte:",
        ["📤 Upload de Arquivos", "🐘 PostgreSQL", "🎯 Dados Demo"],
        help="Escolha como carregar os dados de embedding"
    )
    
    # Processamento baseado na fonte selecionada
    if data_source == "🎯 Dados Demo":
        if st.sidebar.button("🔄 Gerar Dados Demo", use_container_width=True):
            st.session_state.results = analyzer.create_sample_data()
            st.session_state.data_loaded = True
            st.session_state.demo_mode = True
            st.sidebar.success("✅ Dados demo carregados!")
    
    elif data_source == "🐘 PostgreSQL":
        if POSTGRESQL_AVAILABLE:
            # Renderizar configuração PostgreSQL
            pg_connected = render_postgresql_config()
            
            if pg_connected:
                if st.sidebar.button("📥 Carregar do PostgreSQL", use_container_width=True):
                    with st.spinner("Carregando dados do PostgreSQL..."):
                        results = load_from_postgresql()
                        if results:
                            st.session_state.results = results
                            st.session_state.data_loaded = True
                            st.session_state.demo_mode = False
                            st.sidebar.success("✅ Dados carregados do PostgreSQL!")
                        else:
                            st.sidebar.error("❌ Nenhum dado encontrado no PostgreSQL")
        else:
            st.sidebar.error("❌ PostgreSQL não disponível. Instale: pip install psycopg2-binary")
    
    elif data_source == "📤 Upload de Arquivos":
        # Usar expander para economizar espaço
        with st.sidebar.expander("📤 **Configurar Upload de Arquivos**", expanded=False):
            st.markdown("**Formatos aceitos:** .xlsx, .csv")
            
            # Upload para Prospecções
            prospecoes_file = st.file_uploader(
                "🎯 Arquivo Prospecções (embedding)",
                type=['xlsx', 'csv'],
                help="Arquivo com resultados GEREM → Prospecções",
                key="prospecoes"
            )
            
            # Upload para Negociações
            negociacoes_file = st.file_uploader(
                "🤝 Arquivo Negociações (embedding)",
                type=['xlsx', 'csv'],
                help="Arquivo com resultados GEREM → Negociações",
                key="negociacoes"
            )
            
            # Upload para Projetos
            projetos_file = st.file_uploader(
                "🚀 Arquivo Projetos (embedding)",
                type=['xlsx', 'csv'],
                help="Arquivo com resultados GEREM → Projetos",
                key="projetos"
            )
            
            # Botão para processar
            uploaded_files = [f for f in [prospecoes_file, negociacoes_file, projetos_file] if f is not None]
            
            if uploaded_files:
                st.info(f"📁 {len(uploaded_files)} arquivo(s) selecionado(s)")
                
                if st.button("📤 Processar Arquivos", use_container_width=True):
                    with st.spinner("Processando arquivos..."):
                        results = {}
                        
                        # Processar cada arquivo
                        if prospecoes_file:
                            results['gerem_prospecoes'] = load_single_file(prospecoes_file, "Prospecções")
                        
                        if negociacoes_file:
                            results['gerem_negociacoes'] = load_single_file(negociacoes_file, "Negociações")
                        
                        if projetos_file:
                            results['gerem_projetos'] = load_single_file(projetos_file, "Projetos")
                        
                        st.session_state.results = results
                        st.session_state.data_loaded = True
                        st.session_state.demo_mode = False
                        st.success("✅ Arquivos processados!")
                        
                        # Opção para enviar para PostgreSQL
                        if POSTGRESQL_AVAILABLE and st.checkbox("📤 Enviar para PostgreSQL"):
                            if st.button("🚀 Enviar para BD", use_container_width=True):
                                if upload_to_postgresql(results):
                                    st.success("✅ Dados enviados para PostgreSQL!")
                                else:
                                    st.error("❌ Falha ao enviar para PostgreSQL")
            else:
                st.info("👆 Selecione pelo menos um arquivo para continuar")
    
    # Status dos dados (compacto)
    if 'data_loaded' in st.session_state and st.session_state.data_loaded:
        st.sidebar.markdown("---")
        with st.sidebar.expander("📊 **Status dos Dados**", expanded=False):
            results = st.session_state.get('results', {})
            
            for stage, label in [('gerem_prospecoes', 'Prospecções'), 
                               ('gerem_negociacoes', 'Negociações'), 
                               ('gerem_projetos', 'Projetos')]:
                if stage in results and not results[stage].empty:
                    count = len(results[stage])
                    st.markdown(f'<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #28a745; margin-right: 8px;"></span>{label}: {count:,} registros', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #dc3545; margin-right: 8px;"></span>{label}: Sem dados', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Configurações de threshold
    st.sidebar.markdown("**🎯 Thresholds de Similaridade**")
    
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

def load_single_file(uploaded_file, file_type):
    """Carrega um único arquivo de embedding"""
    try:
        # Ler arquivo
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error(f"❌ Formato não suportado: {uploaded_file.name}")
            return pd.DataFrame()
        
        # Verificar colunas essenciais
        required_cols = ['similarity', 'source_id', 'target_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Arquivo {file_type} está faltando colunas: {missing_cols}")
            st.write(f"Colunas disponíveis: {list(df.columns)}")
            return pd.DataFrame()
        
        # Verificar dados válidos
        valid_similarities = df['similarity'].notna().sum()
        if valid_similarities == 0:
            st.warning(f"⚠️ Arquivo {file_type} não possui valores válidos de similaridade")
            return pd.DataFrame()
        
        # Mostrar estatísticas
        min_sim = df['similarity'].min()
        max_sim = df['similarity'].max()
        mean_sim = df['similarity'].mean()
        
        st.success(f"✅ {file_type}: {len(df)} registros carregados")
        st.info(f"📊 Similaridade: min={min_sim:.3f}, max={max_sim:.3f}, média={mean_sim:.3f}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar {file_type}: {e}")
        return pd.DataFrame()

def render_simple_dashboard(analysis):
    """Dashboard completo e profissional"""
    # KPIs Principais
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
    
    # Insights
    if analysis['insights']:
        st.markdown("## 💡 Insights Automáticos")
        for insight in analysis['insights']:
            if insight['type'] == 'success':
                st.success(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'warning':
                st.warning(f"**{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'info':
                st.info(f"**{insight['title']}**: {insight['message']}")
    
    st.markdown('<div style="border-top: 2px solid #1f4e79; margin: 2rem 0; opacity: 0.3;"></div>', unsafe_allow_html=True)
    
    # Funil de Conversão
    st.markdown("## 🔀 Funil de Conversão")
    
    stages = ['Interações GEREM', 'Prospecções', 'Negociações', 'Projetos']
    values = [
        kpis['total_gerem_interactions'],
        kpis['conversion_to_prospects'],
        kpis['conversion_to_negotiations'],
        kpis['conversion_to_projects']
    ]
    
    fig_funnel = go.Figure()
    
    fig_funnel.add_trace(go.Funnel(
        y=stages,
        x=values,
        texttemplate="%{label}<br>%{value:,}<br>(%{percentInitial})",
        textposition="inside",
        textfont=dict(size=14, color="white"),
        marker=dict(
            color=['#1f4e79', '#2e6da4', '#4a90b8', '#28a745'],
            line=dict(width=2, color="white")
        ),
        connector=dict(line=dict(color="rgb(63, 63, 63)", dash="dot", width=3))
    ))
    
    fig_funnel.update_layout(
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
    
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    st.markdown('<div style="border-top: 2px solid #1f4e79; margin: 2rem 0; opacity: 0.3;"></div>', unsafe_allow_html=True)
    
    # Análise Detalhada
    st.markdown("## 📊 Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - conversões por etapa
        stages_bar = ['Prospecções', 'Negociações', 'Projetos']
        conversions = [
            kpis['conversion_to_prospects'],
            kpis['conversion_to_negotiations'],
            kpis['conversion_to_projects']
        ]
        
        fig_bar = px.bar(
            x=stages_bar,
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
        labels_pie = ['Não Convertidas', 'Apenas Prospecções', 'Apenas Negociações', 'Projetos']
        
        total = kpis['total_gerem_interactions']
        not_converted = total - kpis['conversion_to_prospects']
        only_prospects = kpis['conversion_to_prospects'] - kpis['conversion_to_negotiations']
        only_negotiations = kpis['conversion_to_negotiations'] - kpis['conversion_to_projects']
        projects = kpis['conversion_to_projects']
        
        values_pie = [not_converted, only_prospects, only_negotiations, projects]
        
        fig_pie = px.pie(
            values=values_pie,
            names=labels_pie,
            title="Distribuição de Conversões",
            color_discrete_sequence=['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
        )
        
        fig_pie.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Métricas de Qualidade
    st.markdown("## 🎯 Métricas de Qualidade")
    
    col1, col2, col3 = st.columns(3)
    
    stages_quality = ['prospecoes', 'negociacoes', 'projetos']
    labels_quality = ['Prospecções', 'Negociações', 'Projetos']
    
    for i, (stage, label) in enumerate(zip(stages_quality, labels_quality)):
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
            else:
                st.markdown(f"### {label}")
                st.info("Sem dados disponíveis")
    
    st.markdown('<div style="border-top: 2px solid #1f4e79; margin: 2rem 0; opacity: 0.3;"></div>', unsafe_allow_html=True)
    
    # Exportar Resultados
    st.markdown("## 💾 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with col1:
        if st.button("📊 Exportar Dashboard (JSON)", use_container_width=True):
            filename = f"gerem_analysis_{timestamp}.json"
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'summary': {
                    'total_interactions': kpis['total_gerem_interactions'],
                    'conversion_rate_projects': kpis['conversion_rate_projects'],
                    'algorithm': 'embedding'
                }
            }
            
            # Converter para JSON e oferecer download
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
    
    with col2:
        if st.button("📈 Relatório Executivo", use_container_width=True):
            # Criar relatório executivo em texto
            report = f"""
# Relatório Executivo - GEREM Chain Analysis
**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Algoritmo:** Embedding

## Resumo Executivo
- **Total de Interações:** {kpis['total_gerem_interactions']:,}
- **Taxa de Conversão para Projetos:** {kpis['conversion_rate_projects']:.1f}%
- **Conversões para Prospecções:** {kpis['conversion_to_prospects']:,}
- **Conversões para Negociações:** {kpis['conversion_to_negotiations']:,}
- **Conversões para Projetos:** {kpis['conversion_to_projects']:,}

## Insights
"""
            if analysis['insights']:
                for insight in analysis['insights']:
                    report += f"- **{insight['title']}:** {insight['message']}\n"
            else:
                report += "- Nenhum insight específico identificado automaticamente.\n"
            
            st.download_button(
                label="⬇️ Download Relatório",
                data=report,
                file_name=f"gerem_executive_report_{timestamp}.txt",
                mime="text/plain"
            )
    
    with col3:
        st.info("**Dados Seguros**\n\nTodos os dados ficam apenas na sua sessão e não são armazenados permanentemente.")

def main():
    """Função principal da aplicação cloud"""
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4e79, #2e6da4); padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white; text-align: center;">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">🎯 GEREM Chain Analysis</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Dashboard Executivo de Análise da Cadeia de Conversão</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;"><em>Powered by Advanced Embedding Analysis</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar analisador cloud
    analyzer = CloudChainAnalyzer()
    
    # Renderizar sidebar
    thresholds, auto_update, show_details = render_cloud_sidebar(analyzer)
    
    # Verificar se dados foram carregados
    if 'data_loaded' not in st.session_state:
        st.info("👈 Use a barra lateral para carregar dados de demonstração ou fazer upload de seus arquivos")
        
        # Mostrar informações sobre o dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Sobre este Dashboard")
            st.markdown("""
            Este dashboard foi desenvolvido para análise profissional da cadeia de conversão GEREM:
            
            - **🔬 Foco em Embedding**: Utiliza apenas algoritmos de embedding para máxima precisão
            - **📊 KPIs Executivos**: Métricas essenciais para tomada de decisão
            - **🎯 Análise Inteligente**: Thresholds adaptativos baseados na distribuição dos dados
            - **💡 Insights Automáticos**: Detecção automática de padrões e oportunidades
            - **📈 Visualizações Profissionais**: Gráficos corporativos e interativos
            """)
        
        with col2:
            st.markdown("### 🚀 Como Usar")
            st.markdown("""
            **Opção 1 - Demonstração:**
            1. Marque "Usar Dados de Demonstração"
            2. Clique em "Gerar Dados Demo"
            3. Execute a análise
            
            **Opção 2 - Seus Dados:**
            1. Desmarque "Usar Dados de Demonstração"
            2. Faça upload dos arquivos de embedding
            3. Configure os thresholds
            4. Execute a análise
            """)
        
        return
    
    results = st.session_state.results
    is_demo = st.session_state.get('demo_mode', True)
    
    # Mostrar alerta de demo se aplicável
    if is_demo:
        render_demo_mode()
    
    # Verificar se há dados carregados
    if not results:
        st.error("❌ Nenhum dado foi carregado. Tente novamente ou use o modo demonstração.")
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
        
        # Renderizar dashboard (versão independente)
        render_simple_dashboard(analysis)
        
        # Mostrar detalhes se solicitado
        if show_details:
            with st.expander("🔍 Detalhes Técnicos", expanded=False):
                st.json(analysis)
    
    else:
        st.info("Configure os parâmetros e execute a análise para ver os resultados.")

if __name__ == "__main__":
    main() 