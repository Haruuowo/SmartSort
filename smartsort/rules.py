import yaml
import os

class RuleEngine:
    def __init__(self, config_path: str):
        self.rules = []
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'rules' in config:
                    self.rules = config['rules']

    def evaluate(self, file_info: dict):
        """
        Evaluates a file against loaded rules.
        file_info expected keys:
        - name: str (filename in lowercase)
        - extension: str (file extension with dot, lowercase)
        - has_exif_date: bool
        
        Returns:
            (rule_name, destination_template) or (None, None)
        """
        for rule in self.rules:
            condition = rule.get('condition', {})
            match = True
            
            # Check name contains
            if 'name_contains' in condition:
                contains_list = condition['name_contains']
                if not any(sub in file_info['name'] for sub in contains_list):
                    match = False
                    
            # Check extensions
            if match and 'extensions' in condition:
                ext_list = condition['extensions']
                if file_info['extension'] not in ext_list:
                    match = False
                    
            # Check EXIF requirement
            if match and 'has_exif_date' in condition:
                if condition['has_exif_date'] != file_info.get('has_exif_date', False):
                    match = False
                    
            if match:
                return rule.get('name', 'Unnamed Rule'), rule.get('destination', 'Unknown')
                
        return None, None
