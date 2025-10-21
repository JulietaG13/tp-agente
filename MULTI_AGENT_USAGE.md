# Multi-Agent Question Generation System - Usage Guide

## Overview

This multi-agent system uses 4 specialized AI agents to create adaptive multiple-choice questions:

- **🎯 Orchestrator** (Cyan): Coordinates all agents and manages the workflow
- **✨ Question Creator** (Green): Creates original MCQs from SD-Com.txt
- **⚖️ Difficulty Reviewer** (Yellow): Ensures questions match user's skill level
- **💡 Feedback Agent** (Magenta): Analyzes learning patterns and provides insights

## Installation

Make sure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

## Running the System

### Option 1: Multi-Agent System (NEW)

```bash
python multi_agent.py
```

This runs the advanced multi-agent orchestrator with adaptive difficulty.

### Option 2: Original Simple Agent

```bash
python agent.py
```

This runs the original single-agent system (examples hardcoded).

## How It Works

### Question Generation Flow

1. **User requests a question** → Orchestrator receives request
2. **Orchestrator decides** → Checks if Feedback Agent should be consulted (if >3 answers exist)
3. **Feedback Agent analyzes** (optional) → Reviews user's patterns and weak areas
4. **Question Creator generates** → Creates a new MCQ based on SD-Com.txt
5. **Difficulty Reviewer evaluates** → Checks if difficulty matches user's score
   - If approved → Question is presented
   - If rejected → Loop back to Question Creator with feedback
6. **User answers** → System records and updates score

### Non-Linear Orchestration

The Orchestrator is **intelligent and adaptive**:
- Only consults Feedback Agent when there's sufficient history (>3 answers)
- May loop between Question Creator and Difficulty Reviewer multiple times
- Makes decisions based on context, not fixed sequences

### Difficulty Adaptation

The Difficulty Reviewer adjusts based on user performance:
- **>75% correct** → Expects more challenging questions
- **50-75% correct** → Moderate difficulty
- **<50% correct** → Easier, more accessible questions

## Usage Examples

### Request a New Question

```
👤 Tu mensaje: dame una pregunta nueva
```

The system will:
1. Check your score
2. Optionally consult Feedback Agent
3. Generate a question
4. Review difficulty
5. Present the approved question

### Answer a Question

```
👤 Tu mensaje: B
```

Or:

```
👤 Tu mensaje: La opción que describe...
```

### Check Your Performance

```
👤 Tu mensaje: muestra mi rendimiento
```

### Exit

```
👤 Tu mensaje: salir
```

## Logging

All agent actions are logged with **colored output** for clarity:

- 🎯 **Cyan** → Orchestrator decisions
- ✨ **Green** → Question Creator actions
- ⚖️ **Yellow** → Difficulty Reviewer analysis
- 💡 **Magenta** → Feedback Agent insights
- 👤 **Blue** → User input
- 📢 **White/Bright** → System output to user

## Architecture Highlights

### State Management

The system uses a shared `AgentState` that includes:
- Message history
- Current question being drafted
- Difficulty feedback
- User learning patterns
- Score data
- Iteration counters

### Memory & Persistence

- **Session-based**: Agents remember everything during a session
- **MCQService**: Single source of truth for questions and answers
- **Score computation**: Dynamically calculated from stored answers

### Tools Available

**Question Creator** has access to:
- `read_text_file_tool` - Read SD-Com.txt
- `search_in_text_file_tool` - Search for specific content
- `list_questions_tool` - Check existing questions to avoid repetition

**Difficulty Reviewer** has access to:
- `get_performance_tool` - Get current user score and statistics

**Feedback Agent** has access to:
- `get_performance_tool` - Get score summary
- `get_history_tool` - Get detailed answer history

**Orchestrator** has access to:
- `get_performance_tool` - Make routing decisions based on score

## Key Features

✅ **Adaptive Difficulty** - Questions automatically adjust to user level  
✅ **Pattern Recognition** - Identifies user's weak areas  
✅ **Non-Linear Flow** - Orchestrator makes intelligent decisions  
✅ **Avoids Repetition** - Checks existing questions before creating new ones  
✅ **Transparent Logging** - See exactly what each agent is doing  
✅ **Quality Control** - Multiple review loops ensure appropriate questions  

## Comparison: multi_agent.py vs agent.py

| Feature | agent.py | multi_agent.py |
|---------|----------|----------------|
| Agents | Single agent | 4 specialized agents |
| Difficulty adaptation | No | Yes |
| Pattern analysis | No | Yes |
| Workflow | Fixed examples | Interactive loop |
| Quality review | No | Multi-stage review |
| Logging | Basic | Colored, detailed |
| Orchestration | N/A | Intelligent, non-linear |

## Environment Variables

Make sure you have a `.env` file with:

```
OPENAI_API_KEY=your_key_here
```

The system uses `gpt-4o-mini` by default for all agents.

## Troubleshooting

### No questions appearing
- Make sure `SD-Com.txt` exists in the project root
- Check that the OpenAI API key is set correctly

### Agents not working
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that colorama is installed for colored output

### Question keeps getting rejected
- The system has a safety limit of 3 iterations before auto-approving
- This prevents infinite loops while maintaining quality

