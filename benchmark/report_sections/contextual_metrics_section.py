from benchmark.metrics import BenchmarkMetrics
from benchmark.simulated_student import PersonaStrategy


class ContextualMetricsSection:
    """Generates persona-validation metrics (EMA, Calibration Offset)."""
    
    def generate_section(self, metrics: BenchmarkMetrics, persona: PersonaStrategy) -> str:
        """Generate the contextual metrics section for persona validation."""
        ema_error = metrics.ema_convergence_error()
        offset = metrics.calibration_offset()
        
        return (
            "## Contextual Metrics (Persona Validation)\n\n"
            "*These metrics validate that the simulated persona behaved as expected.*\n\n"
            "---\n\n"
            "### Component Metrics:\n\n"
            "#### 1. EMA Convergence Error\n"
            f"**Value**: {ema_error}\n"
            f"**Target Level**: {persona.true_level}\n"
            f"**Interpretation**: {self._interpret_ema_error(ema_error)}\n\n"
            "#### 2. Calibration Offset\n"
            f"**Value**: {offset:+.2f}\n"
            f"**Interpretation**: {self._interpret_offset(offset)}\n"
        )
    
    def _interpret_ema_error(self, error: float) -> str:
        """Interpret EMA convergence error value."""
        if error < 0.2:
            return "✅ Perfect - System locked in and maintained user's level"
        elif error < 0.5:
            return "✓ Good - System converged close to target"
        elif error < 1.0:
            return "⚠ Fair - System somewhat off-target"
        else:
            return "❌ Poor - System failed to converge or ended far from target"
    
    def _interpret_offset(self, offset: float) -> str:
        """Interpret calibration offset value."""
        if abs(offset) < 0.3:
            return "✅ Well-calibrated - Challenge level matches ability"
        elif offset < -0.3:
            return f"⚠ Under-challenging by {abs(offset):.2f} - Questions too easy"
        else:
            return f"⚠ Over-challenging by {offset:.2f} - Questions too hard"

