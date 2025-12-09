import time
from typing import List, Dict, Any
from benchmark.metrics.metrics import BenchmarkMetrics
from benchmark.metrics.coverage_metrics import CoverageMetricsCalculator
from benchmark.core.simulated_student import PersonaStrategy
from benchmark.reporting.sections.objective_metrics_section import ObjectiveMetricsSection
from benchmark.reporting.sections.contextual_metrics_section import ContextualMetricsSection
from benchmark.reporting.sections.coverage_matrix_section import CoverageMatrixSection
from benchmark.core.topic_labeler import SubtopicLoader


class BenchmarkReportGenerator:
    """Generates markdown reports for benchmark results."""
    
    def generate_report(
        self, 
        results: List[Dict[str, Any]], 
        persona: PersonaStrategy,
        adaptivity_metrics: BenchmarkMetrics,
        coverage_metrics: CoverageMetricsCalculator
    ) -> str:
        """Generate complete markdown report."""
        sections = [
            self._generate_header(persona, len(results)),
            self._generate_summary(results),
            self._generate_objective_metrics_section(coverage_metrics, adaptivity_metrics),
            self._generate_coverage_matrix(coverage_metrics),
            self._generate_contextual_metrics_section(adaptivity_metrics, persona),
            self._generate_adaptivity_table(results),
            self._generate_detailed_logs(results)
        ]
        return "\n".join(sections)

    def _generate_header(self, persona: PersonaStrategy, total_turns: int) -> str:
        """Generate report header with metadata."""
        persona_name = persona.__class__.__name__
        return (
            f"# Benchmark Report: {persona_name}\n\n"
            f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Total Turns**: {total_turns}\n"
        )

    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate summary statistics section."""
        total_turns = len(results)
        if total_turns == 0:
            return "## Summary\nNo data available.\n"
        
        total_correct = sum(1 for r in results if r['is_correct'])
        accuracy = (total_correct / total_turns) * 100
        avg_difficulty = sum(r['difficulty_score'] for r in results) / total_turns
        
        return (
            f"## Summary\n"
            f"- **Accuracy**: {accuracy:.2f}%\n"
            f"- **Average Difficulty**: {avg_difficulty:.2f}\n"
        )

    def _generate_objective_metrics_section(
        self, 
        coverage_metrics: CoverageMetricsCalculator,
        adaptivity_metrics: BenchmarkMetrics
    ) -> str:
        """Generate objective metrics section using dedicated generator."""
        section = ObjectiveMetricsSection()
        return section.generate_section(coverage_metrics, adaptivity_metrics)
    
    def _generate_contextual_metrics_section(
        self,
        adaptivity_metrics: BenchmarkMetrics,
        persona: PersonaStrategy
    ) -> str:
        """Generate contextual metrics section using dedicated generator."""
        section = ContextualMetricsSection()
        return section.generate_section(adaptivity_metrics, persona)
    
    def _generate_coverage_matrix(self, coverage_metrics: CoverageMetricsCalculator) -> str:
        """Generate topic coverage matrix using dedicated generator."""
        topic_statuses = coverage_metrics.identify_topic_statuses()
        subtopics = SubtopicLoader().load_subtopics()
        
        section = CoverageMatrixSection()
        return section.generate_section(topic_statuses, subtopics)

    def _generate_adaptivity_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate adaptivity analysis table."""
        header = (
            "## Adaptivity Analysis\n"
            "| Turn | Difficulty (1-5) | Result | Correct Answer |\n"
            "|---|---|---|---|\n"
        )
        
        rows = []
        for r in results:
            status = "✅ Correct" if r['is_correct'] else "❌ Incorrect"
            rows.append(f"| {r['turn']} | {r['difficulty_score']} | {status} | {r['correct_answer']} |")
        
        return header + "\n".join(rows) + "\n"

    def _generate_detailed_logs(self, results: List[Dict[str, Any]]) -> str:
        """Generate detailed question logs."""
        logs = ["## Detailed Question Log"]
        for r in results:
            logs.append(self._format_single_turn_log(r))
        return "\n".join(logs)

    def _format_single_turn_log(self, result: Dict[str, Any]) -> str:
        """Format a single turn's detailed log."""
        status_icon = "✅" if result['is_correct'] else "❌"
        
        log_parts = [
            f"### Turn {result['turn']} {status_icon}",
            f"**Question**: {result['question']}\n",
            "**Options**:"
        ]
        
        for i, opt in enumerate(result['options']):
            log_parts.append(self._format_option_line(i, opt, result))
        
        log_parts.append(f"\n**Difficulty**: {result['difficulty_score']}/5")
        log_parts.append(self._format_subtopics(result.get('subtopics', [])))
        log_parts.append("---\n")
        
        return "\n".join(log_parts)

    def _format_option_line(self, index: int, option_text: str, result: Dict[str, Any]) -> str:
        """Format a single option line with appropriate markers."""
        letter = chr(65 + index)
        is_correct = (letter == result['correct_answer'])
        is_selected = (letter == result['student_answer'])
        
        suffix = self._build_option_suffix(is_correct, is_selected)
        line = f"{letter}) {option_text}{suffix}"
        
        if is_selected:
            return f"- **{line}**"
        return f"- {line}"

    def _build_option_suffix(self, is_correct: bool, is_selected: bool) -> str:
        """Build suffix markers for an option."""
        suffix_parts = []
        if is_correct:
            suffix_parts.append("(Correct Answer)")
        if is_selected:
            suffix_parts.append("(Student Choice)")
        
        if suffix_parts:
            return " " + " ".join(suffix_parts)
        return ""


    def _format_subtopics(self, subtopic_ids: List[int]) -> str:
        """Format subtopic IDs for display."""
        if not subtopic_ids:
            return "\n**Subtopics**: None identified"
        
        subtopics = SubtopicLoader().load_subtopics()
        subtopic_names = [f"`[{id}]` {subtopics[id]}" for id in subtopic_ids if id < len(subtopics)]
        
        if not subtopic_names:
            return "\n**Subtopics**: None identified"
        
        return "\n**Subtopics**: " + ", ".join(subtopic_names)

