#!/usr/bin/env python3
"""
Análise da Cadeia de Conversão GEREM
====================================

Script para analisar a cadeia completa:
GEREM Interações → Prospecções → Negociações → Projetos

Funcionalidades:
- Interface local para configurar thresholds de similaridade
- Análise robusta da cadeia de conversão
- Cálculo de taxa de conversão e níveis de confiança
- Visualizações interativas dos resultados
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from datetime import datetime
import json
from pathlib import Path

# Tentar importar utilitários de diagnóstico
try:
    from chain_analysis_utils import generate_diagnostic_report, display_diagnostic_report
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    st.warning("⚠️ Módulo de diagnóstico não disponível. Algumas funcionalidades avançadas podem não funcionar.")

class ChainAnalyzer:
    def __init__(self):
        """Inicializa o analisador de cadeia de conversão"""
        self.results_base_path = "results"
        self.data_cache = {}
        
    def load_latest_results(self):
        """Carrega os resultados mais recentes de cada tipo de matching"""
        results = {}
        
        # Tipos de matching para carregar
        match_types = ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos']
        
        for match_type in match_types:
            type_path = os.path.join(self.results_base_path, match_type)
            if not os.path.exists(type_path):
                st.error(f"Diretório não encontrado: {type_path}")
                continue
            
            # Encontrar a pasta mais recente
            folders = [f for f in os.listdir(type_path) if os.path.isdir(os.path.join(type_path, f))]
            if not folders:
                st.warning(f"Nenhuma pasta de resultados encontrada em: {type_path}")
                continue
            
            latest_folder = sorted(folders)[-1]
            folder_path = os.path.join(type_path, latest_folder)
            
            st.info(f"📂 Carregando de: {folder_path}")
            
            # Carregar os arquivos de matches
            algorithms = ['levenshtein', 'jaro_winkler', 'embedding']
            results[match_type] = {}
            
            for algo in algorithms:
                # Procurar diferentes possíveis nomes de arquivo
                possible_files = [
                    f'{algo}_matches.xlsx',
                    f'{algo}_matches.csv',
                    f'{algo}.xlsx',
                    f'{algo}.csv'
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
                            
                            # Verificar se as colunas essenciais existem
                            required_cols = ['similarity', 'source_id', 'target_id']
                            missing_cols = [col for col in required_cols if col not in df.columns]
                            
                            if missing_cols:
                                st.error(f"❌ Arquivo {file_path} está faltando colunas: {missing_cols}")
                                st.write(f"Colunas disponíveis: {list(df.columns)}")
                                continue
                            
                            # Verificar se há dados válidos de similaridade
                            valid_similarities = df['similarity'].notna().sum()
                            if valid_similarities == 0:
                                st.warning(f"⚠️ Arquivo {file_path} não possui valores válidos de similaridade")
                                continue
                            
                            # Mostrar estatísticas dos dados carregados
                            min_sim = df['similarity'].min()
                            max_sim = df['similarity'].max()
                            mean_sim = df['similarity'].mean()
                            
                            results[match_type][algo] = df
                            st.success(f"✅ Carregado: {match_type}/{algo} - {len(df)} matches")
                            st.write(f"   📊 Similaridade: min={min_sim:.3f}, max={max_sim:.3f}, média={mean_sim:.3f}")
                            
                            file_loaded = True
                            break
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar {file_path}: {e}")
                
                if not file_loaded:
                    st.warning(f"⚠️ Nenhum arquivo encontrado para {match_type}/{algo}")
                    st.write(f"   Procurados: {possible_files}")
                    
        return results
    
    def filter_by_similarity(self, df, threshold, debug=False):
        """Filtra matches por threshold de similaridade com debugging melhorado"""
        if df.empty:
            if debug:
                st.write("DataFrame vazio - nenhum filtro aplicado")
            return df
        
        # Verificar se a coluna similarity existe
        if 'similarity' not in df.columns:
            st.error(f"❌ Coluna 'similarity' não encontrada no DataFrame. Colunas disponíveis: {list(df.columns)}")
            return pd.DataFrame()
        
        # Aplicar filtro
        filtered_df = df[df['similarity'] >= threshold].copy()
        
        # Log do resultado do filtro apenas se debug ativado
        if debug:
            original_count = len(df)
            filtered_count = len(filtered_df)
            percentage_kept = (filtered_count / original_count * 100) if original_count > 0 else 0
            
            similarity_stats = {
                'min': df['similarity'].min(),
                'max': df['similarity'].max(),
                'mean': df['similarity'].mean(),
                'std': df['similarity'].std()
            }
            
            st.write(f"🔍 **Filtro aplicado:**")
            st.write(f"   - Threshold: ≥ {threshold:.3f}")
            st.write(f"   - Registros originais: {original_count:,}")
            st.write(f"   - Registros após filtro: {filtered_count:,}")
            st.write(f"   - Percentual mantido: {percentage_kept:.1f}%")
            st.write(f"   - Similaridade: min={similarity_stats['min']:.3f}, max={similarity_stats['max']:.3f}, média={similarity_stats['mean']:.3f}")
            
            if filtered_count == 0:
                st.warning(f"⚠️ Nenhum registro passou pelo filtro de similaridade (threshold={threshold:.3f})")
                st.write(f"   💡 Sugestão: Reduza o threshold para valores abaixo de {similarity_stats['max']:.3f}")
        
        return filtered_df
    
    def analyze_conversion_chain(self, results, thresholds, algorithms, debug=False):
        """
        Analisa a cadeia completa de conversão aplicando os thresholds configurados
        
        Args:
            results: Dicionário com resultados de matching
            thresholds: Dicionário com thresholds para cada tipo
            algorithms: Dicionário com algoritmos selecionados para cada tipo
            debug: Se True, mostra logs detalhados do processo
        
        Returns:
            Dicionário com análise da cadeia de conversão
        """
        # Container para logs de debug
        debug_container = None
        if debug:
            debug_container = st.expander("🔍 Logs Detalhados da Análise", expanded=True)
            with debug_container:
                st.write("🔄 **Iniciando análise da cadeia de conversão...**")
                st.write(f"📋 Thresholds configurados: {thresholds}")
                st.write(f"🤖 Algoritmos selecionados: {algorithms}")
        
        analysis = {
            'total_interactions': 0,
            'conversions': {
                'to_prospections': {'count': 0, 'matches': [], 'confidence': 0},
                'to_negotiations': {'count': 0, 'matches': [], 'confidence': 0},
                'to_projects': {'count': 0, 'matches': [], 'confidence': 0}
            },
            'chain_analysis': {
                'interactions_to_projects': {'count': 0, 'percentage': 0, 'confidence': 0},
                'full_chain': []
            }
        }
        
        # Verificar estrutura dos dados carregados
        if debug and debug_container:
            with debug_container:
                st.write("📊 **Verificando dados disponíveis:**")
                for match_type, data in results.items():
                    st.write(f"   - {match_type}: {list(data.keys()) if data else 'Sem dados'}")
        
        # 1. GEREM → Prospecções
        if debug and debug_container:
            with debug_container:
                st.write("\n🎯 **Processando GEREM → Prospecções**")
        
        if 'gerem_prospecoes' in results and algorithms['prospecoes'] in results['gerem_prospecoes']:
            prosp_matches = results['gerem_prospecoes'][algorithms['prospecoes']]
            
            if debug and debug_container:
                with debug_container:
                    st.write(f"   📥 Dados carregados: {len(prosp_matches)} registros")
            
            if not prosp_matches.empty:
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   🔧 Aplicando filtro de similaridade...")
                
                prosp_filtered = self.filter_by_similarity(prosp_matches, thresholds['prospecoes'], debug)
                
                analysis['conversions']['to_prospections']['count'] = len(prosp_filtered)
                analysis['conversions']['to_prospections']['matches'] = prosp_filtered.to_dict('records')
                analysis['conversions']['to_prospections']['confidence'] = prosp_filtered['similarity'].mean() if not prosp_filtered.empty else 0
                
                # IDs únicos de interações GEREM que geraram prospecções
                gerem_to_prosp_ids = set(prosp_filtered['source_id'].unique())
                
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   ✅ Resultado: {len(prosp_filtered)} matches, {len(gerem_to_prosp_ids)} IDs únicos")
            else:
                if debug and debug_container:
                    with debug_container:
                        st.warning("   ⚠️ Nenhum dado disponível para prospecções")
                gerem_to_prosp_ids = set()
        else:
            missing_key = 'gerem_prospecoes' if 'gerem_prospecoes' not in results else algorithms['prospecoes']
            if debug and debug_container:
                with debug_container:
                    st.warning(f"   ⚠️ Dados não encontrados: {missing_key}")
            gerem_to_prosp_ids = set()
        
        # 2. GEREM → Negociações
        if debug and debug_container:
            with debug_container:
                st.write("\n🤝 **Processando GEREM → Negociações**")
        
        if 'gerem_negociacoes' in results and algorithms['negociacoes'] in results['gerem_negociacoes']:
            neg_matches = results['gerem_negociacoes'][algorithms['negociacoes']]
            
            if debug and debug_container:
                with debug_container:
                    st.write(f"   📥 Dados carregados: {len(neg_matches)} registros")
            
            if not neg_matches.empty:
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   🔧 Aplicando filtro de similaridade...")
                
                neg_filtered = self.filter_by_similarity(neg_matches, thresholds['negociacoes'], debug)
                
                analysis['conversions']['to_negotiations']['count'] = len(neg_filtered)
                analysis['conversions']['to_negotiations']['matches'] = neg_filtered.to_dict('records')
                analysis['conversions']['to_negotiations']['confidence'] = neg_filtered['similarity'].mean() if not neg_filtered.empty else 0
                
                # IDs únicos de interações GEREM que geraram negociações
                gerem_to_neg_ids = set(neg_filtered['source_id'].unique())
                
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   ✅ Resultado: {len(neg_filtered)} matches, {len(gerem_to_neg_ids)} IDs únicos")
            else:
                if debug and debug_container:
                    with debug_container:
                        st.warning("   ⚠️ Nenhum dado disponível para negociações")
                gerem_to_neg_ids = set()
        else:
            missing_key = 'gerem_negociacoes' if 'gerem_negociacoes' not in results else algorithms['negociacoes']
            if debug and debug_container:
                with debug_container:
                    st.warning(f"   ⚠️ Dados não encontrados: {missing_key}")
            gerem_to_neg_ids = set()
        
        # 3. GEREM → Projetos
        if debug and debug_container:
            with debug_container:
                st.write("\n🚀 **Processando GEREM → Projetos**")
        
        if 'gerem_projetos' in results and algorithms['projetos'] in results['gerem_projetos']:
            proj_matches = results['gerem_projetos'][algorithms['projetos']]
            
            if debug and debug_container:
                with debug_container:
                    st.write(f"   📥 Dados carregados: {len(proj_matches)} registros")
            
            if not proj_matches.empty:
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   🔧 Aplicando filtro de similaridade...")
                
                proj_filtered = self.filter_by_similarity(proj_matches, thresholds['projetos'], debug)
                
                analysis['conversions']['to_projects']['count'] = len(proj_filtered)
                analysis['conversions']['to_projects']['matches'] = proj_filtered.to_dict('records')
                analysis['conversions']['to_projects']['confidence'] = proj_filtered['similarity'].mean() if not proj_filtered.empty else 0
                
                # IDs únicos de interações GEREM que geraram projetos
                gerem_to_proj_ids = set(proj_filtered['source_id'].unique())
                
                if debug and debug_container:
                    with debug_container:
                        st.write(f"   ✅ Resultado: {len(proj_filtered)} matches, {len(gerem_to_proj_ids)} IDs únicos")
            else:
                if debug and debug_container:
                    with debug_container:
                        st.warning("   ⚠️ Nenhum dado disponível para projetos")
                gerem_to_proj_ids = set()
        else:
            missing_key = 'gerem_projetos' if 'gerem_projetos' not in results else algorithms['projetos']
            if debug and debug_container:
                with debug_container:
                    st.warning(f"   ⚠️ Dados não encontrados: {missing_key}")
            gerem_to_proj_ids = set()
        
        # 4. Análise da cadeia completa
        if debug and debug_container:
            with debug_container:
                st.write("\n🔗 **Analisando cadeia completa**")
        
        full_chain_ids = gerem_to_prosp_ids.intersection(gerem_to_neg_ids).intersection(gerem_to_proj_ids)
        
        # Total de interações GEREM únicas
        all_gerem_ids = gerem_to_prosp_ids.union(gerem_to_neg_ids).union(gerem_to_proj_ids)
        
        if 'gerem_prospecoes' in results and algorithms['prospecoes'] in results['gerem_prospecoes']:
            # Usar como base o arquivo de prospecções que tem mais dados
            base_matches = results['gerem_prospecoes'][algorithms['prospecoes']]
            total_unique_gerem = len(base_matches['source_id'].unique()) if not base_matches.empty else 0
        else:
            total_unique_gerem = len(all_gerem_ids)
        
        analysis['total_interactions'] = total_unique_gerem
        analysis['chain_analysis']['interactions_to_projects']['count'] = len(gerem_to_proj_ids)
        
        if total_unique_gerem > 0:
            analysis['chain_analysis']['interactions_to_projects']['percentage'] = (len(gerem_to_proj_ids) / total_unique_gerem) * 100
        
        # Confiança baseada na média das similaridades
        confidences = []
        if analysis['conversions']['to_prospections']['confidence'] > 0:
            confidences.append(analysis['conversions']['to_prospections']['confidence'])
        if analysis['conversions']['to_negotiations']['confidence'] > 0:
            confidences.append(analysis['conversions']['to_negotiations']['confidence'])
        if analysis['conversions']['to_projects']['confidence'] > 0:
            confidences.append(analysis['conversions']['to_projects']['confidence'])
        
        analysis['chain_analysis']['interactions_to_projects']['confidence'] = np.mean(confidences) if confidences else 0
        
        # Detalhes da cadeia completa
        analysis['chain_analysis']['full_chain'] = {
            'count': len(full_chain_ids),
            'percentage': (len(full_chain_ids) / total_unique_gerem * 100) if total_unique_gerem > 0 else 0,
            'ids': list(full_chain_ids)
        }
        
        # Resumo final
        if debug and debug_container:
            with debug_container:
                st.write("\n📈 **Resumo da análise:**")
                st.write(f"   - Total de interações: {analysis['total_interactions']:,}")
                st.write(f"   - Prospecções: {analysis['conversions']['to_prospections']['count']:,}")
                st.write(f"   - Negociações: {analysis['conversions']['to_negotiations']['count']:,}")
                st.write(f"   - Projetos: {analysis['conversions']['to_projects']['count']:,}")
                st.write(f"   - Cadeia completa: {analysis['chain_analysis']['full_chain']['count']:,}")
        
        return analysis
    
    def calculate_confidence_level(self, similarity_scores):
        """
        Calcula o nível de confiança baseado nas similaridades
        
        Args:
            similarity_scores: Lista de scores de similaridade
        
        Returns:
            Tuple (confidence_percentage, confidence_level)
        """
        if not similarity_scores:
            return 0, "Sem Dados"
        
        mean_similarity = np.mean(similarity_scores)
        std_similarity = np.std(similarity_scores)
        
        # Calcular confiança baseada na média e consistência
        confidence_base = mean_similarity * 100
        consistency_penalty = std_similarity * 20  # Penalizar alta variabilidade
        confidence = max(0, confidence_base - consistency_penalty)
        
        # Categorizar nível de confiança
        if confidence >= 85:
            level = "Muito Alto"
        elif confidence >= 70:
            level = "Alto"
        elif confidence >= 55:
            level = "Médio"
        elif confidence >= 40:
            level = "Baixo"
        else:
            level = "Muito Baixo"
        
        return confidence, level

def main():
    st.set_page_config(
        page_title="Análise da Cadeia de Conversão GEREM",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Análise da Cadeia de Conversão GEREM")
    st.markdown("---")
    
    # Inicializar analisador
    analyzer = ChainAnalyzer()
    
    # Sidebar para configurações
    st.sidebar.header("⚙️ Configurações")
    
    # Carregar dados
    if st.sidebar.button("🔄 Carregar Dados"):
        with st.spinner("Carregando resultados..."):
            st.session_state.results = analyzer.load_latest_results()
    
    if 'results' not in st.session_state:
        st.info("👆 Clique em 'Carregar Dados' para começar a análise")
        return
    
    results = st.session_state.results
    
    # Configuração de thresholds
    st.sidebar.subheader("🎯 Thresholds de Similaridade")
    
    thresholds = {}
    thresholds['prospecoes'] = st.sidebar.slider(
        "Prospecções", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.05,
        help="Threshold mínimo de similaridade para considerar match válido",
        key="threshold_prospecoes"
    )
    
    thresholds['negociacoes'] = st.sidebar.slider(
        "Negociações", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.05,
        key="threshold_negociacoes"
    )
    
    thresholds['projetos'] = st.sidebar.slider(
        "Projetos", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.05,
        key="threshold_projetos"
    )
    
    # Seleção de algoritmos
    st.sidebar.subheader("🤖 Algoritmos")
    
    algorithms = {}
    available_algos = ['levenshtein', 'jaro_winkler', 'embedding']
    
    algorithms['prospecoes'] = st.sidebar.selectbox(
        "Prospecções", 
        available_algos,
        index=0,
        key="algo_prospecoes"
    )
    
    algorithms['negociacoes'] = st.sidebar.selectbox(
        "Negociações", 
        available_algos,
        index=0,
        key="algo_negociacoes"
    )
    
    algorithms['projetos'] = st.sidebar.selectbox(
        "Projetos", 
        available_algos,
        index=0,
        key="algo_projetos"
    )
    
    # Opção de atualização automática
    auto_update = st.sidebar.checkbox(
        "🔄 Atualização Automática", 
        value=True,
        help="Atualiza automaticamente quando os filtros mudarem"
    )
    
    # Opção de logs detalhados
    show_debug_logs = st.sidebar.checkbox(
        "🔍 Mostrar Logs Detalhados", 
        value=False,
        help="Exibe logs detalhados do processo de análise"
    )
    
    # Verificar se os parâmetros mudaram
    current_params = {
        'thresholds': thresholds,
        'algorithms': algorithms,
        'show_debug_logs': show_debug_logs
    }
    
    params_changed = False
    if 'last_params' not in st.session_state:
        st.session_state.last_params = current_params
        params_changed = True
    elif st.session_state.last_params != current_params:
        st.session_state.last_params = current_params
        params_changed = True
    
    # Botão para executar análise manual
    manual_run = st.sidebar.button("🚀 Executar Análise")
    
    # Seção de diagnóstico
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Diagnóstico")
    
    if DIAGNOSTICS_AVAILABLE:
        if st.sidebar.button("🩺 Executar Diagnóstico Completo"):
            with st.spinner("Executando diagnóstico..."):
                diagnostic_report = generate_diagnostic_report(results, thresholds, algorithms)
                st.session_state.diagnostic_report = diagnostic_report
                st.sidebar.success("✅ Diagnóstico concluído!")
        
        if 'diagnostic_report' in st.session_state:
            if st.sidebar.button("📋 Mostrar Relatório de Diagnóstico"):
                st.session_state.show_diagnostic = True
    else:
        st.sidebar.info("Diagnóstico não disponível")
    
    # Executar análise se: botão foi clicado OU (atualização automática está ativa E parâmetros mudaram)
    should_run_analysis = manual_run or (auto_update and params_changed)
    
    if should_run_analysis and 'results' in st.session_state:
        with st.spinner("Analisando cadeia de conversão..."):
            analysis = analyzer.analyze_conversion_chain(results, thresholds, algorithms, show_debug_logs)
            st.session_state.analysis = analysis
            
            # Mostrar indicador de atualização
            if auto_update and params_changed and not manual_run:
                st.sidebar.success("✅ Análise atualizada automaticamente!")
    
    if 'analysis' not in st.session_state:
        st.info("👆 Configure os parâmetros e clique em 'Executar Análise' (ou ative a atualização automática)")
        return
    
    analysis = st.session_state.analysis
    
    # Mostrar parâmetros atuais
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Parâmetros Atuais")
    st.sidebar.write(f"**Prospecções:** {algorithms['prospecoes']} (≥{thresholds['prospecoes']:.2f})")
    st.sidebar.write(f"**Negociações:** {algorithms['negociacoes']} (≥{thresholds['negociacoes']:.2f})")
    st.sidebar.write(f"**Projetos:** {algorithms['projetos']} (≥{thresholds['projetos']:.2f})")
    
    # === DASHBOARD DE RESULTADOS ===
    
    # Seção de informações sobre filtros aplicados
    with st.expander("📋 Filtros Aplicados", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🎯 Prospecções**")
            st.write(f"Algoritmo: {algorithms['prospecoes'].title()}")
            st.write(f"Threshold: ≥{thresholds['prospecoes']:.2f}")
            st.write(f"Matches: {analysis['conversions']['to_prospections']['count']:,}")
            
        with col2:
            st.write("**🤝 Negociações**")
            st.write(f"Algoritmo: {algorithms['negociacoes'].title()}")
            st.write(f"Threshold: ≥{thresholds['negociacoes']:.2f}")
            st.write(f"Matches: {analysis['conversions']['to_negotiations']['count']:,}")
            
        with col3:
            st.write("**🚀 Projetos**")
            st.write(f"Algoritmo: {algorithms['projetos'].title()}")
            st.write(f"Threshold: ≥{thresholds['projetos']:.2f}")
            st.write(f"Matches: {analysis['conversions']['to_projects']['count']:,}")
    
    # Seção de debugging para verificar dados carregados
    with st.expander("🔍 Debug: Dados Carregados e Filtros", expanded=False):
        st.write("### Estrutura dos Dados Carregados")
        
        for match_type, data in results.items():
            st.write(f"**{match_type.upper()}:**")
            if data:
                for algo, df in data.items():
                    if not df.empty:
                        st.write(f"   - {algo}: {len(df):,} registros")
                        
                        # Mostrar estatísticas de similaridade
                        if 'similarity' in df.columns:
                            sim_stats = {
                                'min': df['similarity'].min(),
                                'max': df['similarity'].max(),
                                'mean': df['similarity'].mean(),
                                'median': df['similarity'].median()
                            }
                            st.write(f"     📊 Similaridade: min={sim_stats['min']:.3f}, max={sim_stats['max']:.3f}, média={sim_stats['mean']:.3f}")
                            
                            # Mostrar quantos registros passariam pelos thresholds atuais
                            threshold_key = match_type.split('_')[1]  # prospecoes, negociacoes, projetos
                            if threshold_key in thresholds:
                                current_threshold = thresholds[threshold_key]
                                would_pass = len(df[df['similarity'] >= current_threshold])
                                percentage = (would_pass / len(df) * 100) if len(df) > 0 else 0
                                st.write(f"     🎯 Com threshold {current_threshold:.2f}: {would_pass:,} registros ({percentage:.1f}%)")
                        else:
                            st.error(f"     ❌ Coluna 'similarity' não encontrada!")
                    else:
                        st.write(f"   - {algo}: DataFrame vazio")
            else:
                st.write("   - Nenhum dado disponível")
        
        st.write("### Verificação dos Filtros")
        st.write("Os filtros estão sendo aplicados corretamente se:")
        st.write("- ✅ Os arquivos foram carregados com sucesso")
        st.write("- ✅ A coluna 'similarity' existe em todos os DataFrames")
        st.write("- ✅ Os thresholds estão dentro do range de similaridades disponíveis")
        st.write("- ✅ O número de matches após filtro diminui quando o threshold aumenta")
        
        # Teste rápido dos filtros
        st.write("### Teste Rápido dos Filtros")
        test_type = st.selectbox("Selecione tipo para testar:", ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos'])
        test_algo = st.selectbox("Selecione algoritmo para testar:", ['levenshtein', 'jaro_winkler', 'embedding'])
        
        if test_type in results and test_algo in results[test_type]:
            test_df = results[test_type][test_algo]
            if not test_df.empty and 'similarity' in test_df.columns:
                test_threshold = st.slider("Threshold de teste:", 0.0, 1.0, 0.5, 0.05)
                
                original_count = len(test_df)
                filtered_count = len(test_df[test_df['similarity'] >= test_threshold])
                
                st.write(f"**Resultado do teste:**")
                st.write(f"- Registros originais: {original_count:,}")
                st.write(f"- Registros após filtro (≥{test_threshold:.2f}): {filtered_count:,}")
                st.write(f"- Percentual mantido: {(filtered_count/original_count*100):.1f}%")
                
                if filtered_count == 0:
                    max_sim = test_df['similarity'].max()
                    st.warning(f"⚠️ Nenhum registro passou. Similaridade máxima disponível: {max_sim:.3f}")
            else:
                st.error("❌ Dados não disponíveis ou coluna 'similarity' não encontrada")
    
    # Mostrar relatório de diagnóstico se solicitado
    if 'show_diagnostic' in st.session_state and st.session_state.show_diagnostic:
        if 'diagnostic_report' in st.session_state and DIAGNOSTICS_AVAILABLE:
            display_diagnostic_report(st.session_state.diagnostic_report)
            
            # Botão para ocultar o relatório
            if st.button("❌ Ocultar Relatório de Diagnóstico"):
                st.session_state.show_diagnostic = False
                st.rerun()
            
            st.markdown("---")
    
    # Métricas principais
    st.header("📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Interações",
            f"{analysis['total_interactions']:,}",
            help="Total de interações GEREM únicas analisadas"
        )
    
    with col2:
        proj_count = analysis['chain_analysis']['interactions_to_projects']['count']
        proj_percentage = analysis['chain_analysis']['interactions_to_projects']['percentage']
        st.metric(
            "Interações → Projetos",
            f"{proj_count:,}",
            f"{proj_percentage:.1f}%"
        )
    
    with col3:
        confidence = analysis['chain_analysis']['interactions_to_projects']['confidence']
        confidence_pct, confidence_level = analyzer.calculate_confidence_level([confidence])
        st.metric(
            "Nível de Confiança",
            f"{confidence_pct:.0f}%",
            confidence_level
        )
    
    with col4:
        full_chain_count = analysis['chain_analysis']['full_chain']['count']
        full_chain_pct = analysis['chain_analysis']['full_chain']['percentage']
        st.metric(
            "Cadeia Completa",
            f"{full_chain_count:,}",
            f"{full_chain_pct:.1f}%",
            help="Interações que passaram por todas as etapas: Prospecção → Negociação → Projeto"
        )
    
    # Funil de conversão
    st.header("🔀 Funil de Conversão")
    
    # Preparar dados para o funil
    funnel_data = {
        'Etapa': ['Interações GEREM', 'Prospecções', 'Negociações', 'Projetos'],
        'Quantidade': [
            analysis['total_interactions'],
            analysis['conversions']['to_prospections']['count'],
            analysis['conversions']['to_negotiations']['count'],
            analysis['conversions']['to_projects']['count']
        ],
        'Confiança': [
            100,  # Base
            analysis['conversions']['to_prospections']['confidence'] * 100,
            analysis['conversions']['to_negotiations']['confidence'] * 100,
            analysis['conversions']['to_projects']['confidence'] * 100
        ]
    }
    
    # Gráfico de funil
    fig_funnel = go.Figure()
    
    fig_funnel.add_trace(go.Funnel(
        y=funnel_data['Etapa'],
        x=funnel_data['Quantidade'],
        texttemplate="%{label}: %{value:,}<br>(%{percentInitial})",
        textposition="inside",
        marker=dict(
            color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
            line=dict(width=2, color="white")
        )
    ))
    
    fig_funnel.update_layout(
        title="Funil de Conversão GEREM",
        height=400
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Gráficos de análise
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - Conversões por etapa
        fig_conv = px.bar(
            x=funnel_data['Etapa'][1:],  # Excluir base
            y=funnel_data['Quantidade'][1:],
            title="Conversões por Etapa",
            labels={'x': 'Etapa', 'y': 'Quantidade'},
            color=funnel_data['Quantidade'][1:],
            color_continuous_scale='viridis'
        )
        
        fig_conv.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_conv, use_container_width=True)
    
    with col2:
        # Gráfico de confiança
        fig_conf = px.bar(
            x=funnel_data['Etapa'][1:],
            y=funnel_data['Confiança'][1:],
            title="Nível de Confiança por Etapa",
            labels={'x': 'Etapa', 'y': 'Confiança (%)'},
            color=funnel_data['Confiança'][1:],
            color_continuous_scale='RdYlGn'
        )
        
        fig_conf.update_layout(height=400, showlegend=False)
        fig_conf.update_yaxes(range=[0, 100])
        st.plotly_chart(fig_conf, use_container_width=True)
    
    # Taxa de conversão detalhada
    st.header("📊 Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Taxa de Conversão Final")
        
        total = analysis['total_interactions']
        projects = analysis['chain_analysis']['interactions_to_projects']['count']
        rate = (projects / total * 100) if total > 0 else 0
        
        # Gauge chart para taxa de conversão
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Taxa de Conversão (%)"},
            delta = {'reference': 10},  # Meta de referência
            gauge = {
                'axis': {'range': [None, 30]},  # Assumindo máximo 30%
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 15], 'color': "yellow"},
                    {'range': [15, 30], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20
                }
            }
        ))
        
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col2:
        st.subheader("🔍 Detalhamento por Algoritmo")
        
        # Tabela com detalhes dos algoritmos selecionados
        algo_details = []
        for step, algo in algorithms.items():
            if step in ['prospecoes', 'negociacoes', 'projetos']:
                step_name = step.title()
                threshold = thresholds[step]
                
                if step == 'prospecoes':
                    count = analysis['conversions']['to_prospections']['count']
                    conf = analysis['conversions']['to_prospections']['confidence']
                elif step == 'negociacoes':
                    count = analysis['conversions']['to_negotiations']['count']
                    conf = analysis['conversions']['to_negotiations']['confidence']
                else:  # projetos
                    count = analysis['conversions']['to_projects']['count']
                    conf = analysis['conversions']['to_projects']['confidence']
                
                algo_details.append({
                    'Etapa': step_name,
                    'Algoritmo': algo.title(),
                    'Threshold': f"{threshold:.2f}",
                    'Matches': f"{count:,}",
                    'Confiança': f"{conf:.3f}"
                })
        
        df_algo = pd.DataFrame(algo_details)
        st.dataframe(df_algo, use_container_width=True)
    
    # Exportar resultados
    st.header("💾 Exportar Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Exportar Análise (JSON)"):
            # Preparar dados para exportação
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'configuration': {
                    'thresholds': thresholds,
                    'algorithms': algorithms
                },
                'results': analysis,
                'summary': {
                    'total_interactions': analysis['total_interactions'],
                    'conversion_rate': rate,
                    'confidence_level': confidence_level,
                    'full_chain_count': full_chain_count,
                    'full_chain_percentage': full_chain_pct
                }
            }
            
            # Salvar arquivo
            filename = f"chain_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Análise exportada para: {filename}")
    
    with col2:
        if st.button("📈 Exportar Detalhes (Excel)"):
            # Criar Excel com múltiplas abas
            filename = f"chain_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Aba resumo
                summary_data = {
                    'Métrica': [
                        'Total de Interações',
                        'Interações → Prospecções',
                        'Interações → Negociações', 
                        'Interações → Projetos',
                        'Taxa de Conversão (%)',
                        'Cadeia Completa',
                        'Nível de Confiança'
                    ],
                    'Valor': [
                        analysis['total_interactions'],
                        analysis['conversions']['to_prospections']['count'],
                        analysis['conversions']['to_negotiations']['count'],
                        analysis['conversions']['to_projects']['count'],
                        f"{rate:.2f}%",
                        full_chain_count,
                        confidence_level
                    ]
                }
                
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Resumo', index=False)
                
                # Abas com detalhes dos matches
                for conversion_type, data in analysis['conversions'].items():
                    if data['matches']:
                        df_matches = pd.DataFrame(data['matches'])
                        sheet_name = conversion_type.replace('to_', '').title()
                        df_matches.to_excel(writer, sheet_name=sheet_name, index=False)
            
            st.success(f"✅ Detalhes exportados para: {filename}")

if __name__ == "__main__":
    main()