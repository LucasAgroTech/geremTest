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