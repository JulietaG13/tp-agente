import math


class FinalScoreCalculator:
    """Calculates weighted final benchmark score from objective metrics."""
    
    WEIGHTS = {
        'effective_coverage': 0.35,
        'remediation_efficiency': 0.30,
        'proficiency': 0.20,
        'error_sensitivity': 0.15,
    }
    
    def calculate_final_score(
        self,
        ecc: float,
        remediation: float,
        proficiency: float,
        sensitivity: float
    ) -> float:
        """
        Returns weighted score 0-100.
        
        Args:
            ecc: Effective Curriculum Coverage (0.0-1.0)
            remediation: Remediation Efficiency (0.0-1.0)
            proficiency: Difficulty-Weighted Proficiency (0.0-1.0)
            sensitivity: Error Sensitivity (0.0-1.0)
            
        Returns:
            Final score as percentage (0-100)
        """
        # Calculate proficiency score using a Gaussian bell curve
        # Target = 0.75 (Sweet spot)
        # Sigma = 0.2 (Controls width: score ~0.5 at +/- 0.25 deviation)
        sigma = 0.2
        proficiency_score = math.exp(-((proficiency - 0.75) ** 2) / (2 * sigma ** 2))

        weighted_sum = (
            self.WEIGHTS['effective_coverage'] * ecc +
            self.WEIGHTS['remediation_efficiency'] * remediation +
            self.WEIGHTS['proficiency'] * proficiency_score +
            self.WEIGHTS['error_sensitivity'] * sensitivity
        )
        
        return round(weighted_sum * 100, 2)
    
    def get_score_interpretation(self, score: float) -> str:
        """Returns interpretation of the final score."""
        if score >= 85:
            return "🏆 Excellent (85-100%) - Outstanding curriculum coverage and adaptation"
        elif score >= 70:
            return "✅ Good (70-84%) - Strong coverage with effective adaptation"
        elif score >= 55:
            return "⚠ Fair (55-69%) - Acceptable but significant gaps remain"
        else:
            return "❌ Poor (<55%) - Major curriculum gaps or adaptation failures"

