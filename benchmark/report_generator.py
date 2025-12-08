import time
from typing import List, Dict, Any
from benchmark.metrics import BenchmarkMetrics
from benchmark.simulated_student import PersonaStrategy


class BenchmarkReportGenerator:
    """Generates markdown reports for benchmark results."""
    
    def generate_report(
        self, 
        results: List[Dict[str, Any]], 
        persona: PersonaStrategy,
        metrics: BenchmarkMetrics
    ) -> str:
        """Generate complete markdown report."""
        sections = [
            self._generate_header(persona, len(results)),
            self._generate_summary(results),
            self._generate_metrics_section(metrics, persona),
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

    def _generate_metrics_section(self, metrics: BenchmarkMetrics, persona: PersonaStrategy) -> str:
        """Generate performance metrics section with interpretations."""
        afs = metrics.calculate_adaptive_fidelity_score(
            persona.target_sensitivity,
            persona.target_accuracy
        )
        
        ema_error = metrics.ema_convergence_error()
        sensitivity = metrics.error_sensitivity()
        offset = metrics.calibration_offset()
        proficiency = metrics.weighted_proficiency()
        
        return (
            "## Performance Metrics\n\n"
            f"### 🎯 Adaptive Fidelity Score (AFS): {afs}%\n"
            f"**Overall Grade**: {self._interpret_afs(afs)}\n\n"
            "---\n\n"
            "### Component Metrics:\n\n"
            "#### 1. EMA Convergence Error (Lock-In Quality)\n"
            f"**Value**: {ema_error}\n"
            f"**Interpretation**: {self._interpret_ema_error(ema_error)}\n\n"
            "#### 2. Error Sensitivity Ratio (Safety Net)\n"
            f"**Value**: {sensitivity}\n"
            f"**Interpretation**: {self._interpret_sensitivity(sensitivity)}\n\n"
            "#### 3. Calibration Offset (Challenge Level)\n"
            f"**Value**: {offset}\n"
            f"**Interpretation**: {self._interpret_offset(offset)}\n\n"
            "#### 4. Difficulty-Weighted Proficiency (True Score)\n"
            f"**Value**: {proficiency:.2%}\n"
            f"**Interpretation**: {self._interpret_proficiency(proficiency)}\n"
        )

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

    def _interpret_ema_error(self, error: float) -> str:
        """Interpret EMA convergence error value."""
        if error < 0.2:
            return "✅ Perfect - System locked in and maintained user's level"
        if error < 0.5:
            return "✓ Good - System converged close to target"
        if error < 1.0:
            return "⚠ Fair - System somewhat off-target"
        return "❌ Poor - System failed to converge or ended far from target"

    def _interpret_sensitivity(self, sensitivity: float) -> str:
        """Interpret error sensitivity ratio."""
        if sensitivity > 0.8:
            return "✅ High responsiveness - Immediately helps after errors"
        if sensitivity > 0.5:
            return "✓ Moderate responsiveness - Often adjusts after errors"
        if sensitivity > 0.3:
            return "⚠ Low responsiveness - Occasionally adjusts after errors"
        return "❌ Very low - Rarely adjusts difficulty after errors"

    def _interpret_offset(self, offset: float) -> str:
        """Interpret calibration offset value."""
        if abs(offset) < 0.3:
            return "✅ Well-calibrated - Challenge level matches ability"
        if offset < -0.3:
            return f"⚠ Under-challenging by {abs(offset):.2f} - Questions too easy"
        return f"⚠ Over-challenging by {offset:.2f} - Questions too hard"

    def _interpret_proficiency(self, proficiency: float) -> str:
        """Interpret difficulty-weighted proficiency."""
        if proficiency >= 0.8:
            return "✅ Excellent performance considering difficulty"
        if proficiency >= 0.6:
            return "✓ Good performance considering difficulty"
        if proficiency >= 0.4:
            return "⚠ Fair performance considering difficulty"
        return "❌ Poor performance considering difficulty"

    def _interpret_afs(self, score: float) -> str:
        """Interpret Adaptive Fidelity Score."""
        if score >= 90:
            return "🏆 A+ (90-100%) - Perfect tutor behavior"
        if score >= 75:
            return "✅ B (75-89%) - Good, robust system"
        if score >= 60:
            return "⚠ C (60-74%) - Acceptable but needs improvement"
        return "❌ F (<60%) - System failed to adapt appropriately"

