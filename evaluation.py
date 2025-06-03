import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os

class MatchingEvaluator:
    def __init__(self, config=None, matching_type=None):
        """Initialize evaluator with configuration"""
        # Default configuration
        self.config = {
            'metrics': ['precision', 'recall', 'f1', 'accuracy'],
            'validation_column': 'validation',  # Column in validation data with true/false labels
            'output_path': 'evaluation_results'
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Set matching type for organizing images
        self.matching_type = matching_type or 'general'
        
        # Create output directory with matching type subdirectory
        self.type_output_path = os.path.join(self.config['output_path'], self.matching_type)
        os.makedirs(self.type_output_path, exist_ok=True)
    
    def _get_save_path(self, save_path):
        """Get the full save path with matching type subdirectory"""
        if save_path:
            return os.path.join(self.type_output_path, save_path)
        return None
    
    def evaluate_without_ground_truth(self, results_dict):
        """
        Evaluate matching algorithms without ground truth data
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            
        Returns:
            DataFrame with evaluation metrics
        """
        # Initialize results
        eval_results = []
        
        # For each algorithm
        for algo_name, matches_df in results_dict.items():
            # Skip empty results
            if matches_df.empty:
                continue
            
            # Calculate metrics
            match_count = len(matches_df)
            unique_source = matches_df['source_id'].nunique()
            unique_target = matches_df['target_id'].nunique()
            avg_similarity = matches_df['similarity'].mean()
            median_similarity = matches_df['similarity'].median()
            max_similarity = matches_df['similarity'].max()
            min_similarity = matches_df['similarity'].min()
            
            # Calculate distribution of matches per source record
            matches_per_source = matches_df.groupby('source_id').size()
            avg_matches_per_source = matches_per_source.mean()
            max_matches_per_source = matches_per_source.max()
            
            # Calculate distribution of matches per target record
            matches_per_target = matches_df.groupby('target_id').size()
            avg_matches_per_target = matches_per_target.mean()
            max_matches_per_target = matches_per_target.max()
            
            # Add to results
            eval_results.append({
                'algorithm': algo_name,
                'match_count': match_count,
                'unique_source': unique_source,
                'unique_target': unique_target,
                'avg_similarity': avg_similarity,
                'median_similarity': median_similarity,
                'max_similarity': max_similarity,
                'min_similarity': min_similarity,
                'avg_matches_per_source': avg_matches_per_source,
                'max_matches_per_source': max_matches_per_source,
                'avg_matches_per_target': avg_matches_per_target,
                'max_matches_per_target': max_matches_per_target
            })
        
        # Create DataFrame from results
        eval_df = pd.DataFrame(eval_results)
        
        return eval_df
    
    def evaluate_with_ground_truth(self, results_dict, ground_truth_df):
        """
        Evaluate matching algorithms with ground truth data
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            ground_truth_df: DataFrame with ground truth matches
            
        Returns:
            DataFrame with evaluation metrics
        """
        # Initialize results
        eval_results = []
        
        # Create set of true matches from ground truth
        true_matches = set()
        for _, row in ground_truth_df.iterrows():
            true_matches.add((row['source_id'], row['target_id']))
        
        # For each algorithm
        for algo_name, matches_df in results_dict.items():
            # Skip empty results
            if matches_df.empty:
                continue
            
            # Create set of predicted matches
            pred_matches = set()
            for _, row in matches_df.iterrows():
                pred_matches.add((row['source_id'], row['target_id']))
            
            # Calculate metrics
            true_positives = len(true_matches.intersection(pred_matches))
            false_positives = len(pred_matches - true_matches)
            false_negatives = len(true_matches - pred_matches)
            
            # Calculate precision, recall, F1
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            # Add to results
            eval_results.append({
                'algorithm': algo_name,
                'true_positives': true_positives,
                'false_positives': false_positives,
                'false_negatives': false_negatives,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            })
        
        # Create DataFrame from results
        eval_df = pd.DataFrame(eval_results)
        
        return eval_df
    
    def evaluate_pairwise_agreement(self, results_dict):
        """
        Evaluate agreement between different algorithms
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            
        Returns:
            DataFrame with pairwise agreement metrics
        """
        # Get algorithm names
        algo_names = list(results_dict.keys())
        
        # Initialize agreement matrix
        agreement_matrix = np.zeros((len(algo_names), len(algo_names)))
        
        # Calculate agreement for each pair of algorithms
        for i, algo1 in enumerate(algo_names):
            for j, algo2 in enumerate(algo_names):
                if i == j:
                    agreement_matrix[i, j] = 1.0
                    continue
                
                # Get matches for each algorithm
                matches1 = results_dict[algo1]
                matches2 = results_dict[algo2]
                
                # Skip if either algorithm has no matches
                if matches1.empty or matches2.empty:
                    agreement_matrix[i, j] = 0.0
                    continue
                
                # Create sets of matches
                match_set1 = set()
                for _, row in matches1.iterrows():
                    match_set1.add((row['source_id'], row['target_id']))
                
                match_set2 = set()
                for _, row in matches2.iterrows():
                    match_set2.add((row['source_id'], row['target_id']))
                
                # Calculate Jaccard similarity as agreement
                intersection = len(match_set1.intersection(match_set2))
                union = len(match_set1.union(match_set2))
                
                agreement = intersection / union if union > 0 else 0
                agreement_matrix[i, j] = agreement
        
        # Create DataFrame for agreement matrix
        agreement_df = pd.DataFrame(agreement_matrix, index=algo_names, columns=algo_names)
        
        return agreement_df
    
    def compare_thresholds(self, source_df, target_df, matcher, source_col, target_col, 
                          date_cols=None, thresholds=None, algorithms=None):
        """
        Compare different threshold values for matching algorithms
        
        Args:
            source_df: DataFrame with source data
            target_df: DataFrame with target data
            matcher: MatchingAlgorithms instance
            source_col: Column name in source_df to use for matching
            target_col: Column name in target_df to use for matching
            date_cols: Tuple (source_date_col, target_date_col) for date filtering
            thresholds: Dictionary of threshold values to test for each algorithm
            algorithms: List of algorithms to test
            
        Returns:
            Dictionary with threshold evaluation results
        """
        # Default thresholds
        if thresholds is None:
            thresholds = {
                'levenshtein': [0.5, 0.6, 0.7, 0.8, 0.9],
                'jaro_winkler': [0.7, 0.75, 0.8, 0.85, 0.9],
                'embedding': [0.5, 0.6, 0.7, 0.8, 0.9]
            }
        
        # Default algorithms
        if algorithms is None:
            algorithms = ['levenshtein', 'jaro_winkler', 'embedding']
        
        # Initialize results
        threshold_results = {}
        
        # For each algorithm
        for algo in algorithms:
            results = []
            
            # For each threshold
            for threshold in thresholds.get(algo, []):
                # Set threshold
                orig_threshold = matcher.config.get(f'{algo}_threshold')
                matcher.config[f'{algo}_threshold'] = threshold
                
                # Run matching
                if algo == 'levenshtein':
                    matches = matcher.levenshtein_matching(source_df, target_df, source_col, target_col, date_cols)
                elif algo == 'jaro_winkler':
                    matches = matcher.jaro_winkler_matching(source_df, target_df, source_col, target_col, date_cols)
                elif algo == 'embedding':
                    matches = matcher.embedding_matching(source_df, target_df, source_col, target_col, date_cols)
                
                # Calculate metrics
                match_count = len(matches)
                unique_source = matches['source_id'].nunique() if not matches.empty else 0
                unique_target = matches['target_id'].nunique() if not matches.empty else 0
                avg_similarity = matches['similarity'].mean() if not matches.empty else 0
                
                # Add to results
                results.append({
                    'threshold': threshold,
                    'match_count': match_count,
                    'unique_source': unique_source,
                    'unique_target': unique_target,
                    'avg_similarity': avg_similarity
                })
                
                # Restore original threshold
                matcher.config[f'{algo}_threshold'] = orig_threshold
            
            # Create DataFrame from results for this algorithm
            threshold_results[algo] = pd.DataFrame(results)
        
        return threshold_results
    
    def plot_threshold_comparison(self, threshold_results, metric='match_count', save_path=None):
        """
        Plot comparison of different thresholds
        
        Args:
            threshold_results: Dictionary with threshold evaluation results
            metric: Metric to plot
            save_path: Path to save plot
            
        Returns:
            None
        """
        plt.figure(figsize=(10, 6))
        
        # For each algorithm
        for algo, results in threshold_results.items():
            plt.plot(results['threshold'], results[metric], marker='o', label=algo)
        
        plt.xlabel('Threshold')
        plt.ylabel(metric.replace('_', ' ').title())
        plt.title(f'Effect of Threshold on {metric.replace("_", " ").title()} - {self.matching_type.title()}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        full_path = self._get_save_path(save_path)
        if full_path:
            plt.savefig(full_path)
            print(f"📊 Gráfico salvo: {full_path}")
        
        plt.show()
    
    def plot_similarity_distributions(self, results_dict, save_path=None):
        """
        Plot similarity score distributions for different algorithms
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            save_path: Path to save plot
            
        Returns:
            None
        """
        plt.figure(figsize=(10, 6))
        
        # For each algorithm
        for algo_name, matches_df in results_dict.items():
            if matches_df.empty:
                continue
                
            sns.kdeplot(matches_df['similarity'], label=algo_name)
        
        plt.xlabel('Similarity Score')
        plt.ylabel('Density')
        plt.title(f'Distribution of Similarity Scores by Algorithm - {self.matching_type.title()}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        full_path = self._get_save_path(save_path)
        if full_path:
            plt.savefig(full_path)
            print(f"📊 Gráfico salvo: {full_path}")
        
        plt.show()
    
    def plot_agreement_heatmap(self, agreement_df, save_path=None):
        """
        Plot heatmap of agreement between algorithms
        
        Args:
            agreement_df: DataFrame with pairwise agreement metrics
            save_path: Path to save plot
            
        Returns:
            None
        """
        plt.figure(figsize=(8, 6))
        
        sns.heatmap(agreement_df, annot=True, cmap='YlGnBu', vmin=0, vmax=1)
        plt.title(f'Agreement Between Matching Algorithms - {self.matching_type.title()}')
        
        full_path = self._get_save_path(save_path)
        if full_path:
            plt.savefig(full_path)
            print(f"📊 Gráfico salvo: {full_path}")
        
        plt.show()