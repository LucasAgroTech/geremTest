#!/usr/bin/env python3
"""
Main script for running matching algorithms on EMBRAPII data
"""

import os
import sys
import argparse
import json
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Import project modules
from data_loader import DataLoader
from matching_algorithms import MatchingAlgorithms
from evaluation import MatchingEvaluator
from visualization import MatchingVisualizer
from config import load_config

# Excel limits
EXCEL_MAX_ROWS = 1048576
EXCEL_MAX_COLS = 16384

def safe_save_results(df, file_path, logger, max_rows=500000):
    """
    Safely save results, using CSV for large datasets and Excel for smaller ones
    
    Args:
        df: DataFrame to save
        file_path: Base file path (without extension)
        logger: Logger instance
        max_rows: Maximum rows to include in saved file
    
    Returns:
        str: Path of saved file
    """
    if df.empty:
        logger.warning(f"Empty DataFrame, skipping save for {file_path}")
        return None
    
    # Check if DataFrame is too large
    rows, cols = df.shape
    
    # Limit rows if too many
    if rows > max_rows:
        logger.warning(f"Dataset has {rows:,} rows, limiting to top {max_rows:,} by similarity")
        if 'similarity' in df.columns:
            df = df.nlargest(max_rows, 'similarity')
        else:
            df = df.head(max_rows)
        rows = len(df)
    
    # Choose file format based on size
    if rows > EXCEL_MAX_ROWS or cols > EXCEL_MAX_COLS:
        # Use CSV for large datasets
        csv_path = file_path + '.csv'
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {rows:,} matches to CSV: {csv_path}")
        return csv_path
    else:
        # Use Excel for smaller datasets
        excel_path = file_path + '.xlsx'
        try:
            df.to_excel(excel_path, index=False)
            logger.info(f"Saved {rows:,} matches to Excel: {excel_path}")
            return excel_path
        except Exception as e:
            # Fallback to CSV if Excel fails
            logger.warning(f"Excel save failed ({e}), falling back to CSV")
            csv_path = file_path + '.csv'
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {rows:,} matches to CSV: {csv_path}")
            return csv_path

