import yaml
from pathlib import Path

def get_seeds():
    path = Path(__file__).parent / "config" / "seeds.yaml"
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Flatten all categories into one list for the search loop
    all_keywords = []
    for category, keywords in data['orthopedic_seeds'].items():
        all_keywords.extend(keywords)
        
    config = data.get('runner_config', {})
    
    return {
        "keywords": all_keywords,
        "daily_limit": config.get("daily_search_limit", 25),
        "max_results": config.get("max_results_per_request", 50)
    }

# Usage
seeds_data = get_seeds()
print(f"Total seeds available: {len(seeds_data['keywords'])}")
print(f"Daily limit set to: {seeds_data['daily_limit']}")
