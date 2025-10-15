from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from services.service import FileService, MCQService
from tools.tools import check_multiple_choice_answer as check_answer_func
from tools.tools import register_multiple_choice_question as register_mcq_func

load_dotenv()

file_service = FileService()
mcq_service = MCQService()


@tool
def read_text_file(file_path: str) -> str:
    """Lee el contenido completo de un archivo .txt"""
    try:
        return file_service.read_txt_file(file_path)
    except Exception as e:
        return f"Error al leer el archivo: {str(e)}"


@tool
def search_in_text_file(file_path: str, search_term: str, case_sensitive: bool = False) -> str:
    """Busca un término en un archivo .txt"""
    try:
        results = file_service.search_in_file(file_path, search_term, case_sensitive)
        if not results:
            return f"No se encontraron resultados para '{search_term}' en el archivo."
        output = f"Encontrados {len(results)} resultados para '{search_term}':\n\n"
        for result in results:
            output += f"Línea {result['line_number']}: {result['content']}\n"
        return output
    except Exception as e:
        return f"Error en búsqueda: {str(e)}"


@tool
def check_multiple_choice_answer(question_id: str, user_answer: str) -> str:
    """Verifica si la respuesta del usuario es correcta y la almacena"""
    return check_answer_func(question_id, user_answer)


@tool
def register_multiple_choice_question(question: str, options: list, correct_index: int) -> str:
    """Registra una pregunta con 4 opciones y el índice correcto (0-3)"""
    return register_mcq_func(question, options, correct_index)


tools = [
    read_text_file,
    search_in_text_file,
    check_multiple_choice_answer,
    register_multiple_choice_question,
]

if __name__ == "__main__":
    agent = create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        prompt="Eres un asistente que puede leer y buscar en archivos .txt, y crear preguntas de opción múltiple. Ayuda al usuario a procesar archivos de texto y crear evaluaciones."
    )

    print("=" * 60)
    print("EJEMPLO 1: Leer archivo .txt")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": "Lee el archivo SD-Com.txt y dame un resumen"}]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")

    print("=" * 60)
    print("EJEMPLO 2: Crear y registrar MCQ basado en el archivo")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                "Lee el archivo SD-Com.txt y crea una pregunta de opción múltiple basada en su contenido. "
                "Registra la pregunta con 4 opciones usando la herramienta y especifica cuál es correcta. "
                "Devuélveme el ID de la pregunta y la lista de opciones."
            )
        }]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")
    
    # Extraer el ID de la pregunta de la respuesta para el siguiente ejemplo
    response_text = result['messages'][-1].content
    if "ID:" in response_text:
        question_id = response_text.split("ID: ")[1].split("\n")[0]
        
        print("=" * 60)
        print("EJEMPLO 3: Verificar respuesta de opción múltiple")
        print("=" * 60)

        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Verifica mi respuesta para la pregunta {question_id}. Mi respuesta es 'A'"}]
        })
        print(f"\nRespuesta: {result['messages'][-1].content}\n")
