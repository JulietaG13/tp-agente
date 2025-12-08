from abc import ABC, abstractmethod
from typing import List
import re
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
        return 0.65
    
    def get_system_prompt(self, turn_count: int) -> str:
        return """You are a simulated student taking a multiple choice test.
Your goal is to answer the question based strictly on your persona.
Return ONLY the letter of the option you choose (A, B, C, or D).

Persona: NOVICE. You have little knowledge of the subject. You often guess randomly or fall for distractors. You are easily confused."""

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
        
        formatted_options = "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
        user_message = f"Question: {question}\n\nOptions:\n{formatted_options}\n\nSelect the best answer (A/B/C/D):"
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        content = response.content.strip().upper()
        # Extract just the letter if the LLM was verbose
        if len(content) > 1:
            match = re.search(r'\b([A-D])\b', content)
            if match:
                content = match.group(1)
            else:
                if content[0] in "ABCD":
                    content = content[0]
        
        return content
