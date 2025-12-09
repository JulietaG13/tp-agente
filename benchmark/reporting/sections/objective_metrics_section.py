from benchmark.metrics.coverage_metrics import CoverageMetricsCalculator
from benchmark.metrics.metrics import BenchmarkMetrics
from benchmark.metrics.score_calculator import FinalScoreCalculator


class ObjectiveMetricsSection:
    """Generates objective metrics section (ECC, Remediation, etc)."""
    
    def generate_section(
        self, 
        coverage_metrics: CoverageMetricsCalculator,
        adaptivity_metrics: BenchmarkMetrics
    ) -> str:
        """Generate the objective metrics section of the report."""
        calculator = FinalScoreCalculator()
        
        ecc = coverage_metrics.calculate_effective_coverage()
        remediation = coverage_metrics.calculate_remediation_efficiency()
        exposure = coverage_metrics.calculate_syllabus_exposure()
        proficiency = adaptivity_metrics.weighted_proficiency()
        sensitivity = adaptivity_metrics.error_sensitivity()
        
        final_score = calculator.calculate_final_score(
            ecc, remediation, proficiency, sensitivity
        )
        interpretation = calculator.get_score_interpretation(final_score)
        
        return (
            "## Objective Metrics (Curriculum Coverage)\n\n"
            f"### 🎯 Final Benchmark Score: {final_score}%\n"
            f"**Grade**: {interpretation}\n\n"
            "---\n\n"
            "### Component Metrics:\n\n"
            f"#### 1. Effective Curriculum Coverage (ECC)\n\n"
            f"_Measures the breadth of student mastery across the curriculum._\n\n"
            f"**Value**: {ecc:.2%}\n\n"
            f"**Interpretation**: {self._interpret_ecc(ecc)}\n\n"
            f"#### 2. Syllabus Exposure\n\n"
            f"_Measures the breadth of content presented by the system._\n\n"
            f"**Value**: {exposure:.2%}\n\n"
            f"**Interpretation**: {self._interpret_exposure(exposure)}\n\n"
            f"#### 3. Remediation Efficiency\n\n"
            f"_Measures how effectively the system supports recovery from failures._\n\n"
            f"**Value**: {remediation:.2%}\n\n"
            f"**Interpretation**: {self._interpret_remediation(remediation)}\n\n"
            f"#### 4. Error Sensitivity\n\n"
            f"_Measures how consistently the system adapts difficulty after errors._\n\n"
            f"**Value**: {sensitivity:.2f}\n\n"
            f"**Interpretation**: {self._interpret_sensitivity(sensitivity)}\n\n"
            f"#### 5. Difficulty-Weighted Proficiency\n\n"
            f"_Measures student performance weighted by question difficulty._\n\n"
            f"**Value**: {proficiency:.2%}\n\n"
            f"**Interpretation**: {self._interpret_proficiency(proficiency)}\n"
        )
    
    def _interpret_ecc(self, ecc: float) -> str:
        """Interpret Effective Curriculum Coverage value."""
        if ecc >= 0.80:
            return "✅ Excellent - Student demonstrated competency in most topics"
        elif ecc >= 0.60:
            return "✓ Good - Student covered majority of curriculum"
        elif ecc >= 0.40:
            return "⚠ Fair - Significant gaps in topic coverage"
        else:
            return "❌ Poor - Major curriculum gaps, most topics not mastered"
    
    def _interpret_exposure(self, exposure: float) -> str:
        """Interpret Syllabus Exposure value."""
        if exposure >= 0.80:
            return "✅ Comprehensive - System explored most of the curriculum"
        elif exposure >= 0.60:
            return "✓ Good - System covered substantial portion of topics"
        elif exposure >= 0.40:
            return "⚠ Limited - System missed significant portions of curriculum"
        else:
            return "❌ Poor - System failed to explore most topics"
    
    def _interpret_remediation(self, remediation: float) -> str:
        """Interpret Remediation Efficiency value."""
        if remediation >= 0.70:
            return "✅ Excellent - System effectively helped student recover from failures"
        elif remediation >= 0.50:
            return "✓ Good - System provided adequate support for learning"
        elif remediation >= 0.30:
            return "⚠ Fair - Limited evidence of adaptive support"
        else:
            return "❌ Poor - System failed to help student improve on weak topics"
    
    def _interpret_sensitivity(self, sensitivity: float) -> str:
        """Interpret Error Sensitivity value."""
        if sensitivity > 0.70:
            return "✅ High - System quickly adapts after errors"
        elif sensitivity > 0.50:
            return "✓ Moderate - System usually adjusts difficulty after errors"
        elif sensitivity > 0.30:
            return "⚠ Low - System rarely adjusts after errors"
        else:
            return "❌ Very Low - System doesn't respond to user struggles"
    
    def _interpret_proficiency(self, proficiency: float) -> str:
        """Interpret Difficulty-Weighted Proficiency value."""
        if 0.65 <= proficiency <= 0.85:
            return "✅ Optimal Challenge (Sweet Spot) - Student is learning effectively"
            
        # Upper Boundary violations (Too Easy)
        if proficiency > 0.85:
            if proficiency <= 0.95:
                return "⚠ Under-challenged - Questions may be too easy relative to student level"
            return "❌ Poor - System failing to challenge (Too Easy)"
            
        # Lower Boundary violations (Too Hard)
        if proficiency < 0.65:
            if proficiency >= 0.50:
                return "⚠ Over-challenged - Student is struggling slightly"
            return "❌ Poor - System failing to support (Too Hard)"

