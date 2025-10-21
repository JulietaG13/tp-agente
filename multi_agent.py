from typing import TypedDict, Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
import json

from services.service import FileService, MCQService
from tools.tools import (
    read_text_file,
    search_in_text_file,
    list_multiple_choice_questions,
    register_multiple_choice_question,
    check_last_multiple_choice_answer,
    get_user_performance,
    get_answer_history_detailed
)

load_dotenv()
colorama_init(autoreset=True)

file_service = FileService()
mcq_service = MCQService()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_question: str
    question_options: list
    question_correct_index: int
    difficulty_feedback: str
    user_feedback: str
    score_data: dict
    iteration_count: int
    question_approved: bool
    next_action: str


def log_orchestrator(message: str):
    print(f"{Fore.CYAN}🎯 [ORCHESTRATOR]{Style.RESET_ALL} {message}")


def log_question_creator(message: str):
    print(f"{Fore.GREEN}✨ [QUESTION CREATOR]{Style.RESET_ALL} {message}")


def log_difficulty_reviewer(message: str):
    print(f"{Fore.YELLOW}⚖️  [DIFFICULTY REVIEWER]{Style.RESET_ALL} {message}")


def log_feedback_agent(message: str):
    print(f"{Fore.MAGENTA}💡 [FEEDBACK AGENT]{Style.RESET_ALL} {message}")


def log_user_input(message: str):
    print(f"{Fore.BLUE}👤 [USER INPUT]{Style.RESET_ALL} {message}")


def log_user_output(message: str):
    print(f"{Fore.WHITE}{Style.BRIGHT}📢 [SYSTEM → USER]{Style.RESET_ALL} {message}")


def log_separator():
    print(f"{Fore.LIGHTBLACK_EX}{'=' * 80}{Style.RESET_ALL}")


@tool
def read_text_file_tool(file_path: str) -> str:
    """Lee el contenido completo de un archivo .txt"""
    return read_text_file(file_path)


@tool
def search_in_text_file_tool(file_path: str, search_term: str, case_sensitive: bool = False) -> str:
    """Busca un término en un archivo .txt"""
    return search_in_text_file(file_path, search_term, case_sensitive)


@tool
def list_questions_tool(limit: int = 20) -> str:
    """Lista las últimas preguntas registradas"""
    return list_multiple_choice_questions(limit)


@tool
def get_performance_tool() -> str:
    """Obtiene el rendimiento y puntaje actual del usuario"""
    return get_user_performance()


@tool
def get_history_tool() -> str:
    """Obtiene el historial detallado de respuestas"""
    return get_answer_history_detailed()


def create_question_creator_agent():
    """Crea el agente generador de preguntas"""
    tools = [read_text_file_tool, search_in_text_file_tool, list_questions_tool]
    
    prompt = """Eres un experto creador de preguntas de opción múltiple. Tu trabajo es:

1. Leer el archivo SD-Com.txt y comprender su contenido
2. Revisar las preguntas existentes para evitar repeticiones
3. Crear una pregunta original e interesante basada en el contenido
4. Proporcionar exactamente 4 opciones de respuesta (una correcta y tres incorrectas plausibles)

IMPORTANTE:
- NO registres la pregunta todavía, solo devuélvela en formato JSON
- Asegúrate de que las opciones incorrectas sean realistas pero claramente distintas de la correcta
- La pregunta debe ser clara y específica
- Devuelve tu respuesta en este formato JSON exacto:
{
    "question": "texto de la pregunta",
    "options": ["opción A", "opción B", "opción C", "opción D"],
    "correct_index": 0
}

Donde correct_index es 0-3 indicando cuál opción es la correcta."""
    
    return create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        state_modifier=prompt
    )


