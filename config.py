"""
Configuration for the matching project
"""

import os
from dotenv import load_dotenv

# Default configuration values
DEFAULT_CONFIG = {
    # SharePoint settings
    'sharepoint': {
        'site': 'https://embrapii.sharepoint.com/sites/GEPES',
        'email': '',  # Set via .env or command line
        'password': '',  # Set via .env or command line
        'data_path': {
            'gerem_interacoes': 'General/Lucas Pinheiro/scriptGerem/apuracao_resultados_2024.xlsx',
            'prospeccoes': 'DWPII/srinfo/prospeccao_prospeccao.xlsx',
            'negociacoes': 'DWPII/srinfo/negociacoes_empresas.xlsx',
            'negociacoes_negociacoes': 'DWPII/srinfo/negociacoes_negociacoes.xlsx',
            'projetos': 'DWPII/srinfo/portfolio.xlsx',
            'info_empresas': 'DWPII/srinfo/info_empresas.xlsx'
        }
    },
    
    # Local paths
    'local_paths': {
        'data': 'data',
        'temp': 'temp',
        'results': 'results',
        'logs': 'logs',
        'evaluation': 'evaluation',
        'visualization': 'visualization'
    },
    
    # Matching settings
    'matching': {
        # Column mappings
        'column_mapping': {
            'gerem': {
                'id': 'id_prospeccao',
                'empresa': 'nome_empresa',
                'nome_capital': 'nome_empresa',
                'data': 'data_prospeccao'
            },
            'prospeccoes': {
                'id': 'id_prospeccao',
                'empresa': 'nome_empresa',
                'data': 'data_prospeccao',
                'cnpj': 'cnpj_empresa',
                'unidade': 'unidade_embrapii'
            },
            'negociacoes': {
                'id': 'codigo_negociacao',
                'empresa': 'razao_social',
                'cnpj': 'cnpj',
                'data': 'data_prim_ver_prop_tec',
                'unidade': 'unidade_embrapii'
            },
            'negociacoes_negociacoes': {
                'id': 'codigo_negociacao',
                'data': 'data_prim_ver_prop_tec'
            },
            'projetos': {
                'id': 'codigo_projeto',
                'empresa': 'info_empresa',
                'data': 'data_inicio',
                'unidade': 'unidade_embrapii'
            },
            'info_empresas': {
                'cnpj': 'cnpj',
                'razao_social': 'razao_social'
            }
        },
        
        # Algorithm settings
        'algorithms': {
            'levenshtein': {
                'enabled': True,
                'threshold': 0.7
            },
            'jaro_winkler': {
                'enabled': True,
                'threshold': 0.8
            },
            'embedding': {
                'enabled': True,
                'threshold': 0.6,
                'model': 'paraphrase-multilingual-MiniLM-L12-v2'
            }
        },
        
        # Threshold testing ranges
        'threshold_test': {
            'levenshtein': [0.5, 0.6, 0.7, 0.8, 0.9],
            'jaro_winkler': [0.7, 0.75, 0.8, 0.85, 0.9],
            'embedding': [0.5, 0.6, 0.7, 0.8, 0.9]
        }
    },
    
    # Evaluation settings
    'evaluation': {
        'metrics': ['precision', 'recall', 'f1', 'agreement'],
        'generate_visualizations': True,
        'save_detailed_results': True,
        'best_algorithm_criteria': 'f1_score',  # Which metric to use for selecting the best algorithm
        'run_threshold_comparison': False  # Desabilitar threshold comparison para acelerar
    },
    
    # Visualization settings
    'visualization': {
        'figsize': (12, 8),
        'palette': 'viridis',
        'dpi': 300
    },
    
    # Logging settings
    'logging': {
        'level': 'INFO',
        'file': 'matching.log',
        'console': True
    }
}


def load_config(config_file=None, overrides=None):
    """
    Load configuration from file and apply overrides
    
    Args:
        config_file: Path to YAML or JSON configuration file
        overrides: Dictionary with override values
    
    Returns:
        Dictionary with configuration
    """
    # Load environment variables first
    load_dotenv()
    
    config = DEFAULT_CONFIG.copy()
    
    # Load environment variables into config
    env_overrides = {}
    sharepoint_email = os.getenv('sharepoint_email')
    sharepoint_password = os.getenv('sharepoint_password')
    sharepoint_site = os.getenv('sharepoint_url_site')
    
    if sharepoint_email or sharepoint_password or sharepoint_site:
        env_overrides['sharepoint'] = {}
        if sharepoint_email:
            env_overrides['sharepoint']['email'] = sharepoint_email
        if sharepoint_password:
            env_overrides['sharepoint']['password'] = sharepoint_password
        if sharepoint_site:
            env_overrides['sharepoint']['site'] = sharepoint_site
    
    # Apply environment variables first
    if env_overrides:
        deep_update(config, env_overrides)
    
    # Load from file if provided
    if config_file:
        try:
            import yaml
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                
            # Update config with file values (nested)
            deep_update(config, file_config)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
    
    # Apply overrides if provided (these take highest priority)
    if overrides:
        deep_update(config, overrides)
    
    return config


def deep_update(d, u):
    """
    Update nested dictionary d with values from nested dictionary u
    """
    import collections.abc
    
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d