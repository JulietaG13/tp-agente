# Multi-Agent System Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                │
│                    "Dame una pregunta nueva"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  🎯 ORCHESTRATOR│
                    │    (Cyan)       │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │  Decision Making:        │
                │  - Check user score      │
                │  - Analyze request       │
                │  - Route to agents       │
                └────────────┬────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    [Score >= 3?]      [Direct]          [Show Stats]
          │                  │                  │
          ▼                  │                  ▼
  ┌───────────────┐         │           ┌─────────────┐
  │ 💡 FEEDBACK    │         │           │   DISPLAY   │
  │    AGENT       │         │           │ PERFORMANCE │
  │  (Magenta)     │         │           └─────────────┘
  └───────┬────────┘         │
          │                  │
  ┌───────┴────────┐         │
  │ Analyze:        │         │
  │ - Patterns      │         │
  │ - Weak areas    │         │
  │ - Suggestions   │         │
  └───────┬────────┘         │
          │                  │
          └──────────────────┤
                             ▼
                    ┌────────────────┐
                    │ ✨ QUESTION     │
                    │    CREATOR      │
                    │    (Green)      │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ Actions:         │
                    │ - Read SD-Com.txt│
                    │ - Check existing │
                    │ - Generate MCQ   │
                    │ - Format JSON    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ ⚖️  DIFFICULTY   │
                    │    REVIEWER     │
                    │    (Yellow)     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ Evaluate:        │
                    │ - User score     │
                    │ - Question level │
                    │ - Appropriateness│
                    └────────┬────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
     [APPROVED]                            [REJECTED]
          │                                     │
          ▼                                     │
  ┌───────────────┐                            │
  │   REGISTER    │                            │
  │   QUESTION    │                            │
  │   IN MEMORY   │                            │
  └───────┬───────┘                            │
          │                                     │
          ▼                                     │
  ┌───────────────┐                            │
  │   PRESENT     │                            │
  │   TO USER     │                            │
  │   📢 (White)  │                            │
  └───────┬───────┘                            │
          │                                     │
          ▼                                     │
  ┌───────────────┐                            │
  │ USER ANSWERS  │                            │
  │   👤 (Blue)   │                            │
  └───────┬───────┘                            │
          │                                     │
          ▼                                     │
  ┌───────────────┐                            │
  │   CHECK &     │                            │
  │   STORE       │                            │
  │   ANSWER      │                            │
  └───────┬───────┘                            │
          │                                     │
          ▼                                     │
  ┌───────────────┐                            │
  │  UPDATE SCORE │                            │
  │   IN MEMORY   │                            │
  └───────────────┘                            │
                                                │
          ┌─────────────────────────────────────┘
          │ [If iteration < 3]
          │ Loop back with feedback
          ▼
   ┌────────────────┐
   │ ✨ QUESTION     │
   │    CREATOR      │
   │ (with feedback) │
   └────────────────┘


═══════════════════════════════════════════════════════════════════════

KEY DECISION POINTS:

1. ORCHESTRATOR ROUTING:
   ├─ Has score data (≥3 answers)? → Consult Feedback Agent first
   ├─ Request is for stats? → Show performance directly
   └─ Otherwise → Create question directly

2. DIFFICULTY REVIEW:
   ├─ Score > 75%? → Demand challenging questions
   ├─ Score 50-75%? → Moderate difficulty OK
   ├─ Score < 50%? → Prefer easier questions
   └─ No history? → Accept moderate questions

3. ITERATION CONTROL:
   ├─ Approved? → Present to user
   ├─ Rejected & iteration < 3? → Loop back to Question Creator
   └─ Iteration ≥ 3? → Auto-approve (prevent infinite loops)

═══════════════════════════════════════════════════════════════════════

STATE FLOW:

AgentState {
  messages: [...],                    // Conversation history
  current_question: "...",            // Draft question text
  question_options: [...],            // 4 answer options
  question_correct_index: 0-3,        // Correct answer index
  difficulty_feedback: "...",         // Reviewer's feedback
  user_feedback: "...",              // Learning pattern insights
  score_data: {...},                 // Performance metrics
  iteration_count: 0,                // Loop counter
  question_approved: false,          // Review decision
  next_action: "..."                 // Router control
}

