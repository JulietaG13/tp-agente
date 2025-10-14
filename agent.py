from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv
load_dotenv()

# tools de ejemplo
@tool
def calculator(operation: str) -> str:
    try:
        # Evaluar la operación matemática de forma segura
        result = eval(operation, {"__builtins__": {}}, {})
        return f"El resultado de {operation} es: {result}"
    except Exception as e:
        return f"Error al calcular: {str(e)}"


@tool
def string_length(text: str) -> str:
    length = len(text)
    return f"El texto '{text}' tiene {length} caracteres"


tools = [calculator, string_length]

if __name__ == "__main__":
    agent = create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        prompt="Eres un asistente útil que puede realizar cálculos y contar caracteres."
    )

    # Ejemplos
    print("=" * 60)
    print("EJEMPLO 1: Calculadora")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": "¿Cuánto es 25 * 4 + 10?"}]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")

    print("=" * 60)
    print("EJEMPLO 2: Longitud de texto")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": "¿Cuántos caracteres tiene la palabra 'LangGraph'?"}]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")

    print("=" * 60)
    print("EJEMPLO 3: Múltiples tools")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": "Calcula 15 * 3 y luego cuenta cuántos caracteres tiene el resultado"}]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")
