import math
from typing import Dict, List


class TopicHistoryBuilder:
    """Builds per-topic correctness history from benchmark results."""
    
    def build_history(self, results: List[Dict]) -> Dict[int, List[bool]]:
        """
        Build history tracking correctness for each topic across all questions.
        
        Args:
            results: List of turn results with 'subtopics' and 'is_correct' fields
            
        Returns:
            Dictionary mapping topic_id -> list of correctness booleans
        """
        topic_history = {}
        
        for result in results:
            subtopics = result.get('subtopics', [])
            is_correct = result.get('is_correct', False)
            
            for topic_id in subtopics:
                if topic_id not in topic_history:
                    topic_history[topic_id] = []
                topic_history[topic_id].append(is_correct)
        
        return topic_history


class CoverageMetricsCalculator:
    """Calculates curriculum coverage metrics."""
    
    def __init__(self, topic_history: Dict[int, List[bool]], total_topics: int, total_turns: int):
        self.topic_history = topic_history
        self.total_topics = total_topics
        self.total_turns = total_turns
    
    def _calculate_expected_coverage_capacity(self) -> int:
        """
        Calculate expected topic coverage capacity.
        Assumption: A session can cover topics twice the number of turns (at most 2 topics per turn).
        """
        expected = math.ceil(self.total_turns * 2)
        return min(self.total_topics, expected)

    def calculate_syllabus_exposure(self) -> float:
        """Percentage of topics that appeared in any question (relative to capacity)."""
        capacity = self._calculate_expected_coverage_capacity()
        if capacity == 0:
            return 0.0
        
        topics_attempted = len(self.topic_history)
        # Cap at 1.0 in case attempted > capacity (e.g. multi-topic questions)
        return round(min(1.0, topics_attempted / capacity), 4)
    
    def calculate_effective_coverage(self) -> float:
        """Percentage of topics user answered correctly at least once (relative to capacity)."""
        capacity = self._calculate_expected_coverage_capacity()
        if capacity == 0:
            return 0.0
        
        topics_passed = self._count_passed_topics()
        return round(min(1.0, topics_passed / capacity), 4)
    
    def calculate_remediation_efficiency(self) -> float:
        """Percentage of initially-failed topics that were later recovered."""
        failed_first = self._identify_initially_failed_topics()
        
        if len(failed_first) == 0:
            return 1.0
        
        recovered = self._count_recovered_topics(failed_first)
        return round(recovered / len(failed_first), 4)
    
    def identify_topic_statuses(self) -> Dict[int, str]:
        """
        Returns status for each topic: 'mastered', 'recovered', 'failed', 'missed'.
        
        Status definitions:
        - 'mastered': First attempt was correct
        - 'recovered': First attempt failed, but later succeeded
        - 'failed': Attempted but never answered correctly
        - 'missed': Never appeared in any question
        """
        statuses = {}
        
        for topic_id in range(self.total_topics):
            if topic_id not in self.topic_history:
                statuses[topic_id] = 'missed'
            else:
                history = self.topic_history[topic_id]
                statuses[topic_id] = self._determine_topic_status(history)
        
        return statuses
    
    def _count_passed_topics(self) -> int:
        """Count topics where at least one question was answered correctly."""
        count = 0
        for history in self.topic_history.values():
            if any(history):
                count += 1
        return count
    
    def _identify_initially_failed_topics(self) -> set:
        """Identify topics where the first encounter was incorrect."""
        failed_first = set()
        
        for topic_id, history in self.topic_history.items():
            if history and not history[0]:
                failed_first.add(topic_id)
        
        return failed_first
    
    def _count_recovered_topics(self, failed_first: set) -> int:
        """Count topics that were initially failed but later passed."""
        recovered = 0
        
        for topic_id in failed_first:
            history = self.topic_history[topic_id]
            if any(history):
                recovered += 1
        
        return recovered
    
    def _determine_topic_status(self, history: List[bool]) -> str:
        """Determine status based on topic history."""
        if not history:
            return 'missed'
        
        first_correct = history[0]
        ever_correct = any(history)
        
        if first_correct:
            return 'mastered'
        elif ever_correct:
            return 'recovered'
        else:
            return 'failed'

