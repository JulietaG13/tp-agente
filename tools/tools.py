from services.service import FileService


file_service = FileService()


def read_text_file(file_path: str) -> str:
    try:
        content = file_service.read_txt_file(file_path)
        return content
    except Exception as e:
        return f"Error al leer el archivo: {str(e)}"


def search_in_text_file(file_path: str, search_term: str,
                       case_sensitive: bool = False) -> str:
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

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "Lee el contenido completo de un archivo .txt",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Ruta completa al archivo .txt"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_text_file",
            "description": "Busca un término en un archivo .txt",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Ruta al archivo"
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Término a buscar"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Distinguir mayúsculas",
                        "default": False
                    }
                },
                "required": ["file_path", "search_term"]
            }
        }
    }
]

TOOLS_MAP = {
    "read_text_file": read_text_file,
    "search_in_text_file": search_in_text_file
}
