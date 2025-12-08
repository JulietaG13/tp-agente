from benchmark.coverage_metrics import CoverageMetricsCalculator
from benchmark.metrics import BenchmarkMetrics
from benchmark.score_calculator import FinalScoreCalculator


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
            f"#### 1. Effective Curriculum Coverage (ECC)\n"
            f"**Value**: {ecc:.2%}\n"
            f"**Interpretation**: {self._interpret_ecc(ecc)}\n\n"
            f"#### 2. Syllabus Exposure\n"
            f"**Value**: {exposure:.2%}\n"
            f"**Interpretation**: {self._interpret_exposure(exposure)}\n\n"
            f"#### 3. Remediation Efficiency\n"
            f"**Value**: {remediation:.2%}\n"
            f"**Interpretation**: {self._interpret_remediation(remediation)}\n\n"
            f"#### 4. Error Sensitivity\n"
            f"**Value**: {sensitivity:.2f}\n"
            f"**Interpretation**: {self._interpret_sensitivity(sensitivity)}\n\n"
            f"#### 5. Difficulty-Weighted Proficiency\n"
            f"**Value**: {proficiency:.2%}\n"
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
        if proficiency >= 0.75:
            return "✅ Excellent performance relative to question difficulty"
        elif proficiency >= 0.60:
            return "✓ Good performance considering difficulty levels"
        elif proficiency >= 0.45:
            return "⚠ Fair performance relative to difficulty"
        else:
            return "❌ Poor performance even accounting for difficulty"