═══════════════════════════════════════════════════════════════════════

MEMORY STORAGE (MCQService):

_questions: {
  "uuid-1": {
    question: "...",
    options: [...],
    correct_answer: "...",
    created_at: datetime
  },
  ...
}

_answers: {
  "uuid-1": {
    user_answer: "...",
    is_correct: true/false,
    answered_at: datetime
  },
  ...
}

═══════════════════════════════════════════════════════════════════════

AGENT CAPABILITIES:

🎯 ORCHESTRATOR:
   Tools: get_performance_tool
   Role: Coordination, routing, final presentation
   Model: gpt-4o-mini

✨ QUESTION CREATOR:
   Tools: read_text_file_tool, search_in_text_file_tool, list_questions_tool
   Role: Generate original MCQs from content
   Model: gpt-4o-mini
   Output: JSON with question, options, correct_index

⚖️ DIFFICULTY REVIEWER:
   Tools: get_performance_tool
   Role: Validate question appropriateness
   Model: gpt-4o-mini
   Output: JSON with approved (bool) and feedback (string)

💡 FEEDBACK AGENT:
   Tools: get_performance_tool, get_history_tool
   Role: Analyze patterns, identify weak areas
   Model: gpt-4o-mini
   Output: Insights and recommendations

═══════════════════════════════════════════════════════════════════════
```

## Color Legend

When running the system, you'll see:

- 🎯 **Cyan** - Orchestrator making decisions and coordinating
- ✨ **Green** - Question Creator generating MCQs
- ⚖️ **Yellow** - Difficulty Reviewer analyzing appropriateness
- 💡 **Magenta** - Feedback Agent providing insights
- 👤 **Blue** - User input
- 📢 **White/Bright** - System output to user
- **Gray** - Separator lines

## Example Session Flow

```
════════════════════════════════════════════════════════════════════════
🚀 SISTEMA MULTI-AGENTE DE GENERACIÓN DE PREGUNTAS
════════════════════════════════════════════════════════════════════════

👤 Tu mensaje: dame una pregunta

════════════════════════════════════════════════════════════════════════
🎯 [ORCHESTRATOR] Procesando solicitud del usuario...
🎯 [ORCHESTRATOR] Score actual: 0.0% (0/0)
🎯 [ORCHESTRATOR] Historial insuficiente, procediendo directamente a crear pregunta
🎯 [ORCHESTRATOR] Routing: create_question

✨ [QUESTION CREATOR] Iniciando creación de pregunta...
✨ [QUESTION CREATOR] Respuesta recibida: {...
✨ [QUESTION CREATOR] Pregunta creada: ¿Qué es el modelo OSI?

⚖️ [DIFFICULTY REVIEWER] Revisando dificultad de la pregunta propuesta...
⚖️ [DIFFICULTY REVIEWER] Análisis recibido: {...
⚖️ [DIFFICULTY REVIEWER] Decisión: ✓ APROBADA
⚖️ [DIFFICULTY REVIEWER] Feedback: Pregunta apropiada para comenzar...

🎯 [ORCHESTRATOR] Pregunta aprobada, registrando y presentando al usuario...

════════════════════════════════════════════════════════════════════════
📢 [SYSTEM → USER]

Pregunta registrada con ID: abc123...

Pregunta: ¿Qué es el modelo OSI?

Opciones:
A) Un protocolo de red
B) Un modelo de 7 capas para comunicación
C) Un tipo de cable
D) Un sistema operativo
════════════════════════════════════════════════════════════════════════

👤 Tu mensaje: B

════════════════════════════════════════════════════════════════════════
📢 [SYSTEM → USER]

Respuesta registrada para pregunta abc123...

Tu respuesta: Un modelo de 7 capas para comunicación
Respuesta correcta: Un modelo de 7 capas para comunicación
Resultado: ✓ CORRECTO
════════════════════════════════════════════════════════════════════════
```

