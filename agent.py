from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from services.service import FileService

load_dotenv()

file_service = FileService()


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


tools = [read_text_file, search_in_text_file]

if __name__ == "__main__":
    agent = create_react_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        prompt="Eres un asistente que puede leer y buscar en archivos .txt. Ayuda al usuario a procesar archivos de texto."
    )

    print("=" * 60)
    print("EJEMPLO: Leer archivo .txt")
    print("=" * 60)

    result = agent.invoke({
        "messages": [{"role": "user", "content": "Lee el archivo SD-Com.txt y dame un resumen"}]
    })
    print(f"\nRespuesta: {result['messages'][-1].content}\n")
