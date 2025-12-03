from services.service import FileService, MCQService

# By default we can create a global one for backward compatibility if needed, 
# but we will prefer using the class methods.
# For now, we keep the global instances to serve as default for the wrapper functions,
# but we expose a ToolFactory.

_default_file_service = FileService()
_default_mcq_service = MCQService()

class ToolSet:
    def __init__(self, mcq_service: MCQService = None, file_service: FileService = None):
        self.mcq_service = mcq_service or _default_mcq_service
        self.file_service = file_service or _default_file_service

    def read_text_file(self, file_path: str) -> str:
        try:
            content = self.file_service.read_txt_file(file_path)
            return content
        except Exception as e:
            return f"Error al leer el archivo: {str(e)}"

    def search_in_text_file(self, file_path: str, search_term: str, case_sensitive: bool = False) -> str:
        try:
            results = self.file_service.search_in_file(file_path, search_term, case_sensitive)
            if not results:
                return f"No se encontraron resultados para '{search_term}' en el archivo."
            output = f"Encontrados {len(results)} resultados para '{search_term}':\n\n"
            for result in results:
                output += f"Línea {result['line_number']}: {result['content']}\n"
            return output
        except Exception as e:
            return f"Error en búsqueda: {str(e)}"

    def check_multiple_choice_answer(self, question_id: str, user_answer: str) -> str:
        try:
            question_data = self.mcq_service.get_question(question_id)
            if not question_data:
                return f"Error: No se encontró pregunta con ID {question_id}"
            
            correct_answer = question_data["correct_answer"]
            options = question_data["options"]
            
            user_answer_text = user_answer
            if len(user_answer) == 1 and user_answer.upper() in 'ABCD':
                letter_index = ord(user_answer.upper()) - ord('A')
                if 0 <= letter_index < len(options):
                    user_answer_text = options[letter_index]
            
            is_correct = user_answer_text == correct_answer
            self.mcq_service.store_user_answer(question_id, user_answer_text, is_correct)
            
            result = f"Respuesta registrada para pregunta {question_id}\n\n"
            result += f"Tu respuesta: {user_answer_text}\n"
            result += f"Respuesta correcta: {correct_answer}\n"
            result += f"Resultado: {'✓ CORRECTO' if is_correct else '✗ INCORRECTO'}"
            return result
        except Exception as e:
            return f"Error al verificar respuesta: {str(e)}"

    def check_last_multiple_choice_answer(self, user_answer: str) -> str:
        try:
            last_id = self.mcq_service.get_last_question_id()
            if not last_id:
                return "Error: No hay preguntas registradas aún"
            return self.check_multiple_choice_answer(last_id, user_answer)
        except Exception as e:
            return f"Error al verificar respuesta para la última pregunta: {str(e)}"

    def register_multiple_choice_question(self, question: str, options: list, correct_index: int) -> str:
        try:
            if not isinstance(options, list):
                return "Error: 'options' debe ser una lista de 4 strings"
            if len(options) != 4:
                return "Error: Deben proveerse exactamente 4 opciones"
            if not all(isinstance(opt, str) and opt.strip() for opt in options):
                return "Error: Todas las opciones deben ser strings no vacíos"
            if not isinstance(correct_index, int) or not (0 <= correct_index < 4):
                return "Error: 'correct_index' debe ser un entero entre 0 y 3"

            import random
            indexed_options = list(enumerate(options))
            random.shuffle(indexed_options)
            shuffled_options = [opt for _, opt in indexed_options]
            
            original_correct_answer = options[correct_index]
            correct_answer = original_correct_answer
            question_id = self.mcq_service.store_question(question, shuffled_options, correct_answer)

            result = f"Pregunta registrada con ID: {question_id}\n\n"
            result += f"Pregunta: {question}\n\n"
            result += "Opciones:\n"
            for i, option in enumerate(shuffled_options, 1):
                result += f"{chr(64+i)}) {option}\n"
            return result
        except Exception as e:
            return f"Error al registrar pregunta: {str(e)}"

    def list_multiple_choice_questions(self, limit: int = 20) -> str:
        try:
            all_questions = self.mcq_service.get_all_questions()
            items = list(all_questions.items())
            items.sort(key=lambda kv: kv[1].get("created_at"))
            if limit is not None:
                items = items[-limit:]
            lines = []
            for qid, data in items:
                question = data.get("question", "")
                options = data.get("options", [])
                lines.append(f"ID: {qid}\nPregunta: {question}\nOpciones:\n" + "\n".join(
                    [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)]
                ))
            return "\n\n".join(lines) if lines else "Sin preguntas registradas"
        except Exception as e:
            return f"Error al listar preguntas: {str(e)}"

    def get_user_performance(self) -> str:
        try:
            score_data = self.mcq_service.compute_user_score()
            if score_data['total_questions'] == 0:
                return "No hay respuestas registradas todavía. El usuario no ha respondido ninguna pregunta."
            
            result = f"=== RENDIMIENTO DEL USUARIO ===\n\n"
            result += f"Total de preguntas respondidas: {score_data['total_questions']}\n"
            result += f"Respuestas correctas: {score_data['correct_count']}\n"
            result += f"Respuestas incorrectas: {score_data['incorrect_count']}\n"
            result += f"Porcentaje de aciertos: {score_data['score_percentage']:.1f}%\n\n"
            
            if score_data['recent_performance']:
                result += "Rendimiento reciente (últimas 5 respuestas):\n"
                for i, perf in enumerate(score_data['recent_performance'], 1):
                    status = "✓ CORRECTO" if perf['is_correct'] else "✗ INCORRECTO"
                    result += f"  {i}. {status}\n"
            return result
        except Exception as e:
            return f"Error al obtener rendimiento: {str(e)}"

    def get_answer_history_detailed(self) -> str:
        try:
            history = self.mcq_service.get_answer_history()
            if not history:
                return "No hay historial de respuestas todavía."
            
            result = f"=== HISTORIAL DE RESPUESTAS ({len(history)} preguntas) ===\n\n"
            for i, entry in enumerate(history, 1):
                result += f"--- Pregunta {i} ---\n"
                result += f"Pregunta: {entry['question']}\n"
                result += f"Respuesta del usuario: {entry['user_answer']}\n"
                result += f"Respuesta correcta: {entry['correct_answer']}\n"
                result += f"Resultado: {'✓ CORRECTO' if entry['is_correct'] else '✗ INCORRECTO'}\n\n"
            return result
        except Exception as e:
            return f"Error al obtener historial: {str(e)}"

# Default ToolSet for backward compatibility
_default_tools = ToolSet()

# Expose functions that use the default toolset (to maintain current API)
read_text_file = _default_tools.read_text_file
search_in_text_file = _default_tools.search_in_text_file
check_multiple_choice_answer = _default_tools.check_multiple_choice_answer
check_last_multiple_choice_answer = _default_tools.check_last_multiple_choice_answer
register_multiple_choice_question = _default_tools.register_multiple_choice_question
list_multiple_choice_questions = _default_tools.list_multiple_choice_questions
get_user_performance = _default_tools.get_user_performance
get_answer_history_detailed = _default_tools.get_answer_history_detailed
mcq_service = _default_tools.mcq_service # For direct access if needed
