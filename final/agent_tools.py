from langchain_core.tools import tool, StructuredTool
from tools.tools import ToolSet

def create_agent_tools(toolset: ToolSet = None):
    # Use default toolset if none provided (backward compatibility)
    ts = toolset or ToolSet()
    
    # We define tools dynamically bound to the provided toolset instance
    
    @tool
    def read_text_file_tool(file_path: str) -> str:
        """Read complete file content"""
        return ts.read_text_file(file_path)

    @tool
    def search_in_text_file_tool(file_path: str, search_term: str, case_sensitive: bool = False) -> str:
        """Search for term in file"""
        return ts.search_in_text_file(file_path, search_term, case_sensitive)

    @tool
    def list_questions_tool(limit: int = 20) -> str:
        """List recent questions"""
        return ts.list_multiple_choice_questions(limit)

    @tool
    def get_performance_tool() -> str:
        """Get user performance stats"""
        return ts.get_user_performance()

    @tool
    def get_history_tool() -> str:
        """Get answer history"""
        return ts.get_answer_history_detailed()
        
    @tool
    def register_question_tool(question: str, options: list, correct_index: int) -> str:
        """Register a new multiple choice question"""
        return ts.register_multiple_choice_question(question, options, correct_index)

    return [
        read_text_file_tool,
        search_in_text_file_tool,
        list_questions_tool,
        get_performance_tool,
        get_history_tool,
        register_question_tool
    ]

# Default tools for backward compatibility
# We use a helper to unpack cleanly by name
_default_tools_list = create_agent_tools()
_tools_map = {t.name: t for t in _default_tools_list}

read_text_file_tool = _tools_map["read_text_file_tool"]
search_in_text_file_tool = _tools_map["search_in_text_file_tool"]
list_questions_tool = _tools_map["list_questions_tool"]
get_performance_tool = _tools_map["get_performance_tool"]
get_history_tool = _tools_map["get_history_tool"]
register_question_tool = _tools_map["register_question_tool"]
