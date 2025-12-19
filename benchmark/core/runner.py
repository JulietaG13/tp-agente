import time
from typing import Dict, List, Any
from tqdm import tqdm

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
from services.service_manager import initialize_session_services, get_service
from tools.tools import check_multiple_choice_answer
from benchmark.core.simulated_student import SimulatedStudent
from benchmark.core.evaluator import BenchmarkEvaluator
from benchmark.core.topic_labeler import TopicLabeler

class BenchmarkRunner:
    def __init__(self, student: SimulatedStudent, turns: int = 10, sleep_duration: float = 0):
        self.student = student
        self.turns = turns
        self.sleep_duration = sleep_duration
        self.evaluator = BenchmarkEvaluator()
        self.topic_labeler = TopicLabeler()
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
        workflow.add_node("create_mcq_question", question_creator_node)
        workflow.add_node("create_open_question", question_creator_node)
        workflow.add_node("review_difficulty", difficulty_reviewer_node)
        workflow.add_node("present_question", present_question_node)

        workflow.set_entry_point("orchestrator")

        workflow.add_conditional_edges(
            "orchestrator",
            route_orchestrator,
            {
                "get_feedback": "get_feedback",
                "create_mcq_question": "create_mcq_question",
                "create_open_question": "create_open_question",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "get_feedback",
            route_after_feedback,
            {
                "create_mcq_question": "create_mcq_question",
                "create_open_question": "create_open_question"
            }
        )

        workflow.add_conditional_edges(
            "create_mcq_question",
            route_after_question_creation,
            {
                "review_difficulty": "review_difficulty",
                "create_mcq_question": "create_mcq_question",
                "create_open_question": "create_open_question"
            }
        )

        workflow.add_conditional_edges(
            "create_open_question",
            route_after_question_creation,
            {
                "review_difficulty": "review_difficulty",
                "create_mcq_question": "create_mcq_question",
                "create_open_question": "create_open_question"
            }
        )

        workflow.add_conditional_edges(
            "review_difficulty",
            route_after_difficulty_review,
            {
                "present_question": "present_question",
                "create_mcq_question": "create_mcq_question",
                "create_open_question": "create_open_question"
            }
        )

        workflow.add_edge("present_question", END)

        return workflow.compile()

    def run(self) -> Dict:
        """Runs the benchmark and returns raw results data."""
        print(f"Starting benchmark for persona: {self.student.persona.__class__.__name__} with {self.turns} turns.")
        initialize_session_services()
        state = self._get_initial_state()

        for turn in range(1, self.turns + 1):
            print(f"--- Turn {turn}/{self.turns} ---")

            state, success = self._execute_single_turn(turn, state)
            if not success:
                break

        return self._prepare_raw_results()

    def _execute_single_turn(self, turn: int, state: Dict) -> tuple[Dict, bool]:
        try:
            start_time = time.time()
            result = self.workflow.invoke(state)
            generation_time = time.time() - start_time

            turn_result = self._process_turn_result(result, turn, generation_time)

            if turn_result:
                self.results.append(turn_result)
            
            next_state = self._get_next_turn_state()
            
            if self.sleep_duration > 0 and turn < self.turns:
                self._sleep_with_progress(turn)
                
            return next_state, True
            
        except Exception as e:
            print(f"Error in turn {turn}: {e}")
            return state, False

    def _get_initial_state(self):
        return self._base_state("Quiero una pregunta nueva")

    def _get_next_turn_state(self):
        return self._base_state("Dame otra pregunta")

    def _base_state(self, user_msg: str) -> Dict:
        return {
            "messages": [HumanMessage(content=user_msg)],
            "question_type": "",
            "current_question": "",
            "question_options": [],
            "question_correct_index": 0,
            "open_question": "",
            "open_evaluation_criteria": "",
            "open_key_concepts": [],
            "open_question_difficulty": "",
            "difficulty_feedback": "",
            "user_feedback": "",
            "score_data": {},
            "iteration_count": 0,
            "question_approved": False,
            "next_action": "",
            "question_type_decision": "",
            "question_id": "",
            "user_open_answer": "",
            "evaluation_score": 0.0,
            "evaluation_feedback": "",
            "evaluation_passing": False,
        }

    def _process_turn_result(self, result: Dict, turn: int, generation_time: float) -> Dict[str, Any]:
        question_id = result.get("question_id")
        if not question_id:
            print("Error: No question_id generated in this turn.")
            return None

        service = get_service()
        q_data = service.get_question(question_id)
        if not q_data:
            print("Error: Question not found in service.")
            return None

        question = q_data.get("question")
        options = q_data.get("options")
        correct_answer = q_data.get("correct_answer")
        if not question or not options:
            print("Error: Question data incomplete.")
            return None

        correct_idx = options.index(correct_answer) if correct_answer in options else -1
        
        difficulty_score = self.evaluator.evaluate_difficulty(question, options)
        subtopic_ids = self.topic_labeler.label_question(question, options)
        student_answer_letter = self.student.answer_question(question, options)
        check_multiple_choice_answer(question_id, student_answer_letter)
        answer_data = service.get_user_answer(question_id) or {}
        is_correct = bool(answer_data.get("is_correct", False))
        
        return {
            "turn": turn,
            "question": question,
            "options": options,
            "difficulty_score": difficulty_score,
            "subtopics": subtopic_ids,
            "is_correct": is_correct,
            "student_answer": student_answer_letter,
            "correct_answer": chr(65 + correct_idx) if 0 <= correct_idx <= 3 else "?",
            "generation_time_seconds": round(generation_time, 2)
        }

    def _sleep_with_progress(self, current_turn: int):
        """Sleep between turns with progress indicator."""
        print(f"\n⏳ Rate limit protection: Waiting {self.sleep_duration}s before next turn...")
        
        for _ in tqdm(range(int(self.sleep_duration * 10)), desc="Sleeping", unit="0.1s", ncols=80):
            time.sleep(0.1)
        
        print()

    def _prepare_raw_results(self) -> Dict:
        """Prepare raw results for serialization."""
        generation_times = [r['generation_time_seconds'] for r in self.results if 'generation_time_seconds' in r]

        timing_stats = {}
        if generation_times:
            timing_stats = {
                'average_generation_time_seconds': round(sum(generation_times) / len(generation_times), 2),
                'min_generation_time_seconds': round(min(generation_times), 2),
                'max_generation_time_seconds': round(max(generation_times), 2),
                'total_generation_time_seconds': round(sum(generation_times), 2)
            }

        return {
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'turns_planned': self.turns,
                'turns_completed': len(self.results),
                'persona_type': self.student.persona.__class__.__name__,
                **timing_stats
            },
            'persona_config': {
                'true_level': self.student.persona.true_level,
                'target_sensitivity': self.student.persona.target_sensitivity,
                'target_accuracy': self.student.persona.target_accuracy
            },
            'results': self.results
        }

