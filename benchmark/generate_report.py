import argparse
import os
import sys
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.reporting.data_serializer import BenchmarkDataSerializer
from benchmark.metrics.metrics import BenchmarkMetrics
from benchmark.metrics.coverage_metrics import TopicHistoryBuilder, CoverageMetricsCalculator
from benchmark.reporting.report_generator import BenchmarkReportGenerator
from benchmark.core.topic_labeler import SubtopicLoader
from benchmark.core.simulated_student import ExpertPersona, NovicePersona, LearnerPersona, PersonaStrategy


def load_benchmark_data(data_path: str) -> Dict:
    """Load benchmark data from JSON file."""
    serializer = BenchmarkDataSerializer()
    return serializer.load_from_file(data_path)


def reconstruct_persona(metadata: Dict) -> PersonaStrategy:
    """Reconstruct persona object from saved metadata."""
    persona_map = {
        'ExpertPersona': ExpertPersona,
        'NovicePersona': NovicePersona,
        'LearnerPersona': LearnerPersona
    }
    
    persona_type = metadata.get('persona_type')
    if persona_type in persona_map:
        return persona_map[persona_type]()
    
    raise ValueError(f"Unknown persona type: {persona_type}")


def compute_adaptivity_metrics(results: List[Dict[str, Any]], persona: PersonaStrategy) -> BenchmarkMetrics:
    """Compute adaptivity-focused metrics from results."""
    turns_data = [
        {
            'difficulty_score': r['difficulty_score'],
            'is_correct': r['is_correct']
        }
        for r in results
    ]
    return BenchmarkMetrics(turns_data, persona.true_level)


def compute_coverage_metrics(results: List[Dict[str, Any]]) -> CoverageMetricsCalculator:
    """Compute topic coverage metrics from results."""
    builder = TopicHistoryBuilder()
    topic_history = builder.build_history(results)
    
    subtopics = SubtopicLoader().load_subtopics()
    total_topics = len(subtopics)
    total_turns = len(results)
    
    return CoverageMetricsCalculator(topic_history, total_topics, total_turns)


def generate_report_from_data(data: Dict) -> str:
    """Generate markdown report from raw benchmark data."""
    results = data.get('results', [])
    metadata = data.get('metadata', {})
    
    persona = reconstruct_persona(metadata)
    
    adaptivity_metrics = compute_adaptivity_metrics(results, persona)
    coverage_metrics = compute_coverage_metrics(results)
    
    generator = BenchmarkReportGenerator()
    return generator.generate_report(
        results,
        persona,
        adaptivity_metrics,
        coverage_metrics
    )


def save_report(report: str, output_path: str):
    """Save report to markdown file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)


def determine_output_path(data_file_path: str, output_arg: str = None) -> str:
    """Determine output path for report."""
    if output_arg:
        return output_arg
    
    return os.path.join(os.path.dirname(data_file_path), "report.md")


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark report from saved data")
    parser.add_argument("data_file", help="Path to benchmark data JSON file")
    parser.add_argument("--output", help="Output report file (default: report.md in same directory)")
    
    args = parser.parse_args()
    
    print(f"Loading benchmark data from {args.data_file}...")
    data = load_benchmark_data(args.data_file)
    
    print("Generating report...")
    report = generate_report_from_data(data)
    
    output_path = determine_output_path(args.data_file, args.output)
    save_report(report, output_path)
    
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()

