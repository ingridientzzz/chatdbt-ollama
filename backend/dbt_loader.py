import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from llama_index.core import Document
import json

class DBTProjectLoader:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.compiled_sql_path = self.project_path / "target" / "compiled"
        self.manifest_path = self.project_path / "target" / "manifest.json"

    def load_dbt_files(self) -> List[Document]:
        """Load DBT project files and convert to LlamaIndex documents"""
        documents = []
        
        # Load model files (.sql)
        documents.extend(self._load_sql_models())

        # Load YAML files (.yml)
        documents.extend(self._load_yaml_files())

        # Load manifest file
        documents.extend(self._load_manifest_file())
        
        return documents
    
    def _load_sql_models(self) -> List[Document]:
        """Load SQL model files"""
        documents = []
        
        if not self.compiled_sql_path.exists():
            return documents

        for sql_file in self.compiled_sql_path.rglob("*.sql"):
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract model name from file path
                relative_path = sql_file.relative_to(self.compiled_sql_path)
                model_name = str(relative_path).replace('.sql', '').replace('/', '.')
                
                doc = Document(
                    text=content,
                    metadata={
                        "file_path": str(sql_file),
                        "file_type": "sql_model",
                        "model_name": model_name,
                        "project_file": "dbt_model"
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Error loading SQL file {sql_file}: {e}")
                
        return documents
    

    def _load_yaml_files(self) -> List[Document]:
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
                        "file_type": "yaml",
                        "project_file": "dbt_yaml"
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                print(f"Error loading YAML file {yml_file}: {e}")

        return documents
    
    def _load_manifest_file(self) -> List[Document]:
        """Load manifest.json from the target directory and extract DBT documentation"""
        documents = []

        if not self.manifest_path.exists():
            return documents

        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Extract nodes (models, sources, etc.) from manifest
            nodes = manifest.get("nodes", {})
            sources = manifest.get("sources", {})

            # Process models and other nodes
            for node in nodes.values():
                name = node.get("name", "unknown")
                description = node.get("description", "")
                depends_on = node.get("depends_on", {}).get("nodes", [])
                resource_type = node.get("resource_type", "")

                text = f"Name: {name}\nType: {resource_type}\nDescription: {description}\nDependencies:\n{depends_on}"
                doc = Document(
                    text=text,
                    metadata={
                        "source": resource_type,
                        "project_file": "dbt_manifest"
                    }
                )
                documents.append(doc)

            # Process sources
            for source in sources.values():
                name = source.get("name", "unknown")
                description = source.get("description", "")
                table_name = source.get("relation_name", "")
                resource_type = source.get("resource_type", "")

                text = f"Source: {name}\nTable: {table_name}\nType: {resource_type}\nDescription: {description}"
                doc = Document(
                    text=text,
                    metadata={
                        "source": resource_type,
                        "project_file": "dbt_manifest"
                    }
                )
                documents.append(doc)

        except Exception as e:
            print(f"Error loading manifest.json: {e}")

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