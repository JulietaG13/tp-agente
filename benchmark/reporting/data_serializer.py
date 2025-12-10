import json
from typing import Dict, List, Tuple


class BenchmarkDataSerializer:
    """Serializes and deserializes benchmark results to/from JSON."""
    
    def serialize_results(
        self,
        results: List[Dict],
        persona_info: Dict,
        metadata: Dict
    ) -> Dict:
        """
        Convert benchmark results to JSON-serializable dict.
        
        Args:
            results: List of turn results
            persona_info: Persona configuration (true_level, target_sensitivity, etc)
            metadata: Benchmark metadata (timestamp, turns, persona_type)
            
        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            'metadata': metadata,
            'persona_config': persona_info,
            'results': results
        }
    
    def deserialize_results(self, data: Dict) -> Tuple[List[Dict], Dict, Dict]:
        """
        Load benchmark results from JSON dict.
        
        Args:
            data: Dictionary loaded from JSON
            
        Returns:
            Tuple of (results, persona_info, metadata)
        """
        results = data.get('results', [])
        persona_info = data.get('persona_config', {})
        metadata = data.get('metadata', {})
        
        return results, persona_info, metadata
    
    def save_to_file(self, data: Dict, filepath: str):
        """Save data to JSON file with pretty formatting."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str) -> Dict:
        """Load data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

