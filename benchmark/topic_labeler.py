import json
import os
import re
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from final.agents import create_model


class SubtopicLoader:
    """Loads and provides access to subtopic definitions."""
    
    def load_subtopics(self) -> List[str]:
        """Load subtopics from JSON file."""
        subtopics_path = os.path.join(
            os.path.dirname(__file__), 
            "content", 
            "subtopics.json"
        )
        
        with open(subtopics_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class TopicLabeler:
    """Labels questions with relevant subtopic IDs using LLM."""
    
    def __init__(self):
        self.llm = create_model()
        self.subtopics = SubtopicLoader().load_subtopics()
    
    def label_question(self, question: str, options: List[str]) -> List[int]:
        """Returns list of subtopic indices (0-based) covered in question."""
        prompt = self._build_labeling_prompt(question, options)
        response = self._invoke_llm(prompt)
        return self._parse_subtopic_indices(response)
    
    def _build_labeling_prompt(self, question: str, options: List[str]) -> str:
        subtopics_list = self._format_subtopics_for_prompt()
        formatted_options = "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
        
        return f"""Given the following list of subtopics (numbered from 0 to {len(self.subtopics)-1}):

{subtopics_list}

Analyze this multiple-choice question and identify which subtopics are covered:

Question: {question}

Options:
{formatted_options}

Return ONLY a comma-separated list of the subtopic indices (numbers) that are covered in this question.
For example: "0,5,12" or "3" or "7,15,20"

Response:"""
    
    def _format_subtopics_for_prompt(self) -> str:
        return "\n".join([f"{i}. {topic}" for i, topic in enumerate(self.subtopics)])
    
    def _invoke_llm(self, prompt: str) -> str:
        response = self.llm.invoke([
            SystemMessage(content="You are an expert at analyzing educational content and identifying topics."),
            HumanMessage(content=prompt)
        ])
        return response.content.strip()
    
    def _parse_subtopic_indices(self, response: str) -> List[int]:
        numbers = re.findall(r'\d+', response)
        indices = [int(n) for n in numbers if 0 <= int(n) < len(self.subtopics)]
        return sorted(list(set(indices)))