def setup_logging(config):
    """Set up logging based on configuration"""
    log_level = getattr(logging, config['logging']['level'].upper())
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger('matching')
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Create handlers
    if config['logging']['console']:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if config['logging']['file']:
        # Make sure the logs directory exists
        logs_dir = config['local_paths']['logs']
        os.makedirs(logs_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(os.path.join(logs_dir, config['logging']['file']))
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def run_gerem_prospecoes_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger):
    """Run matching between GEREM interactions and prospections"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(config['local_paths']['results'], 'gerem_prospecoes', timestamp)
    os.makedirs(results_dir, exist_ok=True)
    
    logger.info("Starting GEREM to Prospections matching")
    
    # Create specific evaluator and visualizer for prospections
    evaluator = MatchingEvaluator({
        'metrics': config['evaluation']['metrics'],
        'output_path': config['local_paths']['evaluation']
    }, matching_type='prospecoes')
    
    visualizer = MatchingVisualizer({
        'output_path': config['local_paths']['visualization'],
        'figsize': config['visualization']['figsize'],
        'palette': config['visualization']['palette'],
        'dpi': config['visualization']['dpi']
    }, matching_type='prospecoes')
    
    # Load data
    try:
        logger.info("Loading GEREM interactions data")
        gerem_df = data_loader.load_from_sharepoint(
            config['sharepoint']['data_path']['gerem_interacoes']
        )
        logger.info(f"Loaded {len(gerem_df)} GEREM interactions")
        
        logger.info("Loading prospections data")
        prospecoes_df = data_loader.load_from_sharepoint(
            config['sharepoint']['data_path']['prospeccoes']
        )
        logger.info(f"Loaded {len(prospecoes_df)} prospections")
        
        # Save copies to results directory
        gerem_df.to_excel(os.path.join(results_dir, 'gerem_input.xlsx'), index=False)
        prospecoes_df.to_excel(os.path.join(results_dir, 'prospecoes_input.xlsx'), index=False)
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise
    
    # Get column names from config
    gerem_col_map = config['matching']['column_mapping']['gerem']
    prosp_col_map = config['matching']['column_mapping']['prospeccoes']
    
    # Define source and target columns for matching
    source_col = gerem_col_map['nome_capital']
    target_col = prosp_col_map['empresa']
    
    # Define date columns for filtering
    date_cols = (gerem_col_map['data'], prosp_col_map['data'])
    
    # Initialize results dictionary
    results = {}
    
    # Run Levenshtein matching if enabled
    if config['matching']['algorithms']['levenshtein']['enabled']:
        logger.info("Running Levenshtein matching")
        matcher.config['levenshtein_threshold'] = config['matching']['algorithms']['levenshtein']['threshold']
        
        levenshtein_results = matcher.levenshtein_matching(
            gerem_df, prospecoes_df, source_col, target_col, date_cols
        )
        
        results['levenshtein'] = levenshtein_results
        logger.info(f"Found {len(levenshtein_results)} matches using Levenshtein")
        
        # Save matches to file
        safe_save_results(levenshtein_results, os.path.join(results_dir, 'levenshtein_matches'), logger)
    
    # Run Jaro-Winkler matching if enabled
    if config['matching']['algorithms']['jaro_winkler']['enabled']:
        logger.info("Running Jaro-Winkler matching")
        matcher.config['jaro_winkler_threshold'] = config['matching']['algorithms']['jaro_winkler']['threshold']
        
        jaro_winkler_results = matcher.jaro_winkler_matching(
            gerem_df, prospecoes_df, source_col, target_col, date_cols
        )
        
        results['jaro_winkler'] = jaro_winkler_results
        logger.info(f"Found {len(jaro_winkler_results)} matches using Jaro-Winkler")
        
        # Save matches to file
        safe_save_results(jaro_winkler_results, os.path.join(results_dir, 'jaro_winkler_matches'), logger)
    
    # Run Embedding matching if enabled
    if config['matching']['algorithms']['embedding']['enabled']:
        logger.info("Running Embedding matching")
        matcher.config['embedding_threshold'] = config['matching']['algorithms']['embedding']['threshold']
        matcher.config['embedding_model'] = config['matching']['algorithms']['embedding']['model']
        
        embedding_results = matcher.embedding_matching(
            gerem_df, prospecoes_df, source_col, target_col, date_cols
        )
        
        results['embedding'] = embedding_results
        logger.info(f"Found {len(embedding_results)} matches using Embeddings")
        
        # Save matches to file
        safe_save_results(embedding_results, os.path.join(results_dir, 'embedding_matches'), logger)
    
    # Evaluate results
    logger.info("Evaluating matching results")
    
    # Without ground truth
    eval_results = evaluator.evaluate_without_ground_truth(results)
    
    # Pairwise agreement
    if len(results) > 1:
        agreement_df = evaluator.evaluate_pairwise_agreement(results)
    else:
        agreement_df = None
    
    # Save evaluation results
    eval_results.to_excel(os.path.join(results_dir, 'evaluation_metrics.xlsx'), index=False)
    if agreement_df is not None:
        agreement_df.to_excel(os.path.join(results_dir, 'agreement_matrix.xlsx'))
    
    # Create visualizations if enabled
    if config['evaluation']['generate_visualizations']:
        logger.info("Generating visualizations for prospections")
        
        # Match counts
        visualizer.plot_match_counts(results, save_path='match_counts.png')
        
        # Similarity distributions
        visualizer.plot_similarity_distributions(results, save_path='similarity_distributions.png')
        
        # Agreement heatmap if applicable
        if agreement_df is not None:
            visualizer.plot_agreement_heatmap(agreement_df, save_path='agreement_heatmap.png')
        
        # Match examples
        visualizer.plot_match_examples(results, n_examples=5, save_path='match_examples.png')
        
        # Network visualization
        try:
            visualizer.plot_comparative_network(results, save_path='network_visualization.png')
        except Exception as e:
            logger.warning(f"Could not generate network visualization: {e}")
    
    # Run threshold comparison
    if config['evaluation'].get('run_threshold_comparison', True):
        logger.info("Running threshold comparison")
        threshold_results = evaluator.compare_thresholds(
            gerem_df, prospecoes_df, matcher, source_col, target_col, date_cols,
            config['matching']['threshold_test']
        )
        
        # Save threshold results
        for algo, threshold_df in threshold_results.items():
            threshold_df.to_excel(os.path.join(results_dir, f'threshold_comparison_{algo}.xlsx'), index=False)
        
        # Visualize threshold comparison
        if config['evaluation']['generate_visualizations']:
            evaluator.plot_threshold_comparison(threshold_results, metric='match_count', 
                                               save_path='threshold_comparison_match_count.png')
            evaluator.plot_threshold_comparison(threshold_results, metric='unique_source', 
                                               save_path='threshold_comparison_unique_source.png')
    else:
        logger.info("Skipping threshold comparison (disabled in config)")
        threshold_results = {}
    
    # Determine best algorithm based on criteria
    if config['evaluation']['best_algorithm_criteria'] == 'match_count':
        best_algo = eval_results.loc[eval_results['match_count'].idxmax(), 'algorithm']
    elif config['evaluation']['best_algorithm_criteria'] == 'unique_source':
        best_algo = eval_results.loc[eval_results['unique_source'].idxmax(), 'algorithm']
    else:
        # Default to first algorithm
        best_algo = eval_results.iloc[0]['algorithm']
    
    logger.info(f"Best algorithm based on {config['evaluation']['best_algorithm_criteria']}: {best_algo}")
    
    # Save best matches to separate file
    if best_algo in results:
        safe_save_results(results[best_algo], os.path.join(results_dir, 'best_matches'), logger)
    
    # Save configuration used
    with open(os.path.join(results_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=4)
    
    # Return results
    return {
        'results': results,
        'evaluation': eval_results,
        'agreement': agreement_df,
        'threshold_results': threshold_results,
        'best_algorithm': best_algo,
        'results_dir': results_dir
    }

def run_gerem_negociacoes_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger):
    """Run matching between GEREM interactions and negotiations"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(config['local_paths']['results'], 'gerem_negociacoes', timestamp)
    os.makedirs(results_dir, exist_ok=True)
    
    logger.info("Starting GEREM to Negotiations matching")
    
    # Create specific evaluator and visualizer for negotiations
    evaluator = MatchingEvaluator({
        'metrics': config['evaluation']['metrics'],
        'output_path': config['local_paths']['evaluation']
    }, matching_type='negociacoes')
    
    visualizer = MatchingVisualizer({
        'output_path': config['local_paths']['visualization'],
        'figsize': config['visualization']['figsize'],
        'palette': config['visualization']['palette'],
        'dpi': config['visualization']['dpi']
    }, matching_type='negociacoes')
    
    # Load data
    try:
        logger.info("Loading GEREM interactions data")
        gerem_df = data_loader.load_from_sharepoint(
            config['sharepoint']['data_path']['gerem_interacoes']
        )
        logger.info(f"Loaded {len(gerem_df)} GEREM interactions")
        
        logger.info("Loading and consolidating negotiations data")
        # Usar a nova função que consolida todas as planilhas de negociações
        negociacoes_df = data_loader.load_and_merge_negociacoes(
            config['sharepoint']['data_path']['negociacoes'],
            config['sharepoint']['data_path']['negociacoes_negociacoes'],
            config['sharepoint']['data_path']['info_empresas'],
            config['matching']['column_mapping']
        )
        logger.info(f"Loaded and consolidated {len(negociacoes_df)} negotiations")
        
        # Save copies to results directory
        gerem_df.to_excel(os.path.join(results_dir, 'gerem_input.xlsx'), index=False)
        negociacoes_df.to_excel(os.path.join(results_dir, 'negociacoes_input.xlsx'), index=False)
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise
    
    # Get column names from config
    gerem_col_map = config['matching']['column_mapping']['gerem']
    neg_col_map = config['matching']['column_mapping']['negociacoes']
    
    # Define source and target columns for matching
    source_col = gerem_col_map['nome_capital']
    target_col = neg_col_map['empresa']
    
    # Define date columns for filtering
    date_cols = (gerem_col_map['data'], neg_col_map['data'])
    
    # Initialize results dictionary
    results = {}
    
    # Run Levenshtein matching if enabled
    if config['matching']['algorithms']['levenshtein']['enabled']:
        logger.info("Running Levenshtein matching")
        matcher.config['levenshtein_threshold'] = config['matching']['algorithms']['levenshtein']['threshold']
        
        levenshtein_results = matcher.levenshtein_matching(
            gerem_df, negociacoes_df, source_col, target_col, date_cols
        )
        
        results['levenshtein'] = levenshtein_results
        logger.info(f"Found {len(levenshtein_results)} matches using Levenshtein")
        
        # Save matches to file
        safe_save_results(levenshtein_results, os.path.join(results_dir, 'levenshtein_matches'), logger)
    
    # Run Jaro-Winkler matching if enabled
    if config['matching']['algorithms']['jaro_winkler']['enabled']:
        logger.info("Running Jaro-Winkler matching")
        matcher.config['jaro_winkler_threshold'] = config['matching']['algorithms']['jaro_winkler']['threshold']
        
        jaro_winkler_results = matcher.jaro_winkler_matching(
            gerem_df, negociacoes_df, source_col, target_col, date_cols
        )
        
        results['jaro_winkler'] = jaro_winkler_results
        logger.info(f"Found {len(jaro_winkler_results)} matches using Jaro-Winkler")
        
        # Save matches to file
        safe_save_results(jaro_winkler_results, os.path.join(results_dir, 'jaro_winkler_matches'), logger)
    
    # Run Embedding matching if enabled
    if config['matching']['algorithms']['embedding']['enabled']:
        logger.info("Running Embedding matching")
        matcher.config['embedding_threshold'] = config['matching']['algorithms']['embedding']['threshold']
        matcher.config['embedding_model'] = config['matching']['algorithms']['embedding']['model']
        
        embedding_results = matcher.embedding_matching(
            gerem_df, negociacoes_df, source_col, target_col, date_cols
        )
        
        results['embedding'] = embedding_results
        logger.info(f"Found {len(embedding_results)} matches using Embeddings")
        
        # Save matches to file
        safe_save_results(embedding_results, os.path.join(results_dir, 'embedding_matches'), logger)
    
    # Evaluate results
    logger.info("Evaluating matching results")
    
    # Without ground truth
    eval_results = evaluator.evaluate_without_ground_truth(results)
    
    # Pairwise agreement
    if len(results) > 1:
        agreement_df = evaluator.evaluate_pairwise_agreement(results)
    else:
        agreement_df = None
    
    # Save evaluation results
    eval_results.to_excel(os.path.join(results_dir, 'evaluation_metrics.xlsx'), index=False)
    if agreement_df is not None:
        agreement_df.to_excel(os.path.join(results_dir, 'agreement_matrix.xlsx'))
    
    # Create visualizations if enabled
    if config['evaluation']['generate_visualizations']:
        logger.info("Generating visualizations for negotiations")
        
        # Match counts
        visualizer.plot_match_counts(results, save_path='match_counts.png')
        
        # Similarity distributions
        visualizer.plot_similarity_distributions(results, save_path='similarity_distributions.png')
        
        # Agreement heatmap if applicable
        if agreement_df is not None:
            visualizer.plot_agreement_heatmap(agreement_df, save_path='agreement_heatmap.png')
        
        # Match examples
        visualizer.plot_match_examples(results, n_examples=5, save_path='match_examples.png')
        
        # Network visualization
        try:
            visualizer.plot_comparative_network(results, save_path='network_visualization.png')
        except Exception as e:
            logger.warning(f"Could not generate network visualization: {e}")
    
    # Run threshold comparison
    if config['evaluation'].get('run_threshold_comparison', True):
        logger.info("Running threshold comparison")
        threshold_results = evaluator.compare_thresholds(
            gerem_df, negociacoes_df, matcher, source_col, target_col, date_cols,
            config['matching']['threshold_test']
        )
        
        # Save threshold results
        for algo, threshold_df in threshold_results.items():
            threshold_df.to_excel(os.path.join(results_dir, f'threshold_comparison_{algo}.xlsx'), index=False)
        
        # Visualize threshold comparison
        if config['evaluation']['generate_visualizations']:
            evaluator.plot_threshold_comparison(threshold_results, metric='match_count', 
                                               save_path='threshold_comparison_match_count.png')
            evaluator.plot_threshold_comparison(threshold_results, metric='unique_source', 
                                               save_path='threshold_comparison_unique_source.png')
    else:
        logger.info("Skipping threshold comparison (disabled in config)")
        threshold_results = {}
    
    # Determine best algorithm based on criteria
    if len(results) > 0:
        if config['evaluation']['best_algorithm_criteria'] == 'match_count':
            best_algo = eval_results.loc[eval_results['match_count'].idxmax(), 'algorithm']
        elif config['evaluation']['best_algorithm_criteria'] == 'unique_source':
            best_algo = eval_results.loc[eval_results['unique_source'].idxmax(), 'algorithm']
        else:
            # Default to first algorithm
            best_algo = eval_results.iloc[0]['algorithm']
        
        logger.info(f"Best algorithm based on {config['evaluation']['best_algorithm_criteria']}: {best_algo}")
        
        # Save best matches to separate file
        if best_algo in results:
            safe_save_results(results[best_algo], os.path.join(results_dir, 'best_matches'), logger)
    else:
        best_algo = 'N/A'
        logger.info("No matching algorithms produced results")
    
    # Save configuration used
    with open(os.path.join(results_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=4)
    
    # Return results
    return {
        'results': results,
        'evaluation': eval_results,
        'agreement': agreement_df,
        'threshold_results': threshold_results,
        'best_algorithm': best_algo,
        'results_dir': results_dir
    }

def run_gerem_projetos_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger):
    """Run matching between GEREM interactions and projects"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(config['local_paths']['results'], 'gerem_projetos', timestamp)
    os.makedirs(results_dir, exist_ok=True)
    
    logger.info("Starting GEREM to Projects matching")
    
    # Create specific evaluator and visualizer for projects
    evaluator = MatchingEvaluator({
        'metrics': config['evaluation']['metrics'],
        'output_path': config['local_paths']['evaluation']
    }, matching_type='projetos')
    
    visualizer = MatchingVisualizer({
        'output_path': config['local_paths']['visualization'],
        'figsize': config['visualization']['figsize'],
        'palette': config['visualization']['palette'],
        'dpi': config['visualization']['dpi']
    }, matching_type='projetos')
    
    # Load data
    try:
        logger.info("Loading GEREM interactions data")
        gerem_df = data_loader.load_from_sharepoint(
            config['sharepoint']['data_path']['gerem_interacoes']
        )
        logger.info(f"Loaded {len(gerem_df)} GEREM interactions")
        
        logger.info("Loading projects data")
        projetos_df = data_loader.load_from_sharepoint(
            config['sharepoint']['data_path']['projetos']
        )
        logger.info(f"Loaded {len(projetos_df)} projects")
        
        # Save copies to results directory
        gerem_df.to_excel(os.path.join(results_dir, 'gerem_input.xlsx'), index=False)
        projetos_df.to_excel(os.path.join(results_dir, 'projetos_input.xlsx'), index=False)
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise
    
    # Get column names from config
    gerem_col_map = config['matching']['column_mapping']['gerem']
    proj_col_map = config['matching']['column_mapping']['projetos']
    
    # Define source and target columns for matching
    source_col = gerem_col_map['nome_capital']
    target_col = proj_col_map['empresa']
    
    # Define date columns for filtering
    date_cols = (gerem_col_map['data'], proj_col_map['data'])
    
    # Initialize results dictionary
    results = {}
    
    # Run Levenshtein matching if enabled
    if config['matching']['algorithms']['levenshtein']['enabled']:
        logger.info("Running Levenshtein matching")
        matcher.config['levenshtein_threshold'] = config['matching']['algorithms']['levenshtein']['threshold']
        
        levenshtein_results = matcher.levenshtein_matching(
            gerem_df, projetos_df, source_col, target_col, date_cols
        )
        
        results['levenshtein'] = levenshtein_results
        logger.info(f"Found {len(levenshtein_results)} matches using Levenshtein")
        
        # Save matches to file
        safe_save_results(levenshtein_results, os.path.join(results_dir, 'levenshtein_matches'), logger)
    
    # Run Jaro-Winkler matching if enabled
    if config['matching']['algorithms']['jaro_winkler']['enabled']:
        logger.info("Running Jaro-Winkler matching")
        matcher.config['jaro_winkler_threshold'] = config['matching']['algorithms']['jaro_winkler']['threshold']
        
        jaro_winkler_results = matcher.jaro_winkler_matching(
            gerem_df, projetos_df, source_col, target_col, date_cols
        )
        
        results['jaro_winkler'] = jaro_winkler_results
        logger.info(f"Found {len(jaro_winkler_results)} matches using Jaro-Winkler")
        
        # Save matches to file
        safe_save_results(jaro_winkler_results, os.path.join(results_dir, 'jaro_winkler_matches'), logger)
    
    # Run Embedding matching if enabled
    if config['matching']['algorithms']['embedding']['enabled']:
        logger.info("Running Embedding matching")
        matcher.config['embedding_threshold'] = config['matching']['algorithms']['embedding']['threshold']
        matcher.config['embedding_model'] = config['matching']['algorithms']['embedding']['model']
        
        embedding_results = matcher.embedding_matching(
            gerem_df, projetos_df, source_col, target_col, date_cols
        )
        
        results['embedding'] = embedding_results
        logger.info(f"Found {len(embedding_results)} matches using Embeddings")
        
        # Save matches to file
        safe_save_results(embedding_results, os.path.join(results_dir, 'embedding_matches'), logger)
    
    # Evaluate results
    logger.info("Evaluating matching results")
    
    # Without ground truth
    eval_results = evaluator.evaluate_without_ground_truth(results)
    
    # Pairwise agreement
    if len(results) > 1:
        agreement_df = evaluator.evaluate_pairwise_agreement(results)
    else:
        agreement_df = None
    
    # Save evaluation results
    eval_results.to_excel(os.path.join(results_dir, 'evaluation_metrics.xlsx'), index=False)
    if agreement_df is not None:
        agreement_df.to_excel(os.path.join(results_dir, 'agreement_matrix.xlsx'))
    
    # Create visualizations if enabled
    if config['evaluation']['generate_visualizations']:
        logger.info("Generating visualizations for projects")
        
        # Match counts
        visualizer.plot_match_counts(results, save_path='match_counts.png')
        
        # Similarity distributions
        visualizer.plot_similarity_distributions(results, save_path='similarity_distributions.png')
        
        # Agreement heatmap if applicable
        if agreement_df is not None:
            visualizer.plot_agreement_heatmap(agreement_df, save_path='agreement_heatmap.png')
        
        # Match examples
        visualizer.plot_match_examples(results, n_examples=5, save_path='match_examples.png')
    
    # Run threshold comparison
    if config['evaluation'].get('run_threshold_comparison', True):
        logger.info("Running threshold comparison")
        threshold_results = evaluator.compare_thresholds(
            gerem_df, projetos_df, matcher, source_col, target_col, date_cols,
            config['matching']['threshold_test']
        )
        
        # Save threshold results
        for algo, threshold_df in threshold_results.items():
            threshold_df.to_excel(os.path.join(results_dir, f'threshold_comparison_{algo}.xlsx'), index=False)
        
        # Visualize threshold comparison
        if config['evaluation']['generate_visualizations']:
            evaluator.plot_threshold_comparison(threshold_results, metric='match_count', 
                                               save_path='threshold_comparison_match_count.png')
            evaluator.plot_threshold_comparison(threshold_results, metric='unique_source', 
                                               save_path='threshold_comparison_unique_source.png')
    else:
        logger.info("Skipping threshold comparison (disabled in config)")
        threshold_results = {}
    
    # Determine best algorithm based on criteria
    if config['evaluation']['best_algorithm_criteria'] == 'match_count':
        best_algo = eval_results.loc[eval_results['match_count'].idxmax(), 'algorithm']
    elif config['evaluation']['best_algorithm_criteria'] == 'unique_source':
        best_algo = eval_results.loc[eval_results['unique_source'].idxmax(), 'algorithm']
    else:
        # Default to first algorithm
        best_algo = eval_results.iloc[0]['algorithm']
    
    logger.info(f"Best algorithm based on {config['evaluation']['best_algorithm_criteria']}: {best_algo}")
    
    # Save best matches to separate file
    if best_algo in results:
        safe_save_results(results[best_algo], os.path.join(results_dir, 'best_matches'), logger)
    
    # Save configuration used
    with open(os.path.join(results_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=4)
    
    # Return results
    return {
        'results': results,
        'evaluation': eval_results,
        'agreement': agreement_df,
        'threshold_results': threshold_results,
        'best_algorithm': best_algo,
        'results_dir': results_dir
    }

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run matching algorithms on EMBRAPII data')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--mode', type=str, choices=['prospecoes', 'negociacoes', 'projetos', 'all'], 
                       default='all', help='Which matching mode to run')
    parser.add_argument('--email', type=str, help='SharePoint email (overrides .env)')
    parser.add_argument('--password', type=str, help='SharePoint password (overrides .env)')
    parser.add_argument('--no-vis', action='store_true', help='Disable visualizations')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Prepare overrides from command line
    overrides = {}
    if args.email:
        overrides['sharepoint'] = {'email': args.email}
    if args.password:
        if 'sharepoint' not in overrides:
            overrides['sharepoint'] = {}
        overrides['sharepoint']['password'] = args.password
    if args.no_vis:
        overrides['evaluation'] = {'generate_visualizations': False}
    
    # Load configuration
    config = load_config(args.config, overrides)
    
    # Set up logging
    logger = setup_logging(config)
    
    # Log startup
    logger.info("Starting EMBRAPII matching tool")
    
    # Create required directories
    for path_name, path_value in config['local_paths'].items():
        os.makedirs(path_value, exist_ok=True)
        logger.debug(f"Created directory: {path_value}")
    
    # Initialize components
    try:
        # Data loader
        logger.info("Initializing data loader")
        data_loader = DataLoader({
            'sharepoint_site': config['sharepoint']['site'],
            'sharepoint_email': config['sharepoint']['email'],
            'sharepoint_password': config['sharepoint']['password'],
            'local_data_path': config['local_paths']['data'],
            'temp_path': config['local_paths']['temp']
        })
        
        # Matching algorithms
        logger.info("Initializing matching algorithms")
        matcher = MatchingAlgorithms({
            'levenshtein_threshold': config['matching']['algorithms']['levenshtein']['threshold'],
            'jaro_winkler_threshold': config['matching']['algorithms']['jaro_winkler']['threshold'],
            'embedding_threshold': config['matching']['algorithms']['embedding']['threshold'],
            'embedding_model': config['matching']['algorithms']['embedding']['model']
        })
        
        # Evaluator
        logger.info("Initializing evaluator")
        base_evaluator = MatchingEvaluator({
            'metrics': config['evaluation']['metrics'],
            'output_path': config['local_paths']['evaluation']
        })
        
        # Visualizer
        logger.info("Initializing visualizer")
        base_visualizer = MatchingVisualizer({
            'output_path': config['local_paths']['visualization'],
            'figsize': config['visualization']['figsize'],
            'palette': config['visualization']['palette'],
            'dpi': config['visualization']['dpi']
        })
        
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        sys.exit(1)
    
    # Run matching based on mode
    try:
        if args.mode == 'prospecoes' or args.mode == 'all':
            logger.info("Running GEREM to Prospections matching")
            prospecoes_results = run_gerem_prospecoes_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger)
            logger.info(f"GEREM to Prospections matching completed. Results in {prospecoes_results['results_dir']}")
            logger.info(f"Best algorithm: {prospecoes_results['best_algorithm']}")
        
        if args.mode == 'negociacoes' or args.mode == 'all':
            logger.info("Running GEREM to Negotiations matching")
            negociacoes_results = run_gerem_negociacoes_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger)
            logger.info(f"GEREM to Negotiations matching completed. Results in {negociacoes_results['results_dir']}")
            logger.info(f"Best algorithm: {negociacoes_results['best_algorithm']}")
        
        if args.mode == 'projetos' or args.mode == 'all':
            logger.info("Running GEREM to Projects matching")
            projetos_results = run_gerem_projetos_matching(config, data_loader, matcher, base_evaluator, base_visualizer, logger)
            logger.info(f"GEREM to Projects matching completed. Results in {projetos_results['results_dir']}")
            logger.info(f"Best algorithm: {projetos_results['best_algorithm']}")
        
    except Exception as e:
        logger.error(f"Error running matching: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("All matching completed successfully")

if __name__ == '__main__':
    main()