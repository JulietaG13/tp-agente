from abc import ABC, abstractmethod
from typing import List
import json
import re
from colorama import Fore, Style
from langchain_core.messages import HumanMessage, SystemMessage
from final.agents import create_model

class PersonaStrategy(ABC):
    """Abstract base class for student personas."""
    
    @property
    @abstractmethod
    def true_level(self) -> float:
        """Returns the expected difficulty level for this persona (1.0-5.0)."""
        pass
    
    @property
    @abstractmethod
    def target_sensitivity(self) -> float:
        """Returns the ideal error sensitivity for this persona (0.0-1.0)."""
        pass
    
    @property
    @abstractmethod
    def target_accuracy(self) -> float:
        """Returns the expected accuracy for this persona (0.0-1.0)."""
        pass
    
    @abstractmethod
    def get_system_prompt(self, turn_count: int) -> str:
        pass

class ExpertPersona(PersonaStrategy):
    @property
    def true_level(self) -> float:
        return 5.0
    
    @property
    def target_sensitivity(self) -> float:
        return 0.3
    
    @property
    def target_accuracy(self) -> float:
        return 0.75
    
    def get_system_prompt(self, turn_count: int) -> str:
        return """You are a simulated student taking a multiple choice test.
Your goal is to answer the question based strictly on your persona.
Return ONLY the letter of the option you choose (A, B, C, or D).

Persona: EXPERT. You are highly knowledgeable in the subject. You rarely make mistakes (95% accuracy). You are confident and critical of ambiguous questions."""

class NovicePersona(PersonaStrategy):
    @property
    def true_level(self) -> float:
        return 1.5
    
    @property
    def target_sensitivity(self) -> float:
        return 0.8
    
    @property
    def target_accuracy(self) -> float:
        return 0.78
    
    def get_system_prompt(self, turn_count: int) -> str:
        return """You are a simulated student taking a multiple choice test.
Return ONLY the letter of the option you choose (A, B, C, or D).

Persona: NOVICE with limited distributed systems knowledge.

Your Cognitive Profile:
- You understand basic terminology but struggle with subtle distinctions
- You are just starting to learn about the topic.
- Long, complex questions and options overwhelm you and you miss key details
- When a question combines multiple concepts, you fail to integrate them properly
- Technical jargon and formal definitions confuse you
- You're prone to selecting "distractors" - answers that sound right superficially
- You tend to oversimplify complex scenarios

Performance Characteristics:
- Simple, direct questions: ~70% accuracy
- Complex or multi-part questions: ~30% accuracy
- When uncertain, you pick answers based on familiarity rather than deep analysis

You do NOT guess randomly. You do NOT act as an expert. You genuinely try to reason, but your limited knowledge leads to systematic errors on harder material."""

class LearnerPersona(PersonaStrategy):
    @property
    def true_level(self) -> float:
        return 3.0
    
    @property
    def target_sensitivity(self) -> float:
        return 0.6
    
    @property
    def target_accuracy(self) -> float:
        return 0.70
    
    def get_system_prompt(self, turn_count: int) -> str:
        base = """You are a simulated student taking a multiple choice test.
Your goal is to answer the question based strictly on your persona.
Return ONLY the letter of the option you choose (A, B, C, or D).

Persona: LEARNER. You start with low knowledge but learn from feedback (simulated improvement)."""
        
        if turn_count <= 5:
            return base + "\nCURRENT STATE: You are at the beginning of your learning journey. Behave like a Novice."
        elif turn_count <= 10:
            return base + "\nCURRENT STATE: You are starting to understand the concepts. You get some right, some wrong."
        else:
            return base + "\nCURRENT STATE: You have studied hard. Behave like an Expert."

class SimulatedStudent:
    def __init__(self, persona: PersonaStrategy):
        self.llm = create_model()
        self.persona = persona
        self.turn_count = 0
        
    def answer_question(self, question: str, options: List[str]) -> str:
        self.turn_count += 1
        
        system_prompt = self.persona.get_system_prompt(self.turn_count)
        system_prompt = self._with_output_format(system_prompt)
        
        formatted_options = "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
        user_message = (
            f"Question: {question}\n\n"
            f"Options:\n{formatted_options}\n\n"
            "You may reason in plain text, but you MUST end your message with a single JSON object like:\n"
            '{"answer":"A"}\n'
            "and nothing after it."
        )
        
        self._log_student_input(system_prompt, user_message)
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        raw = response.content.strip()
        picked, method = self._extract_choice(raw)
        self._log_student_output(raw, picked, method)
        return picked

    def _with_output_format(self, system_prompt: str) -> str:
        return (
            f"{system_prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "- You may include reasoning.\n"
            '- You MUST end your message with a single JSON object exactly like: {"answer":"A"}\n'
            "- The JSON must be the last thing in your message (no trailing text).\n"
            "- answer must be exactly one of: A, B, C, D."
        )

    def _extract_choice(self, raw: str) -> tuple[str, str]:
        content = (raw or "").strip()
        try:
            data = self._extract_json_object(content)
            answer = str(data.get("answer", "")).strip().upper()
            if answer in "ABCD":
                return answer, "json"
        except Exception:
            pass

        # Fallback: take the LAST standalone option letter (avoids matching "Option A" early).
        matches = re.findall(r"\b([A-D])\b", content.upper())
        if matches:
            return matches[-1], "fallback_last_letter"

        # Final fallback: first character if it looks like a choice
        upper = content.upper()
        if upper and upper[0] in "ABCD":
            return upper[0], "fallback_first_char"

        return "A", "fallback_default"

    def _extract_json_object(self, text: str) -> dict:
        try:
            return json.loads(text)
        except Exception:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))

        obj = re.search(r"\{[\s\S]*\}", text)
        if obj:
            return json.loads(obj.group(0))

        raise ValueError("Could not parse JSON object")

    def _persona_name(self) -> str:
        return self.persona.__class__.__name__

    def _log_student_input(self, system_prompt: str, user_message: str) -> None:
        header = f"{Fore.LIGHTMAGENTA_EX}🎓 [STUDENT]{Style.RESET_ALL} persona={self._persona_name()} turn={self.turn_count}"
        print(header)
        print(f"{Fore.LIGHTMAGENTA_EX}🎓 [STUDENT]{Style.RESET_ALL} system_prompt:\n{system_prompt}")
        print(f"{Fore.LIGHTMAGENTA_EX}🎓 [STUDENT]{Style.RESET_ALL} user_message:\n{user_message}")

    def _log_student_output(self, raw: str, picked: str, method: str) -> None:
        print(f"{Fore.LIGHTMAGENTA_EX}🎓 [STUDENT]{Style.RESET_ALL} raw_llm_output:\n{raw}")
        print(f"{Fore.LIGHTMAGENTA_EX}🎓 [STUDENT]{Style.RESET_ALL} extracted_choice={picked} method={method}")
