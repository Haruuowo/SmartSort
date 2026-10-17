import os
import yaml


class RuleEngine:
    def __init__(self, config_path: str):
        self.rules = []
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and isinstance(config.get('rules'), list):
                    self.rules = config['rules']

        # Pre-normalise conditions once instead of on every evaluation
        self._compiled = []
        for rule in self.rules:
            cond = rule.get('condition', {}) or {}
            names = cond.get('name_contains')
            exts = cond.get('extensions')
            self._compiled.append((
                rule,
                [str(s).lower() for s in names] if names is not None else None,
                {str(e).lower() for e in exts} if exts is not None else None,
                cond.get('has_exif_date') if 'has_exif_date' in cond else None,
            ))

    @property
    def uses_exif(self) -> bool:
        return any(c[3] is not None for c in self._compiled)

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
        name = file_info.get('name', '')
        ext = file_info.get('extension', '')
        for rule, names, exts, exif in self._compiled:
            if names is not None and not any(sub in name for sub in names):
                continue
            if exts is not None and ext not in exts:
                continue
            if exif is not None and exif != file_info.get('has_exif_date', False):
                continue
            return rule.get('name', 'Unnamed Rule'), rule.get('destination', 'Unknown')

        return None, None
