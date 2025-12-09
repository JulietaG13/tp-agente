from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from final.agents import create_model
import re

class BenchmarkEvaluator:
    def __init__(self):
        self.llm = create_model()

    def evaluate_difficulty(self, question: str, options: List[str]) -> int:
        """
        Evaluates the difficulty of a question on a scale of 1-5.
        1 = Very Easy
        5 = Very Hard
        """
        
        system_prompt = """You are an objective educational expert. 
Your task is to analyze a multiple-choice question and assign it a difficulty score from 1 to 5.

Scale:
1: Recall of basic facts, obvious answer.
2: Simple concept understanding.
3: Application of concepts, require some reasoning.
4: Analysis or complex reasoning, close distractors.
5: Synthesis/Evaluation, very subtle distinctions, complex scenario.

Output ONLY the number (1-5)."""

        formatted_options = "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
        user_message = f"""Analyze the difficulty of this question:

Question: {question}

Options:
{formatted_options}

Return ONLY the difficulty score (1-5)."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            content = response.content.strip()
            # Extract number
            match = re.search(r'\b([1-5])\b', content)
            if match:
                return int(match.group(1))
            else:
                # Fallback
                if content.isdigit() and 1 <= int(content) <= 5:
                    return int(content)
                return 3 # Default to moderate if parsing fails
        except Exception as e:
            print(f"Error evaluating difficulty: {e}")
            return 3

