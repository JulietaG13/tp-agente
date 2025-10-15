import os
from typing import List, Dict, Optional
import uuid
from datetime import datetime


class MCQService:
    def __init__(self):
        self._questions: Dict[str, Dict] = {}
        self._answers: Dict[str, Dict] = {}
    
    def store_question(self, question: str, options: List[str], correct_answer: str) -> str:
        """Almacena una pregunta de opción múltiple y retorna su ID"""
        question_id = str(uuid.uuid4())
        self._questions[question_id] = {
            'question': question,
            'options': options,
            'correct_answer': correct_answer,
            'created_at': datetime.now()
        }
        return question_id
    
    def get_question(self, question_id: str) -> Optional[Dict]:
        """Obtiene una pregunta por su ID"""
        return self._questions.get(question_id)
    
    def store_user_answer(self, question_id: str, user_answer: str, is_correct: bool) -> bool:
        """Almacena la respuesta del usuario y si fue correcta"""
        if question_id not in self._questions:
            return False
        
        self._answers[question_id] = {
            'user_answer': user_answer,
            'is_correct': is_correct,
            'answered_at': datetime.now()
        }
        return True
    
    def get_user_answer(self, question_id: str) -> Optional[Dict]:
        """Obtiene la respuesta del usuario para una pregunta"""
        return self._answers.get(question_id)
    
    def get_all_questions(self) -> Dict[str, Dict]:
        """Obtiene todas las preguntas almacenadas"""
        return self._questions.copy()
    
    def get_all_answers(self) -> Dict[str, Dict]:
        """Obtiene todas las respuestas almacenadas"""
        return self._answers.copy()

    def get_last_question_id(self) -> Optional[str]:
        """Retorna el ID de la pregunta creada más recientemente"""
        if not self._questions:
            return None
        return max(self._questions.items(), key=lambda item: item[1].get('created_at'))[0]


class FileService:
    @staticmethod
    def read_txt_file(file_path: str) -> str:
        if not file_path.endswith('.txt'):
            raise ValueError(f"El archivo debe tener extensión .txt: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def search_in_file(file_path: str, search_term: str,
                      case_sensitive: bool = False) -> List[Dict[str, any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        results = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line_to_search = line if case_sensitive else line.lower()
                term_to_search = search_term if case_sensitive else search_term.lower()
                if term_to_search in line_to_search:
                    results.append({
                        "line_number": line_num,
                        "content": line.strip(),
                        "file_path": file_path
                    })
        return results