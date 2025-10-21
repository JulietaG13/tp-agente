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
    
    def compute_user_score(self) -> Dict:
        """Calcula el puntaje y métricas de rendimiento del usuario"""
        total_questions = len(self._answers)
        if total_questions == 0:
            return {
                'total_questions': 0,
                'correct_count': 0,
                'incorrect_count': 0,
                'score_percentage': 0.0,
                'recent_performance': []
            }
        
        correct_count = sum(1 for ans in self._answers.values() if ans['is_correct'])
        incorrect_count = total_questions - correct_count
        score_percentage = (correct_count / total_questions) * 100
        
        # Obtener las últimas 5 respuestas
        sorted_answers = sorted(
            self._answers.items(),
            key=lambda x: x[1]['answered_at']
        )
        recent_answers = sorted_answers[-5:]
        recent_performance = [
            {
                'question_id': qid,
                'is_correct': ans['is_correct'],
                'answered_at': ans['answered_at']
            }
            for qid, ans in recent_answers
        ]
        
        return {
            'total_questions': total_questions,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'score_percentage': score_percentage,
            'recent_performance': recent_performance
        }
    
    def get_answer_history(self) -> List[Dict]:
        """Retorna historial cronológico de respuestas"""
        sorted_answers = sorted(
            self._answers.items(),
            key=lambda x: x[1]['answered_at']
        )
        
        history = []
        for qid, ans in sorted_answers:
            question_data = self._questions.get(qid, {})
            history.append({
                'question_id': qid,
                'question': question_data.get('question', ''),
                'user_answer': ans['user_answer'],
                'correct_answer': question_data.get('correct_answer', ''),
                'is_correct': ans['is_correct'],
                'answered_at': ans['answered_at']
            })
        
        return history


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