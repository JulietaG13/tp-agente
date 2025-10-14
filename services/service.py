import os
from typing import List, Dict, Optional


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