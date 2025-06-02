import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.colors import LinearSegmentedColormap

class MatchingVisualizer:
    def __init__(self, config=None):
        """Initialize visualizer with configuration"""
        # Default configuration
        self.config = {
            'output_path': 'visualization_results',
            'figsize': (12, 8),
            'palette': 'viridis',
            'dpi': 300
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config['output_path'], exist_ok=True)
    
    def plot_match_counts(self, results_dict, save_path=None):
        """
        Plot match counts for different algorithms
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            save_path: Path to save plot
            
        Returns:
            None
        """
        # Get match counts for each algorithm
        algo_names = []
        match_counts = []
        
        for algo_name, matches_df in results_dict.items():
            algo_names.append(algo_name)
            match_counts.append(len(matches_df))
        
        # Create plot
        plt.figure(figsize=self.config['figsize'])
        bars = plt.bar(algo_names, match_counts, color=sns.color_palette(self.config['palette'], len(algo_names)))
        
        # Add count labels
        for bar, count in zip(bars, match_counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.title('Number of Matches by Algorithm', fontsize=16)
        plt.xlabel('Algorithm', fontsize=14)
        plt.ylabel('Number of Matches', fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save if path provided
        if save_path:
            full_path = os.path.join(self.config['output_path'], save_path)
            plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
        
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
        plt.figure(figsize=self.config['figsize'])
        
        # For each algorithm
        for algo_name, matches_df in results_dict.items():
            if matches_df.empty:
                continue
                
            sns.kdeplot(matches_df['similarity'], label=algo_name, fill=True, alpha=0.3)
        
        plt.xlabel('Similarity Score', fontsize=14)
        plt.ylabel('Density', fontsize=14)
        plt.title('Distribution of Similarity Scores by Algorithm', fontsize=16)
        plt.legend(fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        # Save if path provided
        if save_path:
            full_path = os.path.join(self.config['output_path'], save_path)
            plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
        
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
        plt.figure(figsize=(10, 8))
        
        # Create custom colormap from white to blue
        cmap = LinearSegmentedColormap.from_list('custom_cmap', ['#ffffff', '#4a7bb7'])
        
        # Plot heatmap
        ax = sns.heatmap(agreement_df, annot=True, cmap=cmap, vmin=0, vmax=1, 
                        annot_kws={"size": 14}, fmt='.3f', linewidths=1, linecolor='white')
        
        # Set title and labels
        plt.title('Agreement Between Matching Algorithms', fontsize=16)
        plt.xticks(fontsize=12, rotation=45, ha='right')
        plt.yticks(fontsize=12, rotation=0)
        
        # Fix colorbar size
        cbar = ax.collections[0].colorbar
        cbar.ax.tick_params(labelsize=12)
        
        # Save if path provided
        if save_path:
            full_path = os.path.join(self.config['output_path'], save_path)
            plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
        
        plt.tight_layout()
        plt.show()
    
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
        plt.figure(figsize=self.config['figsize'])
        
        # Get colors from palette
        colors = sns.color_palette(self.config['palette'], len(threshold_results))
        
        # For each algorithm
        for i, (algo, results) in enumerate(threshold_results.items()):
            plt.plot(results['threshold'], results[metric], marker='o', 
                    label=algo, color=colors[i], linewidth=2, markersize=8)
        
        plt.xlabel('Threshold', fontsize=14)
        plt.ylabel(metric.replace('_', ' ').title(), fontsize=14)
        plt.title(f'Effect of Threshold on {metric.replace("_", " ").title()}', fontsize=16)
        plt.legend(fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        # Save if path provided
        if save_path:
            full_path = os.path.join(self.config['output_path'], save_path)
            plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
        
        plt.show()
    
    def plot_evaluation_metrics(self, eval_df, save_path=None):
        """
        Plot evaluation metrics for different algorithms
        
        Args:
            eval_df: DataFrame with evaluation metrics
            save_path: Path to save plot
            
        Returns:
            None
        """
        # Check if DataFrame has the expected columns
        metric_cols = ['precision', 'recall', 'f1_score']
        if not all(col in eval_df.columns for col in metric_cols):
            raise ValueError("eval_df must contain columns: precision, recall, f1_score")
        
        # Reshape DataFrame for plotting
        plot_data = []
        for _, row in eval_df.iterrows():
            for metric in metric_cols:
                plot_data.append({
                    'Algorithm': row['algorithm'],
                    'Metric': metric.capitalize(),
                    'Value': row[metric]
                })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Create plot
        plt.figure(figsize=self.config['figsize'])
        ax = sns.barplot(x='Algorithm', y='Value', hue='Metric', data=plot_df)
        
        # Add value labels
        for container in ax.containers:
            ax.bar_label(container, fmt='%.3f', fontsize=10)
        
        plt.title('Performance Metrics by Algorithm', fontsize=16)
        plt.xlabel('Algorithm', fontsize=14)
        plt.ylabel('Score', fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(title='Metric', fontsize=12, title_fontsize=14)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save if path provided
        if save_path:
            full_path = os.path.join(self.config['output_path'], save_path)
            plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
        
        plt.show()
    
    def plot_match_examples(self, results_dict, n_examples=5, save_path=None):
        """
        Plot examples of matches from different algorithms
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            n_examples: Number of examples to show per algorithm
            save_path: Path to save plot
            
        Returns:
            None
        """
        # For each algorithm
        for algo_name, matches_df in results_dict.items():
            if matches_df.empty or len(matches_df) < n_examples:
                continue
            
            # Get top n examples
            examples = matches_df.head(n_examples)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(14, n_examples*1.2))
            
            # Hide axes
            ax.axis('off')
            
            # Create table data
            table_data = []
            for _, row in examples.iterrows():
                table_data.append([
                    row['source_text'],
                    row['target_text'],
                    f"{row['similarity']:.3f}"
                ])
            
            # Create table
            table = ax.table(
                cellText=table_data,
                colLabels=['Source Text', 'Target Text', 'Similarity'],
                loc='center',
                cellLoc='center',
                colWidths=[0.4, 0.4, 0.2]
            )
            
            # Style table
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)
            
            # Color header row
            for i in range(3):
                table[(0, i)].set_facecolor('#4a7bb7')
                table[(0, i)].set_text_props(color='white', fontweight='bold')
            
            # Set title
            plt.title(f'Top {n_examples} Matches using {algo_name.capitalize()}', fontsize=16, pad=20)
            
            # Save if path provided
            if save_path:
                algo_path = f"{algo_name}_{save_path}"
                full_path = os.path.join(self.config['output_path'], algo_path)
                plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
            
            plt.tight_layout()
            plt.show()
    
    def plot_comparative_network(self, results_dict, source_label_col=None, target_label_col=None, save_path=None):
        """
        Plot a network visualization comparing matches from different algorithms
        
        Args:
            results_dict: Dictionary with algorithm name as key and matches DataFrame as value
            source_label_col: Column name in source data to use for node labels
            target_label_col: Column name in target data to use for node labels
            save_path: Path to save plot
            
        Returns:
            None
        """
        try:
            import networkx as nx
            
            # Create figure
            plt.figure(figsize=(14, 10))
            
            # Create graph
            G = nx.DiGraph()
            
            # Add edges for each algorithm with different colors
            colors = sns.color_palette(self.config['palette'], len(results_dict))
            edge_colors = []
            edges = []
            
            for i, (algo_name, matches_df) in enumerate(results_dict.items()):
                if matches_df.empty:
                    continue
                
                # Get color for this algorithm
                color = colors[i]
                
                # Add top 10 matches for this algorithm
                top_matches = matches_df.head(10)
                for _, row in top_matches.iterrows():
                    source = f"S_{row['source_id']}"
                    target = f"T_{row['target_id']}"
                    
                    # Add nodes if they don't exist
                    if source not in G:
                        G.add_node(source, bipartite=0, label=row['source_text'][:20] if source_label_col else source)
                    
                    if target not in G:
                        G.add_node(target, bipartite=1, label=row['target_text'][:20] if target_label_col else target)
                    
                    # Add edge
                    G.add_edge(source, target, weight=row['similarity'], algorithm=algo_name)
                    edges.append((source, target))
                    edge_colors.append(color)
            
            # Get positions
            if len(G.nodes) == 0:
                print("No nodes to visualize")
                return
                
            # Create positions with source nodes on left, target nodes on right
            left_nodes = [n for n, d in G.nodes(data=True) if d['bipartite'] == 0]
            right_nodes = [n for n, d in G.nodes(data=True) if d['bipartite'] == 1]
            
            pos = {}
            
            # Position left nodes in a column
            for i, node in enumerate(left_nodes):
                pos[node] = np.array([-1, (i - len(left_nodes)/2)])
            
            # Position right nodes in a column
            for i, node in enumerate(right_nodes):
                pos[node] = np.array([1, (i - len(right_nodes)/2)])
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, nodelist=left_nodes, node_color='skyblue', node_size=300, alpha=0.8)
            nx.draw_networkx_nodes(G, pos, nodelist=right_nodes, node_color='lightgreen', node_size=300, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edgelist=edges, width=2, alpha=0.5, edge_color=edge_colors, 
                                connectionstyle="arc3,rad=0.1")
            
            # Draw labels
            labels = nx.get_node_attributes(G, 'label')
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
            
            # Create legend
            legend_elements = []
            for i, algo_name in enumerate(results_dict.keys()):
                if i < len(colors):  # Ensure we don't go out of bounds
                    from matplotlib.lines import Line2D
                    legend_elements.append(Line2D([0], [0], color=colors[i], lw=4, label=algo_name))
            
            plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=len(legend_elements))
            
            # Set title and remove axis
            plt.title('Comparative Matching Network', fontsize=16)
            plt.axis('off')
            
            # Save if path provided
            if save_path:
                full_path = os.path.join(self.config['output_path'], save_path)
                plt.savefig(full_path, dpi=self.config['dpi'], bbox_inches='tight')
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            print("networkx package is required for network visualization")
            return