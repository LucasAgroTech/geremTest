"""
Utilitários para diagnóstico de problemas na análise da cadeia de conversão
"""

import pandas as pd
import numpy as np
import os
import streamlit as st

def diagnose_data_structure(results_path="results"):
    """
    Diagnostica a estrutura dos dados de resultados para identificar problemas
    
    Args:
        results_path: Caminho para a pasta de resultados
        
    Returns:
        Dictionary com diagnóstico completo
    """
    diagnosis = {
        'status': 'unknown',
        'errors': [],
        'warnings': [],
        'info': [],
        'structure': {}
    }
    
    try:
        if not os.path.exists(results_path):
            diagnosis['errors'].append(f"Pasta de resultados não encontrada: {results_path}")
            diagnosis['status'] = 'error'
            return diagnosis
        
        # Verificar estrutura de pastas
        match_types = ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos']
        
        for match_type in match_types:
            type_path = os.path.join(results_path, match_type)
            diagnosis['structure'][match_type] = {
                'exists': os.path.exists(type_path),
                'folders': [],
                'files': {}
            }
            
            if os.path.exists(type_path):
                folders = [f for f in os.listdir(type_path) if os.path.isdir(os.path.join(type_path, f))]
                diagnosis['structure'][match_type]['folders'] = sorted(folders)
                
                if folders:
                    latest_folder = sorted(folders)[-1]
                    folder_path = os.path.join(type_path, latest_folder)
                    
                    # Verificar arquivos na pasta mais recente
                    algorithms = ['levenshtein', 'jaro_winkler', 'embedding']
                    for algo in algorithms:
                        algo_files = []
                        for ext in ['xlsx', 'csv']:
                            for pattern in [f'{algo}_matches', f'{algo}']:
                                file_path = os.path.join(folder_path, f'{pattern}.{ext}')
                                if os.path.exists(file_path):
                                    algo_files.append(f'{pattern}.{ext}')
                        
                        diagnosis['structure'][match_type]['files'][algo] = algo_files
                else:
                    diagnosis['warnings'].append(f"Nenhuma pasta de resultados em {type_path}")
            else:
                diagnosis['warnings'].append(f"Pasta não encontrada: {type_path}")
        
        diagnosis['status'] = 'success'
        diagnosis['info'].append("Diagnóstico estrutural concluído")
        
    except Exception as e:
        diagnosis['errors'].append(f"Erro durante diagnóstico: {str(e)}")
        diagnosis['status'] = 'error'
    
    return diagnosis

