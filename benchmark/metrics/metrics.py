import math
from typing import List, Dict, Any


class BenchmarkMetrics:
    def __init__(self, turns_data: List[Dict[str, Any]], persona_true_level: float):
        """
        Initialize metrics calculator with benchmark data.
        
        Args:
            turns_data: List of dicts with 'difficulty_score' (int) and 'is_correct' (bool)
            persona_true_level: float (e.g., 5.0 for Expert, 1.0 for Novice)
        """
        self.turns = turns_data
        self.difficulties = [t['difficulty_score'] for t in turns_data]
        self.correctness = [1 if t['is_correct'] else 0 for t in turns_data]
        self.theta = float(persona_true_level)

    def ema_convergence_error(self, alpha: float = 0.3) -> float:
        """
        Calculates the distance between the User's True Level and the 
        Exponential Moving Average (EMA) of the system's difficulty.
        Lower is Better. 0.0 is Perfect.
        
        Interpretation:
        - < 0.2: Perfect (System "locked in" and stayed there)
        - > 1.0: Failure (System ended off-target or crashed at the end)
        """
        if not self.difficulties:
            return 0.0
        
        ema = self._calculate_ema(alpha)
        return round(abs(ema - self.theta), 3)

    def error_sensitivity(self) -> float:
        """
        Calculates % of times difficulty dropped after an error.
        Higher = More forgiving.
        
        Interpretation:
        - Novice Target: > 0.8 (Needs immediate help)
        - Expert Target: < 0.4 (Needs forgiveness for small slips)
        """
        error_indices = self._get_error_indices()
        if not error_indices:
            return 1.0
        
        drops = self._count_difficulty_drops(error_indices)
        return round(drops / len(error_indices), 2)

    def calibration_offset(self) -> float:
        """
        Calculates avg distance from target. 
        
        Interpretation:
        - Negative: Under-challenging (Too Easy)
        - Positive: Over-challenging (Too Hard)
        """
        if not self.difficulties:
            return 0.0
        
        avg_diff = sum(self.difficulties) / len(self.difficulties)
        return round(avg_diff - self.theta, 2)

    def weighted_proficiency(self) -> float:
        """
        Calculates score weighted by difficulty.
        Returns 0.0 to 1.0
        """
        total_points = sum(self.difficulties)
        if total_points == 0:
            return 0.0
        
        earned_points = sum(c * d for c, d in zip(self.correctness, self.difficulties))
        return round(earned_points / total_points, 4)

    def _calculate_ema(self, alpha: float) -> float:
        """Calculate exponential moving average of difficulties."""
        ema = float(self.difficulties[0])
        
        for d in self.difficulties[1:]:
            ema = (alpha * d) + ((1 - alpha) * ema)
        
        return ema

    def _get_error_indices(self) -> List[int]:
        """Get indices where student answered incorrectly."""
        return [i for i, x in enumerate(self.correctness) if x == 0]

    def _count_difficulty_drops(self, error_indices: List[int]) -> int:
        """Count how many times difficulty dropped after an error."""
        drops = 0
        for i in error_indices:
            if self._difficulty_dropped_after(i):
                drops += 1
        return drops

    def _difficulty_dropped_after(self, index: int) -> bool:
        """Check if difficulty dropped in the next turn after given index."""
        if index + 1 >= len(self.difficulties):
            return False
        return self.difficulties[index + 1] < self.difficulties[index]

