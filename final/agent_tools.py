from langchain_core.tools import tool
from tools.tools import (
    read_text_file,
    search_in_text_file,
    list_multiple_choice_questions,
    get_user_performance,
    get_answer_history_detailed
)


@tool
def read_text_file_tool(file_path: str) -> str:
    """Read complete file content"""
    return read_text_file(file_path)


@tool
def search_in_text_file_tool(file_path: str, search_term: str, case_sensitive: bool = False) -> str:
    """Search for term in file"""
    return search_in_text_file(file_path, search_term, case_sensitive)


@tool
def list_questions_tool(limit: int = 20) -> str:
    """List recent questions"""
    return list_multiple_choice_questions(limit)


@tool
def get_performance_tool() -> str:
    """Get user performance stats"""
    return get_user_performance()


@tool
def get_history_tool() -> str:
    """Get answer history"""
    return get_answer_history_detailed()