def create_difficulty_reviewer_agent():
    """Crea el agente revisor de dificultad"""
    tools = [get_performance_tool]
    
    prompt = """Eres un experto revisor de dificultad de preguntas. Tu trabajo es:

1. Revisar el rendimiento actual del usuario
2. Analizar la pregunta propuesta
3. Determinar si la dificultad es apropiada según el puntaje del usuario

CRITERIOS:
- Si el usuario tiene >75% de aciertos: la pregunta debe ser desafiante
- Si el usuario tiene 50-75% de aciertos: la pregunta debe ser de dificultad moderada
- Si el usuario tiene <50% de aciertos: la pregunta debe ser más accesible
- Si no hay historial: acepta preguntas de dificultad moderada

NO SEAS DEMASIADO EXIGENTE, pero tampoco demasiado permisivo. El objetivo es mantener al usuario comprometido.

Devuelve tu respuesta en este formato JSON exacto:
{
    "approved": true/false,
    "feedback": "explicación detallada de por qué apruebas o rechazas la pregunta y qué ajustes sugieres"
}"""
    
    return create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        state_modifier=prompt
    )


def create_feedback_agent():
    """Crea el agente de retroalimentación"""
    tools = [get_performance_tool, get_history_tool]
    
    prompt = """Eres un experto en análisis de patrones de aprendizaje. Tu trabajo es:

1. Analizar el historial de respuestas del usuario
2. Identificar patrones, fortalezas y debilidades
3. Proporcionar recomendaciones sobre qué temas reforzar

Devuelve insights útiles sobre:
- Áreas donde el usuario está teniendo dificultades
- Patrones en los errores
- Sugerencias para enfocar futuras preguntas
- Aspectos pedagógicos a considerar

Sé constructivo y específico."""
    
    return create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        state_modifier=prompt
    )


def create_orchestrator_agent():
    """Crea el agente orquestador"""
    tools = [get_performance_tool]
    
    prompt = """Eres el orquestador principal del sistema de generación de preguntas. Tu trabajo es:

1. Recibir solicitudes del usuario
2. Coordinar a los agentes especializados según sea necesario
3. Decidir cuándo consultar a cada agente
4. Presentar resultados finales al usuario

RESPONSABILIDADES:
- Usa tu juicio para decidir qué agentes consultar (no siempre necesitas todos)
- Si el usuario pide una pregunta, coordina Question Creator y Difficulty Reviewer
- Solo consulta al Feedback Agent si hay suficiente historial (>3 respuestas)
- Sé eficiente: no hagas trabajo innecesario
- Comunícate claramente con el usuario

IMPORTANTE: Tú coordinas pero NO creas preguntas directamente. Delega en los agentes especializados."""
    
    return create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        state_modifier=prompt
    )


def question_creator_node(state: AgentState):
    """Nodo que ejecuta el agente creador de preguntas"""
    log_question_creator("Iniciando creación de pregunta...")
    
    agent = create_question_creator_agent()
    
    context = ""
    if state.get("difficulty_feedback"):
        context = f"\n\nFeedback del revisor de dificultad: {state['difficulty_feedback']}"
    
    if state.get("user_feedback"):
        context += f"\n\nFeedback sobre el usuario: {state['user_feedback']}"
    
    message = f"Crea una nueva pregunta de opción múltiple basada en SD-Com.txt.{context}"
    
    result = agent.invoke({"messages": [HumanMessage(content=message)]})
    response_content = result["messages"][-1].content
    
    log_question_creator(f"Respuesta recibida: {response_content[:200]}...")
    
    try:
        if "```json" in response_content:
            json_start = response_content.find("```json") + 7
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        elif "```" in response_content:
            json_start = response_content.find("```") + 3
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        else:
            start_idx = response_content.find("{")
            end_idx = response_content.rfind("}") + 1
            json_str = response_content[start_idx:end_idx]
        
        question_data = json.loads(json_str)
        
        log_question_creator(f"Pregunta creada: {question_data['question']}")
        
        return {
            "current_question": question_data["question"],
            "question_options": question_data["options"],
            "question_correct_index": question_data["correct_index"],
            "messages": [AIMessage(content=f"Pregunta propuesta: {question_data['question']}")],
            "next_action": "review_difficulty"
        }
    except Exception as e:
        log_question_creator(f"Error al parsear JSON: {str(e)}")
        return {
            "messages": [AIMessage(content=f"Error al crear pregunta: {str(e)}")],
            "next_action": "create_question"
        }


