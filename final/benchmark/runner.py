import time
from typing import Dict, List, Any
from unittest.mock import MagicMock, patch

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from final.models import AgentState
from final.nodes import (
    question_creator_node,
    difficulty_reviewer_node,
    feedback_agent_node,
    orchestrator_node,
    present_question_node,
    route_orchestrator,
    route_after_feedback,
    route_after_question_creation,
    route_after_difficulty_review
)
from final.benchmark.simulated_student import SimulatedStudent
from final.benchmark.evaluator import BenchmarkEvaluator

class BenchmarkRunner:
    def __init__(self, student: SimulatedStudent, turns: int = 10):
        self.student = student
        self.turns = turns
        self.evaluator = BenchmarkEvaluator()
        self.results: List[Dict[str, Any]] = []
        
        # We need a custom graph for benchmarking that mimics the real one
        # but intercepts the "end" state to loop back if needed,
        # or we just run the graph per turn.
        # Running per turn is safer to control the loop and injection.
        self.workflow = self._build_workflow()
        
    def _build_workflow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("orchestrator", orchestrator_node)
        workflow.add_node("get_feedback", feedback_agent_node)
        workflow.add_node("create_question", question_creator_node)
        workflow.add_node("review_difficulty", difficulty_reviewer_node)
        workflow.add_node("present_question", present_question_node)

        workflow.set_entry_point("orchestrator")

        workflow.add_conditional_edges(
            "orchestrator",
            route_orchestrator,
            {
                "get_feedback": "get_feedback",
                "create_question": "create_question",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "get_feedback",
            route_after_feedback,
            {"create_question": "create_question"}
        )

        workflow.add_conditional_edges(
            "create_question",
            route_after_question_creation,
            {"review_difficulty": "review_difficulty"}
        )

        workflow.add_conditional_edges(
            "review_difficulty",
            route_after_difficulty_review,
            {
                "present_question": "present_question",
                "create_question": "create_question"
            }
        )

        workflow.add_edge("present_question", END)
        
        return workflow.compile()

    def run(self) -> str:
        """Runs the benchmark and returns a markdown report."""
        print(f"Starting benchmark for persona: {self.student.persona.__class__.__name__} with {self.turns} turns.")
        
        with patch('final.nodes.mcq_service') as mock_service:
            self._setup_initial_mock_state(mock_service)
            history = []
            state = self._get_initial_state()

            for turn in range(1, self.turns + 1):
                print(f"--- Turn {turn}/{self.turns} ---")
                self._update_mock_service(mock_service, history)
                
                result = self.workflow.invoke(state)
                turn_result = self._process_turn_result(result, turn)
                
                if turn_result:
                    history.append({
                        'is_correct': turn_result['is_correct'],
                        'answered_at': time.time()
                    })
                    self.results.append(turn_result)
                
                state = self._get_next_turn_state()
                
        return self._generate_report()

    def _setup_initial_mock_state(self, mock_service):
        mock_service.compute_user_score.return_value = {
            'total_questions': 0,
            'correct_count': 0,
            'incorrect_count': 0,
            'score_percentage': 0.0,
            'recent_performance': []
        }

    def _get_initial_state(self):
        return {
            "messages": [HumanMessage(content="Quiero una pregunta nueva")],
            "iteration_count": 0,
            "score_data": {}
        }

    def _get_next_turn_state(self):
        return {
            "messages": [HumanMessage(content="Dame otra pregunta")],
            "iteration_count": 0,
        }

    def _process_turn_result(self, result: Dict, turn: int) -> Dict[str, Any]:
        question = result.get("current_question")
        options = result.get("question_options")
        correct_idx = result.get("question_correct_index")
        
        if not question or not options:
            print("Error: No question generated in this turn.")
            return None
        
        difficulty_score = self.evaluator.evaluate_difficulty(question, options)
        student_answer_letter = self.student.answer_question(question, options)
        
        letter_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        student_idx = letter_map.get(student_answer_letter, -1)
        is_correct = (student_idx == correct_idx)
        
        return {
            "turn": turn,
            "question": question,
            "difficulty_score": difficulty_score,
            "is_correct": is_correct,
            "student_answer": student_answer_letter,
            "correct_answer": chr(65 + correct_idx)
        }

    def _update_mock_service(self, mock_service, history):
        total = len(history)
        if total == 0:
            return

        correct = sum(1 for h in history if h['is_correct'])
        incorrect = total - correct
        percentage = (correct / total) * 100 if total > 0 else 0
        
        # Recent (last 5)
        recent = history[-5:]
        
        mock_service.compute_user_score.return_value = {
            'total_questions': total,
            'correct_count': correct,
            'incorrect_count': incorrect,
            'score_percentage': percentage,
            'recent_performance': recent
        }
        
        mock_service.get_last_question_id.return_value = "mock_id"

    def _generate_report(self) -> str:
        persona_name = self.student.persona.__class__.__name__
        report = f"# Benchmark Report: {persona_name}\n\n"
        report += f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Total Turns**: {self.turns}\n\n"
        
        total_correct = sum(1 for r in self.results if r['is_correct'])
        accuracy = (total_correct / self.turns) * 100 if self.turns > 0 else 0
        
        report += f"## Summary\n"
        report += f"- **Accuracy**: {accuracy:.2f}%\n"
        report += f"- **Average Difficulty**: {sum(r['difficulty_score'] for r in self.results) / self.turns:.2f}\n\n"
        
        report += "## Adaptivity Analysis\n"
        report += "| Turn | Difficulty (1-5) | Result | Correct Answer |\n"
        report += "|---|---|---|---|\n"
        
        for r in self.results:
            status = "✅ Correct" if r['is_correct'] else "❌ Incorrect"
            report += f"| {r['turn']} | {r['difficulty_score']} | {status} | {r['correct_answer']} |\n"
            
        return report

