import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from llama_index.core import Document
import json

# some projects may have different description structure for models and columns, 
# try improving _load_manifest_file or expand to get all related information

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
        """Load SQL model files, excluding 'elementary' folder"""
        documents = []
        
        if not self.compiled_sql_path.exists():
            return documents

        for sql_file in self.compiled_sql_path.rglob("*.sql"):
            # Exclude files in any 'elementary' subfolder
            if "elementary" in sql_file.parts:
                continue
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
                print(f"Skipping {yml_file}: is a directory, not a file.")
                continue

            if "eio_documentation" in yml_file.parts or "elementary" in yml_file.parts:
                print(f"Skipping {yml_file}: not core project directories")
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
        """
        Load manifest.json from the target directory and extract DBT documentation,
        with enhanced information for pattern inference by LLMs.
        """
        documents = []  

        if not self.manifest_path.exists():
            return documents    

        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f) 

            # Extract nodes (models, sources, etc.) from manifest
            nodes = manifest.get("nodes", {})
            sources = manifest.get("sources", {})
            macros = manifest.get("macros", {}) # Add macros for better test context    

            # --- Helper to resolve source names from unique_ids ---
            source_unique_id_to_name = {
                unique_id: f"{s.get('source_name', '')}.{s.get('name', '')}"
                for unique_id, s in sources.items()
            }
            
            # --- Helper to get macro names from unique_ids ---
            macro_unique_id_to_name = {
                unique_id: m.get('name', '')
                for unique_id, m in macros.items()
            }   

            # Process models and other nodes
            for node_id, node in nodes.items():
                # Exclude elementary and other irrelevant nodes for core dbt documentation
                if any(substring in node_id for substring in ["elementary", "test"]):
                     continue # Skip elementary models/tests as they are often internal 

                name = node.get("name", "unknown")
                alias = node.get("alias", name)
                description = node.get("description", "")
                resource_type = node.get("resource_type", "")
                compiled_sql = node.get("compiled_code", "")
                original_file_path = node.get("original_file_path", "")
                
                # Extract column information
                columns_info = []
                if node.get("columns"):
                    for col_name, col_data in node["columns"].items():
                        col_description = col_data.get("description", "No description provided.")
                        col_data_type = col_data.get("data_type", "unknown type")
                        columns_info.append(f"- Column '{col_name}' (type: {col_data_type}): {col_description}")
                columns_text = "\n".join(columns_info) if columns_info else "No columns defined."   
    

                # Identify direct dependencies (models and sources)
                direct_model_dependencies = []
                direct_source_dependencies = []
                
                # Ensure 'depends_on' key exists before accessing 'nodes'
                if 'depends_on' in node and 'nodes' in node['depends_on']:
                    for dep_id in node['depends_on']['nodes']:
                        if dep_id.startswith("model."):
                            # Try to resolve the model name
                            dep_model = nodes.get(dep_id)
                            if dep_model:
                                direct_model_dependencies.append(dep_model.get("name", dep_id))
                            else:
                                direct_model_dependencies.append(dep_id) # Fallback to ID
                        elif dep_id.startswith("source."):
                            # Resolve source name using the pre-built map
                            resolved_source_name = source_unique_id_to_name.get(dep_id, dep_id)
                            direct_source_dependencies.append(resolved_source_name) 

                # Identify tests applied to this node
                applied_tests = []
                if 'depends_on' in node and 'macros' in node['depends_on']:
                    for macro_id in node['depends_on']['macros']:
                        # Heuristics for identifying tests applied via macros (e.g., dbt built-in tests)
                        if 'test_' in macro_id: # Common pattern for dbt generic tests
                            test_name = macro_unique_id_to_name.get(macro_id, macro_id.split('.')[-1])
                            applied_tests.append(test_name)
                        # More specific check for unique/not_null tests typically defined as macros
                        elif macro_id.startswith('macro.dbt.test_'):
                             applied_tests.append(macro_id.split('.')[-1])  
    

                # Construct the `text` for the Document
                text = f"DBT {resource_type.upper()} Name: {name}\n"
                text += f"Alias: {alias}\n"
                text += f"Description: {description}\n"
                text += f"Location: {original_file_path}\n" 

                if columns_info:
                    text += f"Columns:\n{columns_text}\n"   

                if direct_model_dependencies:
                    text += f"Directly depends on other models: {', '.join(direct_model_dependencies)}\n"
                
                if direct_source_dependencies:
                    text += f"Directly depends on sources: {', '.join(direct_source_dependencies)}\n"
                
                if applied_tests:
                    text += f"Applied tests: {', '.join(applied_tests)}\n"  

                if compiled_sql:
                    text += f"Compiled SQL:\n```sql\n{compiled_sql}\n```\n" 

                doc = Document(
                    text=text.strip(), # .strip() to remove trailing newlines
                    metadata={
                        "resource_type": resource_type,
                        "project_file": "manifest",
                        "name": name,
                        "alias": alias,
                        "original_file_path": original_file_path,
                        "direct_model_dependencies": direct_model_dependencies,
                        "direct_source_dependencies": direct_source_dependencies,
                        "applied_tests": applied_tests,
                        "unique_id": node_id # Add unique_id for precise referencing
                    }
                )
                documents.append(doc)   

                # --- Add individual column documents for more granular search ---
                for col_name, col_data in node.get("columns", {}).items():
                    col_description = col_data.get("description", "No description provided.")
                    col_data_type = col_data.get("data_type", "unknown type")
                    col_text = (
                        f"Column '{col_name}' of DBT {resource_type} '{name}'.\n"
                        f"Description: {col_description}\n"
                        f"Data Type: {col_data_type}\n"
                        f"Defined in: {original_file_path}"
                    )
                    col_doc = Document(
                        text=col_text.strip(),
                        metadata={
                            "resource_type": "column",
                            "project_file": "manifest",
                            "name": col_name,
                            "parent_resource_type": resource_type,
                            "parent_name": name,
                            "original_file_path": original_file_path,
                            "unique_id": f"{node_id}__column__{col_name}"
                        }
                    )
                    documents.append(col_doc)   
    

            # Process sources
            for source_id, source in sources.items():
                name = source.get("name", "unknown")
                source_name = source.get("source_name", "unknown_source") # The name of the database/schema the source belongs to
                description = source.get("description", "")
                table_name = source.get("relation_name", "").split('.')[-1] # Extract just the table name
                original_file_path = source.get("original_file_path", "")
                resource_type = source.get("resource_type", "") 

                # Extract column information for sources
                columns_info = []
                if source.get("columns"):
                    for col_name, col_data in source["columns"].items():
                        col_description = col_data.get("description", "No description provided.")
                        columns_info.append(f"- Column '{col_name}': {col_description}")
                columns_text = "\n".join(columns_info) if columns_info else "No columns defined."   

                text = f"DBT SOURCE Name: {source_name}.{name}\n"
                text += f"Table Name: {table_name}\n"
                text += f"Description: {description}\n"
                text += f"Location: {original_file_path}\n"
                if columns_info:
                    text += f"Columns:\n{columns_text}\n"   

                doc = Document(
                    text=text.strip(),
                    metadata={
                        "resource_type": resource_type,
                        "project_file": "manifest",
                        "name": name,
                        "source_name": source_name,
                        "table_name": table_name,
                        "original_file_path": original_file_path,
                        "unique_id": source_id
                    }
                )
                documents.append(doc)
                
                # --- Add individual column documents for sources ---
                for col_name, col_data in source.get("columns", {}).items():
                    col_description = col_data.get("description", "No description provided.")
                    col_text = (
                        f"Column '{col_name}' of DBT SOURCE '{source_name}.{name}'.\n"
                        f"Description: {col_description}\n"
                        f"Defined in: {original_file_path}"
                    )
                    col_doc = Document(
                        text=col_text.strip(),
                        metadata={
                            "resource_type": "column",
                            "project_file": "manifest",
                            "name": col_name,
                            "parent_resource_type": "source",
                            "parent_name": f"{source_name}.{name}",
                            "original_file_path": original_file_path,
                            "unique_id": f"{source_id}__column__{col_name}"
                        }
                    )
                    documents.append(col_doc)   
    

        except Exception as e:
            print(f"Error loading manifest.json: {e}")  

        return documents

    
    def _yaml_to_text(self, yaml_content: Dict[Any, Any], filename: str) -> str:
        """Convert YAML content to readable text"""
        text_parts = [f"Schema file: {filename}\n"]
        
        if 'models:' in yaml_content:
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
        
        if 'sources:' in yaml_content:
            text_parts.append("\nSources:")
            for source in yaml_content['sources']:
                if isinstance(source, dict):
                    name = source.get('name', 'Unknown')
                    database = source.get('database', 'No description')
                    schema = source.get('schema', 'No description')
                    table = source.get('table', 'No description')
                    text_parts.append(f"- Source: {name}")
                    text_parts.append(f"  Table: {database}.{schema}.{table}")

        return "\n".join(text_parts)