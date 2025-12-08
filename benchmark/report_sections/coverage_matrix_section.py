from typing import Dict, List


class CoverageMatrixSection:
    """Generates topic coverage matrix visualization."""
    
    def generate_section(self, topic_statuses: Dict[int, str], subtopics: List[str]) -> str:
        """
        Generate topic coverage matrix showing per-topic performance.
        
        Args:
            topic_statuses: Dictionary mapping topic_id -> status string
            subtopics: List of subtopic names
        """
        mastered = []
        recovered = []
        failed = []
        missed = []
        
        for topic_id, status in topic_statuses.items():
            if status == 'mastered':
                mastered.append((topic_id, subtopics[topic_id]))
            elif status == 'recovered':
                recovered.append((topic_id, subtopics[topic_id]))
            elif status == 'failed':
                failed.append((topic_id, subtopics[topic_id]))
            elif status == 'missed':
                missed.append((topic_id, subtopics[topic_id]))
        
        report = "## Topic Coverage Matrix\n\n"
        
        report += self._generate_status_summary(len(mastered), len(recovered), len(failed), len(missed))
        report += "\n\n---\n\n"
        
        if mastered:
            report += self._generate_topic_list("✅ Mastered (First Try)", mastered)
        
        if recovered:
            report += self._generate_topic_list("🔄 Recovered (Improved After Failure)", recovered)
        
        if failed:
            report += self._generate_topic_list("❌ Failed (Never Answered Correctly)", failed)
        
        if missed:
            report += self._generate_topic_list("⚪ Missed (System Never Asked)", missed)
        
        return report
    
    def _generate_status_summary(
        self, 
        mastered: int, 
        recovered: int, 
        failed: int, 
        missed: int
    ) -> str:
        """Generate summary statistics for topic statuses."""
        total = mastered + recovered + failed + missed
        
        return (
            "### Summary\n"
            f"- **Mastered**: {mastered} topics ({mastered/total*100 if total > 0 else 0:.1f}%)\n"
            f"- **Recovered**: {recovered} topics ({recovered/total*100 if total > 0 else 0:.1f}%)\n"
            f"- **Failed**: {failed} topics ({failed/total*100 if total > 0 else 0:.1f}%)\n"
            f"- **Missed**: {missed} topics ({missed/total*100 if total > 0 else 0:.1f}%)\n"
        )
    
    def _generate_topic_list(self, title: str, topics: List[tuple]) -> str:
        """Generate a formatted list of topics."""
        if not topics:
            return ""
        
        result = f"### {title}\n\n"
        for topic_id, topic_name in topics:
            result += f"- `[{topic_id}]` {topic_name}\n"
        result += "\n"
        
        return result

