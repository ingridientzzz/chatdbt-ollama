import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from llama_index.core import Document

class DBTProjectLoader:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.models_path = self.project_path / "models"
        self.docs_path = self.project_path / "target" / "compiled"
        
    def load_dbt_files(self) -> List[Document]:
        """Load DBT project files and convert to LlamaIndex documents"""
        documents = []
        
        # Load model files (.sql)
        documents.extend(self._load_sql_models())
        
        # Load schema files (.yml)
        documents.extend(self._load_schema_files())
        
        # Load documentation files
        documents.extend(self._load_docs_files())
        
        return documents
    
    def _load_sql_models(self) -> List[Document]:
        """Load SQL model files"""
        documents = []
        
        if not self.models_path.exists():
            return documents
            
        for sql_file in self.models_path.rglob("*.sql"):
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract model name from file path
                relative_path = sql_file.relative_to(self.models_path)
                model_name = str(relative_path).replace('.sql', '').replace('/', '.')
                
                doc = Document(
                    text=content,
                    metadata={
                        "file_path": str(sql_file),
                        "file_type": "sql_model",
                        "model_name": model_name,
                        "source": "dbt_model"
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Error loading SQL file {sql_file}: {e}")
                
        return documents
    
    def _load_schema_files(self) -> List[Document]:
        """Load YAML schema files"""
        documents = []

        for yml_file in self.project_path.rglob("*.yml"):
            # Exclude any .yml files found under the "target/compiled" directory
            if not yml_file.is_file():
                print(f"Skipping directory: {yml_file}")
                continue

            try:
                with open(yml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    yaml_content = yaml.safe_load(content)
                
                # Convert YAML to readable text
                text_content = self._yaml_to_text(yaml_content, yml_file.name)
                
                doc = Document(
                    text=text_content,
                    metadata={
                        "file_path": str(yml_file),
                        "file_type": "schema",
                        "source": "dbt_schema"
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Error loading YAML file {yml_file}: {e}")

        return documents
    
    def _load_docs_files(self) -> List[Document]:
        """Load compiled documentation files"""
        documents = []
        
        if not self.docs_path.exists():
            return documents
            
        for doc_file in self.docs_path.rglob("*.sql"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                doc = Document(
                    text=content,
                    metadata={
                        "file_path": str(doc_file),
                        "file_type": "compiled_sql",
                        "source": "dbt_compiled"
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Error loading compiled file {doc_file}: {e}")
                
        return documents
    
    def _yaml_to_text(self, yaml_content: Dict[Any, Any], filename: str) -> str:
        """Convert YAML content to readable text"""
        text_parts = [f"Schema file: {filename}\n"]
        
        if 'models' in yaml_content:
            text_parts.append("Models:")
            for model in yaml_content['models']:
                if isinstance(model, dict):
                    name = model.get('name', 'Unknown')
                    description = model.get('description', 'No description')
                    text_parts.append(f"- Model: {name}")
                    text_parts.append(f"  Description: {description}")
                    
                    if 'columns' in model:
                        text_parts.append("  Columns:")
                        for column in model['columns']:
                            if isinstance(column, dict):
                                col_name = column.get('name', 'unknown')
                                col_desc = column.get('description', 'No description')
                                text_parts.append(f"    - {col_name}: {col_desc}")
        
        if 'sources' in yaml_content:
            text_parts.append("\nSources:")
            for source in yaml_content['sources']:
                if isinstance(source, dict):
                    name = source.get('name', 'Unknown')
                    description = source.get('description', 'No description')
                    text_parts.append(f"- Source: {name}")
                    text_parts.append(f"  Description: {description}")
        
        return "\n".join(text_parts)