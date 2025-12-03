from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from final.agent_tools import create_agent_tools, read_text_file_tool, search_in_text_file_tool, list_questions_tool, get_performance_tool, get_history_tool

def create_claude_model():
    return ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0.7,
        max_tokens=2048,
        timeout=None,
        max_retries=2
    )

def create_question_creator_agent(tools=None):
    if tools is None:
        # Default tools
        tools = [read_text_file_tool, search_in_text_file_tool, list_questions_tool]
    
    llm = create_claude_model()
    return create_agent(llm, tools)

def create_difficulty_reviewer_agent(tools=None):
    if tools is None:
        tools = [get_performance_tool]
        
    llm = create_claude_model()
    return create_agent(llm, tools)

def create_feedback_agent(tools=None):
    if tools is None:
        tools = [get_performance_tool, get_history_tool]
        
    llm = create_claude_model()
    return create_agent(llm, tools)

def create_orchestrator_agent(tools=None):
    if tools is None:
        tools = [get_performance_tool]
        
    llm = create_claude_model()
    return create_agent(llm, tools)
