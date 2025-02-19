import json
from pathlib import Path

def load_translations(lang):
    """Load translations for the specified language."""
    try:
        with open(Path('translations') / f'{lang}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {} 