def difficulty_reviewer_node(state: AgentState):
    """Nodo que ejecuta el agente revisor de dificultad"""
    log_difficulty_reviewer("Revisando dificultad de la pregunta propuesta...")
    
    agent = create_difficulty_reviewer_agent()
    
    question_info = f"""
Pregunta propuesta: {state['current_question']}

Opciones:
A) {state['question_options'][0]}
B) {state['question_options'][1]}
C) {state['question_options'][2]}
D) {state['question_options'][3]}

Respuesta correcta: {chr(65 + state['question_correct_index'])}
"""
    
    message = f"Revisa la siguiente pregunta y determina si la dificultad es apropiada:\n\n{question_info}"
    
    result = agent.invoke({"messages": [HumanMessage(content=message)]})
    response_content = result["messages"][-1].content
    
    log_difficulty_reviewer(f"Análisis recibido: {response_content[:200]}...")
    
    try:
        if "```json" in response_content:
            json_start = response_content.find("```json") + 7
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        elif "```" in response_content:
            json_start = response_content.find("```") + 3
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        else:
            start_idx = response_content.find("{")
            end_idx = response_content.rfind("}") + 1
            json_str = response_content[start_idx:end_idx]
        
        review_data = json.loads(json_str)
        approved = review_data.get("approved", False)
        feedback = review_data.get("feedback", "")
        
        log_difficulty_reviewer(f"Decisión: {'✓ APROBADA' if approved else '✗ RECHAZADA'}")
        log_difficulty_reviewer(f"Feedback: {feedback}")
        
        if approved:
            return {
                "question_approved": True,
                "difficulty_feedback": feedback,
                "messages": [AIMessage(content=f"Pregunta aprobada: {feedback}")],
                "next_action": "present_question"
            }
        else:
            iteration = state.get("iteration_count", 0) + 1
            if iteration >= 3:
                log_difficulty_reviewer("Máximo de iteraciones alcanzado, aprobando pregunta...")
                return {
                    "question_approved": True,
                    "difficulty_feedback": "Aprobada tras múltiples iteraciones",
                    "messages": [AIMessage(content="Pregunta aprobada tras revisión")],
                    "next_action": "present_question"
                }
            else:
                return {
                    "question_approved": False,
                    "difficulty_feedback": feedback,
                    "iteration_count": iteration,
                    "messages": [AIMessage(content=f"Pregunta rechazada: {feedback}")],
                    "next_action": "create_question"
                }
    except Exception as e:
        log_difficulty_reviewer(f"Error al parsear respuesta, aprobando por defecto: {str(e)}")
        return {
            "question_approved": True,
            "difficulty_feedback": "Aprobada por defecto",
            "messages": [AIMessage(content="Pregunta aprobada")],
            "next_action": "present_question"
        }


def feedback_agent_node(state: AgentState):
    """Nodo que ejecuta el agente de retroalimentación"""
    log_feedback_agent("Analizando patrones de aprendizaje del usuario...")
    
    score_data = mcq_service.compute_user_score()
    
    if score_data['total_questions'] < 3:
        log_feedback_agent("Historial insuficiente, omitiendo análisis detallado")
        return {
            "user_feedback": "Usuario nuevo, sin suficiente historial para análisis",
            "messages": [AIMessage(content="Historial insuficiente para análisis")],
            "next_action": "create_question"
        }
    
    agent = create_feedback_agent()
    
    message = "Analiza el rendimiento del usuario e identifica patrones, fortalezas y áreas de mejora."
    
    result = agent.invoke({"messages": [HumanMessage(content=message)]})
    response_content = result["messages"][-1].content
    
    log_feedback_agent(f"Análisis: {response_content[:200]}...")
    
    return {
        "user_feedback": response_content,
        "messages": [AIMessage(content=response_content)],
        "next_action": "create_question"
    }


