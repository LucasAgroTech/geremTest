#!/usr/bin/env python3
"""
Validação Estatística e Análise de Confiança
===========================================

Script complementar para análises estatísticas robustas:
- Intervalos de confiança
- Testes de significância
- Análise de sensibilidade aos thresholds
- Validação cruzada
- Métricas de qualidade dos matches
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy import bootstrap
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class StatisticalValidator:
    def __init__(self):
        """Inicializa o validador estatístico"""
        self.confidence_level = 0.95
        self.bootstrap_samples = 1000
    
    def calculate_confidence_interval(self, data: List[float], confidence_level: float = 0.95) -> Tuple[float, float, float]:
        """
        Calcula intervalo de confiança usando bootstrap
        
        Args:
            data: Lista de valores
            confidence_level: Nível de confiança (default: 0.95)
        
        Returns:
            Tuple (lower_bound, mean, upper_bound)
        """
        if not data:
            return 0, 0, 0
        
        data_array = np.array(data)
        
        # Bootstrap para intervalo de confiança
        def statistic(x):
            return np.mean(x)
        
        rng = np.random.default_rng(42)  # Seed para reprodutibilidade
        res = bootstrap((data_array,), statistic, n_resamples=self.bootstrap_samples, 
                       confidence_level=confidence_level, random_state=rng)
        
        mean_val = np.mean(data_array)
        lower_bound = res.confidence_interval.low
        upper_bound = res.confidence_interval.high
        
        return lower_bound, mean_val, upper_bound
    
    def analyze_match_quality(self, matches_df: pd.DataFrame) -> Dict:
        """
        Analisa a qualidade dos matches usando métricas estatísticas
        
        Args:
            matches_df: DataFrame com matches e similaridades
        
        Returns:
            Dicionário com métricas de qualidade
        """
        if matches_df.empty:
            return {
                'count': 0,
                'similarity_stats': {},
                'quality_score': 0,
                'confidence_interval': (0, 0, 0),
                'distribution_analysis': {}
            }
        
        similarities = matches_df['similarity'].values
        
        # Estatísticas básicas
        similarity_stats = {
            'mean': np.mean(similarities),
            'median': np.median(similarities),
            'std': np.std(similarities),
            'min': np.min(similarities),
            'max': np.max(similarities),
            'q25': np.percentile(similarities, 25),
            'q75': np.percentile(similarities, 75),
            'iqr': np.percentile(similarities, 75) - np.percentile(similarities, 25)
        }
        
        # Intervalo de confiança
        ci_lower, ci_mean, ci_upper = self.calculate_confidence_interval(similarities.tolist())
        
        # Score de qualidade (combinação de média e consistência)
        consistency_score = 1 - (similarity_stats['std'] / similarity_stats['mean']) if similarity_stats['mean'] > 0 else 0
        quality_score = similarity_stats['mean'] * consistency_score
        
        # Análise de distribuição
        distribution_analysis = self._analyze_distribution(similarities)
        
        return {
            'count': len(matches_df),
            'similarity_stats': similarity_stats,
            'quality_score': quality_score,
            'confidence_interval': (ci_lower, ci_mean, ci_upper),
            'distribution_analysis': distribution_analysis
        }
    
    def _analyze_distribution(self, data: np.ndarray) -> Dict:
        """Analisa a distribuição dos dados de similaridade"""
        if len(data) == 0:
            return {}
        
        # Teste de normalidade
        if len(data) >= 3:
            shapiro_stat, shapiro_p = stats.shapiro(data)
        else:
            shapiro_stat, shapiro_p = 0, 1
        
        # Skewness e Kurtosis
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)
        
        return {
            'is_normal': shapiro_p > 0.05,
            'shapiro_statistic': shapiro_stat,
            'shapiro_p_value': shapiro_p,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'is_symmetric': abs(skewness) < 0.5,
            'distribution_type': self._classify_distribution(skewness, kurtosis)
        }
    
    def _classify_distribution(self, skewness: float, kurtosis: float) -> str:
        """Classifica o tipo de distribuição baseado em skewness e kurtosis"""
        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return "Normal"
        elif skewness > 0.5:
            return "Assimétrica à direita"
        elif skewness < -0.5:
            return "Assimétrica à esquerda"
        elif kurtosis > 0.5:
            return "Leptocúrtica (picos altos)"
        elif kurtosis < -0.5:
            return "Platicúrtica (picos baixos)"
        else:
            return "Não classificada"
    
    def sensitivity_analysis(self, matches_df: pd.DataFrame, threshold_range: List[float]) -> Dict:
        """
        Análise de sensibilidade: como o número de matches varia com o threshold
        
        Args:
            matches_df: DataFrame com matches
            threshold_range: Lista de thresholds para testar
        
        Returns:
            Dicionário com resultados da análise de sensibilidade
        """
        if matches_df.empty:
            return {'thresholds': threshold_range, 'counts': [0] * len(threshold_range)}
        
        counts = []
        quality_scores = []
        
        for threshold in threshold_range:
            filtered_df = matches_df[matches_df['similarity'] >= threshold]
            counts.append(len(filtered_df))
            
            if not filtered_df.empty:
                quality = self.analyze_match_quality(filtered_df)
                quality_scores.append(quality['quality_score'])
            else:
                quality_scores.append(0)
        
        # Calcular estabilidade (quão sensível é aos thresholds)
        count_changes = np.diff(counts)
        stability_score = 1 - (np.std(count_changes) / np.mean(counts)) if np.mean(counts) > 0 else 0
        
        return {
            'thresholds': threshold_range,
            'counts': counts,
            'quality_scores': quality_scores,
            'stability_score': max(0, stability_score),
            'optimal_threshold': self._find_optimal_threshold(threshold_range, counts, quality_scores)
        }
    
    def _find_optimal_threshold(self, thresholds: List[float], counts: List[int], quality_scores: List[float]) -> float:
        """Encontra o threshold ótimo balanceando quantidade e qualidade"""
        if not counts or not quality_scores:
            return 0.7  # Default
        
        # Normalizar counts e quality_scores para [0,1]
        max_count = max(counts) if max(counts) > 0 else 1
        max_quality = max(quality_scores) if max(quality_scores) > 0 else 1
        
        normalized_counts = [c / max_count for c in counts]
        normalized_quality = [q / max_quality for q in quality_scores]
        
        # Score combinado (50% quantidade, 50% qualidade)
        combined_scores = [0.5 * c + 0.5 * q for c, q in zip(normalized_counts, normalized_quality)]
        
        # Encontrar threshold com melhor score combinado
        optimal_idx = np.argmax(combined_scores)
        return thresholds[optimal_idx]
    
    def compare_algorithms(self, results_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        Compara diferentes algoritmos estatisticamente
        
        Args:
            results_dict: Dicionário {algoritmo: DataFrame de matches}
        
        Returns:
            Dicionário com comparações estatísticas
        """
        comparison = {
            'algorithms': list(results_dict.keys()),
            'quality_analysis': {},
            'statistical_tests': {},
            'ranking': []
        }
        
        # Analisar qualidade de cada algoritmo
        for algo, matches_df in results_dict.items():
            comparison['quality_analysis'][algo] = self.analyze_match_quality(matches_df)
        
        # Testes estatísticos entre pares de algoritmos
        algos = list(results_dict.keys())
        for i, algo1 in enumerate(algos):
            for j, algo2 in enumerate(algos):
                if i < j:  # Evitar comparações duplicadas
                    test_key = f"{algo1}_vs_{algo2}"
                    
                    # Extrair similaridades
                    sim1 = results_dict[algo1]['similarity'].values if not results_dict[algo1].empty else []
                    sim2 = results_dict[algo2]['similarity'].values if not results_dict[algo2].empty else []
                    
                    # Teste de Mann-Whitney U (não paramétrico)
                    if len(sim1) > 0 and len(sim2) > 0:
                        try:
                            statistic, p_value = stats.mannwhitneyu(sim1, sim2, alternative='two-sided')
                            comparison['statistical_tests'][test_key] = {
                                'test': 'Mann-Whitney U',
                                'statistic': statistic,
                                'p_value': p_value,
                                'significant': p_value < 0.05,
                                'interpretation': self._interpret_test_result(p_value, algo1, algo2, sim1, sim2)
                            }
                        except:
                            comparison['statistical_tests'][test_key] = {
                                'test': 'Mann-Whitney U',
                                'error': 'Não foi possível realizar o teste'
                            }
        
        # Ranking dos algoritmos
        ranking_data = []
        for algo in algos:
            quality = comparison['quality_analysis'][algo]
            ranking_data.append({
                'algorithm': algo,
                'quality_score': quality['quality_score'],
                'count': quality['count'],
                'mean_similarity': quality['similarity_stats'].get('mean', 0),
                'consistency': 1 - quality['similarity_stats'].get('std', 1)
            })
        
        # Ordenar por quality_score
        comparison['ranking'] = sorted(ranking_data, key=lambda x: x['quality_score'], reverse=True)
        
        return comparison
    
    def _interpret_test_result(self, p_value: float, algo1: str, algo2: str, sim1: np.ndarray, sim2: np.ndarray) -> str:
        """Interpreta o resultado do teste estatístico"""
        if p_value < 0.05:
            mean1, mean2 = np.mean(sim1), np.mean(sim2)
            if mean1 > mean2:
                return f"{algo1} produz similaridades significativamente maiores que {algo2}"
            else:
                return f"{algo2} produz similaridades significativamente maiores que {algo1}"
        else:
            return f"Não há diferença significativa entre {algo1} e {algo2}"
    
    def conversion_rate_analysis(self, total_interactions: int, conversions: int, confidence_level: float = 0.95) -> Dict:
        """
        Análise estatística da taxa de conversão
        
        Args:
            total_interactions: Total de interações
            conversions: Número de conversões
            confidence_level: Nível de confiança
        
        Returns:
            Dicionário com análise estatística da conversão
        """
        if total_interactions == 0:
            return {
                'rate': 0,
                'confidence_interval': (0, 0),
                'sample_size_adequate': False,
                'margin_of_error': 0
            }
        
        # Taxa de conversão observada
        rate = conversions / total_interactions
        
        # Intervalo de confiança binomial
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha/2)
        
        # Intervalo de confiança de Wilson
        n = total_interactions
        p = rate
        
        denominator = 1 + z_score**2 / n
        centre_adjusted_prob = (p + z_score**2 / (2*n)) / denominator
        adjusted_standard_error = np.sqrt((p*(1-p) + z_score**2/(4*n)) / n) / denominator
        
        ci_lower = centre_adjusted_prob - z_score * adjusted_standard_error
        ci_upper = centre_adjusted_prob + z_score * adjusted_standard_error
        
        # Margem de erro
        margin_of_error = z_score * adjusted_standard_error
        
        # Verificar se o tamanho da amostra é adequado
        # Regra prática: n*p >= 5 e n*(1-p) >= 5
        sample_size_adequate = (n * p >= 5) and (n * (1-p) >= 5)
        
        return {
            'rate': rate,
            'confidence_interval': (max(0, ci_lower), min(1, ci_upper)),
            'sample_size_adequate': sample_size_adequate,
            'margin_of_error': margin_of_error,
            'required_sample_size': self._calculate_required_sample_size(rate, margin_of_error, confidence_level)
        }
    
    def _calculate_required_sample_size(self, estimated_rate: float, desired_margin: float, confidence_level: float) -> int:
        """Calcula o tamanho de amostra necessário para uma margem de erro desejada"""
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha/2)
        
        # Para proporção, usar p = 0.5 se não temos estimativa (pior caso)
        p = estimated_rate if estimated_rate > 0 else 0.5
        
        n = (z_score**2 * p * (1-p)) / (desired_margin**2)
        return int(np.ceil(n))
    
    def generate_validation_report(self, chain_analysis: Dict, results_dict: Dict) -> Dict:
        """
        Gera relatório completo de validação estatística
        
        Args:
            chain_analysis: Resultado da análise de cadeia
            results_dict: Dicionário com resultados por algoritmo
        
        Returns:
            Relatório completo de validação
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'executive_summary': {},
            'detailed_analysis': {},
            'recommendations': [],
            'statistical_validation': {}
        }
        
        # Análise de conversão
        total = chain_analysis.get('total_interactions', 0)
        projects = chain_analysis.get('chain_analysis', {}).get('interactions_to_projects', {}).get('count', 0)
        
        conversion_analysis = self.conversion_rate_analysis(total, projects)
        
        # Comparação de algoritmos
        algorithm_comparison = self.compare_algorithms(results_dict)
        
        # Resumo executivo
        rate = conversion_analysis['rate']
        ci_lower, ci_upper = conversion_analysis['confidence_interval']
        
        report['executive_summary'] = {
            'conversion_rate': f"{rate:.1%}",
            'confidence_interval': f"[{ci_lower:.1%}, {ci_upper:.1%}]",
            'sample_size_adequate': conversion_analysis['sample_size_adequate'],
            'best_algorithm': algorithm_comparison['ranking'][0]['algorithm'] if algorithm_comparison['ranking'] else 'N/A',
            'statistical_significance': 'Alta' if conversion_analysis['sample_size_adequate'] else 'Baixa'
        }
        
        # Análise detalhada
        report['detailed_analysis'] = {
            'conversion_statistics': conversion_analysis,
            'algorithm_comparison': algorithm_comparison,
            'quality_metrics': {algo: self.analyze_match_quality(df) for algo, df in results_dict.items()}
        }
        
        # Recomendações
        recommendations = []
        
        if not conversion_analysis['sample_size_adequate']:
            required = conversion_analysis['required_sample_size']
            recommendations.append(f"Aumentar amostra para pelo menos {required:,} interações para maior confiabilidade estatística")
        
        if algorithm_comparison['ranking']:
            best_algo = algorithm_comparison['ranking'][0]['algorithm']
            recommendations.append(f"Usar algoritmo '{best_algo}' que apresentou melhor performance geral")
        
        if rate < 0.05:  # Taxa menor que 5%
            recommendations.append("Taxa de conversão baixa - investigar possíveis melhorias no processo")
        
        # Análise de qualidade dos matches
        for algo, quality in report['detailed_analysis']['quality_metrics'].items():
            if quality['quality_score'] < 0.5:
                recommendations.append(f"Revisar parâmetros do algoritmo '{algo}' - baixa qualidade dos matches")
        
        report['recommendations'] = recommendations
        
        # Validação estatística
        report['statistical_validation'] = {
            'confidence_level': self.confidence_level,
            'bootstrap_samples': self.bootstrap_samples,
            'tests_performed': list(algorithm_comparison['statistical_tests'].keys()),
            'validation_status': 'APROVADO' if conversion_analysis['sample_size_adequate'] else 'CONDICIONAL'
        }
        
        return report
    
    def plot_validation_charts(self, validation_report: Dict, save_path: Optional[str] = None):
        """
        Gera gráficos para o relatório de validação
        
        Args:
            validation_report: Relatório de validação
            save_path: Caminho para salvar os gráficos (opcional)
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Análise de Validação Estatística', fontsize=16, fontweight='bold')
        
        # 1. Intervalo de confiança da taxa de conversão
        ax1 = axes[0, 0]
        conv_stats = validation_report['detailed_analysis']['conversion_statistics']
        rate = conv_stats['rate']
        ci_lower, ci_upper = conv_stats['confidence_interval']
        
        ax1.bar(['Taxa de Conversão'], [rate], color='skyblue', alpha=0.7)
        ax1.errorbar(['Taxa de Conversão'], [rate], 
                    yerr=[[rate - ci_lower], [ci_upper - rate]], 
                    fmt='o', color='red', capsize=10, capthick=2)
        ax1.set_ylabel('Taxa (%)')
        ax1.set_title('Taxa de Conversão com Intervalo de Confiança')
        ax1.set_ylim(0, max(ci_upper * 1.2, 0.1))
        
        # 2. Ranking de algoritmos
        ax2 = axes[0, 1]
        algo_comp = validation_report['detailed_analysis']['algorithm_comparison']
        if algo_comp['ranking']:
            algos = [r['algorithm'] for r in algo_comp['ranking']]
            scores = [r['quality_score'] for r in algo_comp['ranking']]
            
            bars = ax2.bar(algos, scores, color='lightgreen', alpha=0.7)
            ax2.set_ylabel('Score de Qualidade')
            ax2.set_title('Ranking de Algoritmos por Qualidade')
            ax2.tick_params(axis='x', rotation=45)
            
            # Adicionar valores nas barras
            for bar, score in zip(bars, scores):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{score:.3f}', ha='center', va='bottom')
        
        # 3. Distribuição de similaridades por algoritmo
        ax3 = axes[1, 0]
        quality_metrics = validation_report['detailed_analysis']['quality_metrics']
        
        for i, (algo, metrics) in enumerate(quality_metrics.items()):
            if metrics['count'] > 0:
                stats_data = metrics['similarity_stats']
                mean_val = stats_data['mean']
                std_val = stats_data['std']
                
                # Simular distribuição normal para visualização
                x = np.linspace(max(0, mean_val - 3*std_val), min(1, mean_val + 3*std_val), 100)
                y = stats.norm.pdf(x, mean_val, std_val)
                ax3.plot(x, y, label=f'{algo} (μ={mean_val:.3f})')
        
        ax3.set_xlabel('Similaridade')
        ax3.set_ylabel('Densidade')
        ax3.set_title('Distribuição de Similaridades por Algoritmo')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Matriz de adequação estatística
        ax4 = axes[1, 1]
        
        # Criar dados para heatmap de adequação
        adequacy_data = []
        for algo, metrics in quality_metrics.items():
            adequacy = {
                'Tamanho Amostra': 1 if metrics['count'] > 30 else 0.5 if metrics['count'] > 10 else 0,
                'Qualidade Matches': min(1, metrics['quality_score']),
                'Consistência': 1 - min(1, metrics['similarity_stats'].get('std', 1))
            }
            adequacy_data.append(adequacy)
        
        if adequacy_data:
            adequacy_df = pd.DataFrame(adequacy_data, index=list(quality_metrics.keys()))
            im = ax4.imshow(adequacy_df.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
            
            # Configurar labels
            ax4.set_xticks(range(len(adequacy_df.columns)))
            ax4.set_xticklabels(adequacy_df.columns, rotation=45, ha='right')
            ax4.set_yticks(range(len(adequacy_df.index)))
            ax4.set_yticklabels(adequacy_df.index)
            ax4.set_title('Matriz de Adequação Estatística')
            
            # Adicionar colorbar
            plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Gráficos salvos em: {save_path}")
        
        plt.show()

# Função utilitária para usar com o script principal
def run_statistical_validation(chain_analysis: Dict, results_dict: Dict) -> Dict:
    """
    Função principal para executar validação estatística
    
    Args:
        chain_analysis: Resultado da análise de cadeia
        results_dict: Resultados por algoritmo
    
    Returns:
        Relatório completo de validação
    """
    validator = StatisticalValidator()
    report = validator.generate_validation_report(chain_analysis, results_dict)
    
    # Gerar gráficos
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    plot_path = f"validation_charts_{timestamp}.png"
    validator.plot_validation_charts(report, plot_path)
    
    return report

if __name__ == "__main__":
    print("Módulo de Validação Estatística carregado.")
    print("Use a função run_statistical_validation() para executar a análise completa.")