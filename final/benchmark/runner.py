import time
from typing import Dict, List, Any, Optional

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
from tools.tools import ToolSet, MCQService, FileService

class BenchmarkRunner:
    def __init__(self, student: SimulatedStudent, turns: int = 10):
        self.student = student
        self.turns = turns
        self.evaluator = BenchmarkEvaluator()
        self.results: List[Dict[str, Any]] = []
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
        
        mcq_service, toolset = self._initialize_isolated_environment()
        state = self._create_initial_state(toolset)

        for turn in range(1, self.turns + 1):
            print(f"--- Turn {turn}/{self.turns} ---")
            
            result_state = self.workflow.invoke(state)
            
            turn_metrics = self._process_turn_and_evaluate(result_state, turn)
            
            if turn_metrics:
                self._record_student_answer(mcq_service, toolset, turn_metrics)
                self.results.append(turn_metrics)
            
            state = self._prepare_next_turn_state(toolset)
                
        return self._generate_report()

    def _initialize_isolated_environment(self):
        """Creates a fresh service and toolset to ensure benchmark isolation."""
        fresh_mcq_service = MCQService()
        fresh_toolset = ToolSet(mcq_service=fresh_mcq_service)
        return fresh_mcq_service, fresh_toolset

    def _create_initial_state(self, toolset: ToolSet) -> Dict:
        return {
            "messages": [HumanMessage(content="Quiero una pregunta nueva")],
            "iteration_count": 0,
            "score_data": {},
            "toolset": toolset
        }

    def _process_turn_and_evaluate(self, result_state: Dict, turn: int) -> Optional[Dict[str, Any]]:
        """Extracts question, evaluates difficulty, and gets student answer."""
        question = result_state.get("current_question")
        options = result_state.get("question_options")
        correct_idx = result_state.get("question_correct_index")
        
        if not question or not options:
            print("Error: No question generated in this turn.")
            return None
        
        difficulty_score = self.evaluator.evaluate_difficulty(question, options)
        student_answer_letter = self.student.answer_question(question, options)
        
        is_correct = self._check_answer_correctness(student_answer_letter, correct_idx)
        
        return {
            "turn": turn,
            "question": question,
            "difficulty_score": difficulty_score,
            "is_correct": is_correct,
            "student_answer": student_answer_letter,
            "correct_answer": chr(65 + correct_idx),
            "options": options
        }

    def _check_answer_correctness(self, student_answer: str, correct_idx: int) -> bool:
        letter_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        student_idx = letter_map.get(student_answer, -1)
        return student_idx == correct_idx

    def _record_student_answer(self, mcq_service: MCQService, toolset: ToolSet, turn_metrics: Dict):
        """Registers the simulated student's answer in the service to update history."""
        # The 'present_question_node' returns the ID, but we can reliably get the last created ID
        last_id = mcq_service.get_last_question_id()
        if last_id:
             toolset.check_multiple_choice_answer(last_id, turn_metrics['student_answer'])

    def _prepare_next_turn_state(self, toolset: ToolSet) -> Dict:
        return {
            "messages": [HumanMessage(content="Dame otra pregunta")],
            "iteration_count": 0,
            "toolset": toolset
        }

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