def orchestrator_node(state: AgentState):
    """Nodo orquestador principal"""
    log_orchestrator("Procesando solicitud del usuario...")
    
    last_message = state["messages"][-1]
    user_request = last_message.content.lower()
    
    score_data = mcq_service.compute_user_score()
    log_orchestrator(f"Score actual: {score_data['score_percentage']:.1f}% ({score_data['correct_count']}/{score_data['total_questions']})")
    
    if "pregunta" in user_request or "question" in user_request or "nueva" in user_request:
        log_orchestrator("Solicitud de nueva pregunta detectada")
        
        if score_data['total_questions'] >= 3:
            log_orchestrator("Historial suficiente, consultando Feedback Agent primero")
            return {"next_action": "get_feedback"}
        else:
            log_orchestrator("Historial insuficiente, procediendo directamente a crear pregunta")
            return {"next_action": "create_question"}
    
    elif "rendimiento" in user_request or "puntaje" in user_request or "score" in user_request:
        log_orchestrator("Solicitud de rendimiento detectada")
        performance = get_user_performance()
        log_user_output(performance)
        return {"next_action": "end", "messages": [AIMessage(content=performance)]}
    
    else:
        log_orchestrator("Solicitud general, creando pregunta")
        return {"next_action": "create_question"}


def route_orchestrator(state: AgentState) -> Literal["get_feedback", "create_question", "end"]:
    """Decide la siguiente acción desde el orquestador"""
    next_action = state.get("next_action", "create_question")
    log_orchestrator(f"Routing: {next_action}")
    return next_action


def route_after_feedback(state: AgentState) -> Literal["create_question"]:
    """Después del feedback, siempre va a crear pregunta"""
    return "create_question"


def route_after_question_creation(state: AgentState) -> Literal["review_difficulty"]:
    """Después de crear pregunta, siempre va a revisión"""
    return "review_difficulty"


def route_after_difficulty_review(state: AgentState) -> Literal["create_question", "present_question"]:
    """Decide si aprobar o iterar"""
    if state.get("question_approved", False):
        return "present_question"
    else:
        log_difficulty_reviewer("Pregunta rechazada, volviendo a Question Creator")
        return "create_question"


def present_question_node(state: AgentState):
    """Presenta la pregunta aprobada al usuario"""
    log_orchestrator("Pregunta aprobada, registrando y presentando al usuario...")
    
    question_id = register_multiple_choice_question(
        state["current_question"],
        state["question_options"],
        state["question_correct_index"]
    )
    
    log_separator()
    log_user_output("\n" + question_id)
    log_separator()
    
    return {
        "messages": [AIMessage(content=f"Pregunta presentada: {question_id}")],
        "next_action": "end"
    }


def build_workflow():
    """Construye el grafo de flujo de trabajo"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("get_feedback", feedback_agent_node)
    workflow.add_node("create_question", question_creator_node)
    workflow.add_node("review_difficulty", difficulty_reviewer_node)
    workflow.add_node("present_question", present_question_node)
    
    workflow.add_edge(START, "orchestrator")
    
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
            "create_question": "create_question",
            "present_question": "present_question"
        }
    )
    
    workflow.add_edge("present_question", END)
    
    return workflow.compile()


def main():
    """Bucle principal de ejecución"""
    log_separator()
    print(f"{Fore.CYAN}{Style.BRIGHT}🚀 SISTEMA MULTI-AGENTE DE GENERACIÓN DE PREGUNTAS{Style.RESET_ALL}")
    log_separator()
    
    app = build_workflow()
    
    print("\nComandos disponibles:")
    print("  - 'pregunta' / 'nueva pregunta': Genera una nueva pregunta")
    print("  - 'rendimiento' / 'puntaje': Muestra tu rendimiento actual")
    print("  - 'salir' / 'exit': Termina el programa")
    print()
    
    while True:
        log_separator()
        user_input = input(f"{Fore.BLUE}👤 Tu mensaje: {Style.RESET_ALL}").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['salir', 'exit', 'quit']:
            log_user_output("¡Hasta luego!")
            break
        
        log_user_input(user_input)
        log_separator()
        
        if user_input.lower().startswith(('a)', 'b)', 'c)', 'd)')) or \
           (len(user_input) == 1 and user_input.upper() in 'ABCD'):
            result_msg = check_last_multiple_choice_answer(user_input)
            log_user_output("\n" + result_msg)
            continue
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "current_question": "",
            "question_options": [],
            "question_correct_index": 0,
            "difficulty_feedback": "",
            "user_feedback": "",
            "score_data": {},
            "iteration_count": 0,
            "question_approved": False,
            "next_action": ""
        }
        
        try:
            result = app.invoke(initial_state)
        except Exception as e:
            log_user_output(f"Error en el sistema: {str(e)}")
            continue


if __name__ == "__main__":
    main()