def diagnose_similarity_data(df, threshold, description="DataFrame"):
    """
    Diagnostica dados de similaridade em um DataFrame
    
    Args:
        df: DataFrame para analisar
        threshold: Threshold para teste
        description: Descrição do DataFrame
        
    Returns:
        Dictionary com diagnóstico dos dados de similaridade
    """
    diagnosis = {
        'status': 'unknown',
        'errors': [],
        'warnings': [],
        'info': [],
        'stats': {}
    }
    
    try:
        if df.empty:
            diagnosis['warnings'].append(f"{description}: DataFrame vazio")
            diagnosis['status'] = 'warning'
            return diagnosis
        
        # Verificar colunas essenciais
        required_cols = ['similarity', 'source_id', 'target_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            diagnosis['errors'].append(f"{description}: Colunas faltando: {missing_cols}")
            diagnosis['status'] = 'error'
            return diagnosis
        
        # Estatísticas de similaridade
        similarity_col = df['similarity']
        
        # Verificar valores válidos
        valid_similarities = similarity_col.notna().sum()
        invalid_similarities = similarity_col.isna().sum()
        
        if valid_similarities == 0:
            diagnosis['errors'].append(f"{description}: Nenhum valor válido de similaridade")
            diagnosis['status'] = 'error'
            return diagnosis
        
        if invalid_similarities > 0:
            diagnosis['warnings'].append(f"{description}: {invalid_similarities} valores inválidos de similaridade")
        
        # Calcular estatísticas
        stats = {
            'count': len(df),
            'valid_similarities': valid_similarities,
            'invalid_similarities': invalid_similarities,
            'min': similarity_col.min(),
            'max': similarity_col.max(),
            'mean': similarity_col.mean(),
            'median': similarity_col.median(),
            'std': similarity_col.std(),
            'percentiles': {
                '25%': similarity_col.quantile(0.25),
                '50%': similarity_col.quantile(0.50),
                '75%': similarity_col.quantile(0.75),
                '90%': similarity_col.quantile(0.90),
                '95%': similarity_col.quantile(0.95),
                '99%': similarity_col.quantile(0.99)
            }
        }
        
        # Teste do threshold
        would_pass = len(df[df['similarity'] >= threshold])
        percentage_pass = (would_pass / len(df) * 100) if len(df) > 0 else 0
        
        stats['threshold_test'] = {
            'threshold': threshold,
            'would_pass': would_pass,
            'percentage': percentage_pass
        }
        
        diagnosis['stats'] = stats
        
        # Verificações e recomendações
        if threshold > stats['max']:
            diagnosis['errors'].append(f"{description}: Threshold ({threshold:.3f}) maior que similaridade máxima ({stats['max']:.3f})")
        elif threshold > stats['percentiles']['95%']:
            diagnosis['warnings'].append(f"{description}: Threshold ({threshold:.3f}) muito alto - apenas {percentage_pass:.1f}% dos registros passariam")
        elif percentage_pass < 1:
            diagnosis['warnings'].append(f"{description}: Threshold ({threshold:.3f}) resultaria em muito poucos matches ({would_pass})")
        
        # Verificar se há valores suspeitos
        if stats['min'] < 0 or stats['max'] > 1:
            diagnosis['warnings'].append(f"{description}: Valores de similaridade fora do range [0,1]: min={stats['min']:.3f}, max={stats['max']:.3f}")
        
        # Verificar distribuição
        if stats['std'] < 0.05:
            diagnosis['info'].append(f"{description}: Baixa variabilidade na similaridade (std={stats['std']:.3f})")
        elif stats['std'] > 0.3:
            diagnosis['info'].append(f"{description}: Alta variabilidade na similaridade (std={stats['std']:.3f})")
        
        diagnosis['status'] = 'success'
        diagnosis['info'].append(f"{description}: Análise de similaridade concluída")
        
    except Exception as e:
        diagnosis['errors'].append(f"{description}: Erro durante análise: {str(e)}")
        diagnosis['status'] = 'error'
    
    return diagnosis

def generate_diagnostic_report(results, thresholds, algorithms):
    """
    Gera um relatório completo de diagnóstico
    
    Args:
        results: Dicionário com resultados carregados
        thresholds: Dicionário com thresholds configurados
        algorithms: Dicionário com algoritmos selecionados
        
    Returns:
        Dictionary com relatório completo
    """
    report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'summary': {
            'total_issues': 0,
            'errors': 0,
            'warnings': 0,
            'status': 'unknown'
        },
        'data_structure': {},
        'similarity_analysis': {},
        'recommendations': []
    }
    
    try:
        # Diagnóstico estrutural
        structure_diag = diagnose_data_structure()
        report['data_structure'] = structure_diag
        
        # Diagnóstico de similaridade para cada combinação
        for match_type in ['gerem_prospecoes', 'gerem_negociacoes', 'gerem_projetos']:
            threshold_key = match_type.split('_')[1]  # prospecoes, negociacoes, projetos
            
            if match_type in results and threshold_key in thresholds and threshold_key in algorithms:
                algorithm = algorithms[threshold_key]
                threshold = thresholds[threshold_key]
                
                if algorithm in results[match_type]:
                    df = results[match_type][algorithm]
                    description = f"{match_type}/{algorithm}"
                    
                    sim_diag = diagnose_similarity_data(df, threshold, description)
                    report['similarity_analysis'][f"{match_type}_{algorithm}"] = sim_diag
        
        # Consolidar contadores
        all_errors = []
        all_warnings = []
        
        for section in [report['data_structure']] + list(report['similarity_analysis'].values()):
            all_errors.extend(section.get('errors', []))
            all_warnings.extend(section.get('warnings', []))
        
        report['summary']['errors'] = len(all_errors)
        report['summary']['warnings'] = len(all_warnings)
        report['summary']['total_issues'] = len(all_errors) + len(all_warnings)
        
        # Determinar status geral
        if len(all_errors) > 0:
            report['summary']['status'] = 'error'
        elif len(all_warnings) > 0:
            report['summary']['status'] = 'warning'
        else:
            report['summary']['status'] = 'success'
        
        # Gerar recomendações
        recommendations = []
        
        if len(all_errors) > 0:
            recommendations.append("❌ Existem erros críticos que impedem o funcionamento correto dos filtros")
        
        if len(all_warnings) > 0:
            recommendations.append("⚠️ Existem avisos que podem afetar a qualidade dos resultados")
        
        # Recomendações específicas baseadas na análise
        for analysis in report['similarity_analysis'].values():
            if 'stats' in analysis and 'threshold_test' in analysis['stats']:
                threshold_test = analysis['stats']['threshold_test']
                if threshold_test['percentage'] < 5:
                    recommendations.append(f"💡 Considere reduzir o threshold para obter mais resultados")
                elif threshold_test['percentage'] > 80:
                    recommendations.append(f"💡 Considere aumentar o threshold para obter resultados mais precisos")
        
        if not recommendations:
            recommendations.append("✅ Nenhuma recomendação específica - sistema funcionando adequadamente")
        
        report['recommendations'] = recommendations
        
    except Exception as e:
        report['summary']['status'] = 'error'
        report['summary']['errors'] = 1
        report['error_message'] = str(e)
    
    return report

