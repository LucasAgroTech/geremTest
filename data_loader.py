import os
import pandas as pd
from office365_api.sharepoint_client import SharePointClient
from dotenv import load_dotenv

class DataLoader:
    def __init__(self, config=None):
        """Initialize data loader with configuration"""
        # Load environment variables
        load_dotenv()
        
        # Default configuration
        self.config = {
            'sharepoint_site': os.getenv('sharepoint_url_site', 'https://embrapii.sharepoint.com/sites/GEPES'),
            'sharepoint_email': os.getenv('sharepoint_email'),
            'sharepoint_password': os.getenv('sharepoint_password'),
            'local_data_path': 'data',
            'temp_path': 'temp'
        }
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Create directories if they don't exist
        os.makedirs(self.config['local_data_path'], exist_ok=True)
        os.makedirs(self.config['temp_path'], exist_ok=True)
        
        # Initialize SharePoint client if credentials are available
        self.sp_client = None
        if self.config['sharepoint_email'] and self.config['sharepoint_password']:
            self.sp_client = SharePointClient(
                self.config['sharepoint_site'],
                self.config['sharepoint_email'],
                self.config['sharepoint_password']
            )
    
    def load_from_sharepoint(self, file_path, sheet_name=0):
        """Load data from SharePoint"""
        if not self.sp_client:
            raise ValueError("SharePoint client not initialized. Check your credentials.")
        
        try:
            # Download file from SharePoint
            file_content = self.sp_client.download_file(file_path)
            
            # Save temporarily to load with pandas
            temp_file = os.path.join(self.config['temp_path'], os.path.basename(file_path))
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            # Load with pandas
            if file_path.endswith('.csv'):
                df = pd.read_csv(temp_file)
            else:
                df = pd.read_excel(temp_file, sheet_name=sheet_name)
            
            return df
        
        except Exception as e:
            print(f"Error loading file from SharePoint: {e}")
            raise
    
    def load_from_local(self, file_path, sheet_name=0):
        """Load data from local file system"""
        try:
            full_path = os.path.join(self.config['local_data_path'], file_path)
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(full_path)
            else:
                df = pd.read_excel(full_path, sheet_name=sheet_name)
            
            return df
        
        except Exception as e:
            print(f"Error loading local file: {e}")
            raise
    
    def save_to_local(self, df, file_name):
        """Save DataFrame to local file system"""
        try:
            full_path = os.path.join(self.config['local_data_path'], file_name)
            
            if file_name.endswith('.csv'):
                df.to_csv(full_path, index=False)
            else:
                df.to_excel(full_path, index=False)
            
            return full_path
        
        except Exception as e:
            print(f"Error saving file locally: {e}")
            raise
    
    def upload_to_sharepoint(self, file_name, sharepoint_path):
        """Upload file to SharePoint"""
        if not self.sp_client:
            raise ValueError("SharePoint client not initialized. Check your credentials.")
        
        try:
            # Read the local file
            full_path = os.path.join(self.config['local_data_path'], file_name)
            with open(full_path, 'rb') as f:
                file_content = f.read()
            
            # Upload to SharePoint  
            self.sp_client.upload_file(file_content, sharepoint_path)
            
            return True
        
        except Exception as e:
            print(f"Error uploading file to SharePoint: {e}")
            raise
    
    def load_info_empresas_and_match_cnpj(self, df_negociacoes, info_empresas_path, cnpj_col='cnpj', razao_social_col='razao_social'):
        """
        Carrega a planilha info_empresas.xlsx e faz match por CNPJ para enriquecer 
        os dados de negociações com razão social
        
        Args:
            df_negociacoes: DataFrame com dados de negociações
            info_empresas_path: Caminho para a planilha info_empresas.xlsx no SharePoint
            cnpj_col: Nome da coluna CNPJ (default: 'cnpj')
            razao_social_col: Nome da coluna razão social (default: 'razao_social')
        
        Returns:
            DataFrame enriquecido com razão social
        """
        try:
            # Carregar planilha info_empresas
            print("Carregando planilha info_empresas.xlsx...")
            df_info_empresas = self.load_from_sharepoint(info_empresas_path)
            print(f"Carregada planilha info_empresas com {len(df_info_empresas)} registros")
            
            # Verificar se as colunas necessárias existem
            if cnpj_col not in df_info_empresas.columns:
                raise ValueError(f"Coluna '{cnpj_col}' não encontrada em info_empresas.xlsx")
            if razao_social_col not in df_info_empresas.columns:
                raise ValueError(f"Coluna '{razao_social_col}' não encontrada em info_empresas.xlsx")
            
            # Limpar CNPJs (remover caracteres especiais e espaços) para melhorar o match
            df_negociacoes_copy = df_negociacoes.copy()
            df_info_empresas_copy = df_info_empresas.copy()
            
            # Função para limpar CNPJ
            def clean_cnpj(cnpj):
                if pd.isna(cnpj):
                    return cnpj
                return str(cnpj).replace('.', '').replace('/', '').replace('-', '').replace(' ', '').strip()
            
            df_negociacoes_copy[cnpj_col + '_clean'] = df_negociacoes_copy[cnpj_col].apply(clean_cnpj)
            df_info_empresas_copy[cnpj_col + '_clean'] = df_info_empresas_copy[cnpj_col].apply(clean_cnpj)
            
            # Fazer o merge por CNPJ limpo
            df_merged = df_negociacoes_copy.merge(
                df_info_empresas_copy[[cnpj_col + '_clean', razao_social_col]], 
                on=cnpj_col + '_clean', 
                how='left'
            )
            
            # Remover coluna auxiliar de CNPJ limpo
            df_merged = df_merged.drop(columns=[cnpj_col + '_clean'])
            
            # Estatísticas do match
            matches_found = df_merged[razao_social_col].notna().sum()
            total_records = len(df_merged)
            match_rate = (matches_found / total_records) * 100 if total_records > 0 else 0
            
            print(f"Match por CNPJ realizado com sucesso:")
            print(f"- Total de registros: {total_records}")
            print(f"- Matches encontrados: {matches_found}")
            print(f"- Taxa de match: {match_rate:.1f}%")
            
            return df_merged
            
        except Exception as e:
            print(f"Erro ao fazer match com info_empresas.xlsx: {e}")
            raise
    
    def load_and_merge_negociacoes(self, negociacoes_empresas_path, negociacoes_negociacoes_path, 
                                   info_empresas_path, config_mapping):
        """
        Carrega e faz merge das planilhas de negociações:
        1. negociacoes_empresas.xlsx (contém CNPJ)
        2. negociacoes_negociacoes.xlsx (contém datas)
        3. info_empresas.xlsx (contém razão social)
        
        Args:
            negociacoes_empresas_path: Caminho para negociacoes_empresas.xlsx
            negociacoes_negociacoes_path: Caminho para negociacoes_negociacoes.xlsx  
            info_empresas_path: Caminho para info_empresas.xlsx
            config_mapping: Dicionário com mapeamento de colunas da configuração
        
        Returns:
            DataFrame consolidado com todas as informações de negociações
        """
        try:
            print("=== CARREGANDO E CONSOLIDANDO DADOS DE NEGOCIAÇÕES ===")
            
            # 1. Carregar negociacoes_empresas.xlsx
            print("1. Carregando negociacoes_empresas.xlsx...")
            df_neg_empresas = self.load_from_sharepoint(negociacoes_empresas_path)
            print(f"   - Carregados {len(df_neg_empresas)} registros de empresas nas negociações")
            print(f"   - Colunas: {list(df_neg_empresas.columns)}")
            
            # 2. Carregar negociacoes_negociacoes.xlsx  
            print("\n2. Carregando negociacoes_negociacoes.xlsx...")
            df_neg_negociacoes = self.load_from_sharepoint(negociacoes_negociacoes_path)
            print(f"   - Carregados {len(df_neg_negociacoes)} registros de negociações")
            print(f"   - Colunas: {list(df_neg_negociacoes.columns)}")
            
            # 3. Fazer merge das duas planilhas de negociações pelo codigo_negociacao
            print("\n3. Fazendo merge das planilhas de negociações...")
            neg_col_map = config_mapping['negociacoes']
            neg_neg_col_map = config_mapping['negociacoes_negociacoes']
            
            # Verificar se as colunas de ID existem
            id_col_empresas = neg_col_map['id']
            id_col_negociacoes = neg_neg_col_map['id']
            
            if id_col_empresas not in df_neg_empresas.columns:
                raise ValueError(f"Coluna '{id_col_empresas}' não encontrada em negociacoes_empresas.xlsx")
            if id_col_negociacoes not in df_neg_negociacoes.columns:
                raise ValueError(f"Coluna '{id_col_negociacoes}' não encontrada em negociacoes_negociacoes.xlsx")
            
            # Fazer merge
            df_negociacoes_merged = df_neg_empresas.merge(
                df_neg_negociacoes[[id_col_negociacoes, neg_neg_col_map['data']]], 
                left_on=id_col_empresas,
                right_on=id_col_negociacoes, 
                how='left'
            )
            
            # Remover coluna duplicada de ID se necessário
            if id_col_empresas != id_col_negociacoes and id_col_negociacoes in df_negociacoes_merged.columns:
                df_negociacoes_merged = df_negociacoes_merged.drop(columns=[id_col_negociacoes])
            
            print(f"   - Merge realizado: {len(df_negociacoes_merged)} registros resultantes")
            
            # 4. Enriquecer com razão social da info_empresas.xlsx
            print("\n4. Enriquecendo com razão social da info_empresas.xlsx...")
            info_col_map = config_mapping['info_empresas']
            
            df_final = self.load_info_empresas_and_match_cnpj(
                df_negociacoes_merged,
                info_empresas_path,
                cnpj_col=neg_col_map['cnpj'],
                razao_social_col=info_col_map['razao_social']
            )
            
            print(f"\n5. Consolidação concluída:")
            print(f"   - Total de registros: {len(df_final)}")
            print(f"   - Colunas finais: {list(df_final.columns)}")
            
            # Verificar se as colunas importantes estão presentes
            expected_cols = [
                neg_col_map['id'],
                neg_col_map['cnpj'], 
                info_col_map['razao_social'],
                neg_neg_col_map['data']
            ]
            
            missing_cols = [col for col in expected_cols if col not in df_final.columns]
            if missing_cols:
                print(f"   - ATENÇÃO: Colunas faltando: {missing_cols}")
            else:
                print("   - ✅ Todas as colunas importantes estão presentes")
            
            return df_final
            
        except Exception as e:
            print(f"Erro ao consolidar dados de negociações: {e}")
            raise