def display_diagnostic_report(report):
    """
    Exibe o relatório de diagnóstico no Streamlit
    
    Args:
        report: Relatório gerado pela função generate_diagnostic_report
    """
    st.header("🔍 Relatório de Diagnóstico - Filtros de Similaridade")
    
    # Resumo
    summary = report['summary']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_color = {"success": "🟢", "warning": "🟡", "error": "🔴"}
        st.metric("Status Geral", f"{status_color.get(summary['status'], '⚪')} {summary['status'].title()}")
    
    with col2:
        st.metric("Total de Problemas", summary['total_issues'])
    
    with col3:
        st.metric("Erros Críticos", summary['errors'])
    
    # Detalhes por seção
    if 'data_structure' in report:
        with st.expander("📁 Estrutura de Dados", expanded=summary['status'] == 'error'):
            structure = report['data_structure']
            
            if structure['errors']:
                st.error("Erros encontrados:")
                for error in structure['errors']:
                    st.write(f"❌ {error}")
            
            if structure['warnings']:
                st.warning("Avisos:")
                for warning in structure['warnings']:
                    st.write(f"⚠️ {warning}")
            
            st.write("**Estrutura de pastas encontrada:**")
            for match_type, data in structure.get('structure', {}).items():
                st.write(f"- **{match_type}:** {'✅' if data['exists'] else '❌'}")
                if data['exists'] and data['folders']:
                    st.write(f"  - Pastas: {len(data['folders'])} (mais recente: {data['folders'][-1]})")
                    for algo, files in data.get('files', {}).items():
                        if files:
                            st.write(f"    - {algo}: {', '.join(files)}")
                        else:
                            st.write(f"    - {algo}: ❌ Nenhum arquivo encontrado")
    
    # Análise de similaridade
    if 'similarity_analysis' in report:
        with st.expander("📊 Análise de Similaridade", expanded=True):
            for analysis_key, analysis in report['similarity_analysis'].items():
                st.write(f"### {analysis_key}")
                
                if analysis['errors']:
                    for error in analysis['errors']:
                        st.error(f"❌ {error}")
                
                if analysis['warnings']:
                    for warning in analysis['warnings']:
                        st.warning(f"⚠️ {warning}")
                
                if 'stats' in analysis:
                    stats = analysis['stats']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Registros", f"{stats['count']:,}")
                    with col2:
                        st.metric("Similaridade Média", f"{stats['mean']:.3f}")
                    with col3:
                        st.metric("Range", f"{stats['min']:.3f} - {stats['max']:.3f}")
                    with col4:
                        threshold_test = stats['threshold_test']
                        st.metric("Passariam no Filtro", f"{threshold_test['would_pass']:,} ({threshold_test['percentage']:.1f}%)")
    
    # Recomendações
    st.write("### 💡 Recomendações")
    for rec in report.get('recommendations', []):
        st.write(rec)
    
    # Opção para baixar relatório
    if st.button("📥 Baixar Relatório Completo (JSON)"):
        import json
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            label="Download",
            data=report_json,
            file_name=f"diagnostic_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        ) 