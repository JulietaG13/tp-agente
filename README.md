# Adaptive Learning Agent

This project implements an intelligent multi-agent system designed to deliver adaptive educational content. It uses a graph-based agent architecture (LangGraph) to generate questions, evaluate student answers, and adapt the difficulty level based on performance, simulating a personalized tutoring experience.

## Success criteria

We consider the system “working” when, across a session:

- **Adaptivity**: question difficulty tracks the student profile (novice is not overwhelmed; expert isn’t bored).
- **Coverage**: the agent explores the syllabus instead of looping on the same few subtopics.
- **Recovery**: after mistakes, the agent reacts (difficulty and feedback) and the student recovers on later encounters.

## Agents

At runtime we run a small graph of specialized agents (implemented as LangGraph nodes):

- **Orchestrator**: decides what to do next (ask for feedback, generate a new question, or end the turn).
- **Question creator**: generates the next question (MCQ or open) based on the session state and (optionally) retrieved context.
- **Difficulty reviewer**: sanity-checks the generated question and nudges difficulty up/down to keep the session on target.
- **Feedback agent**: provides corrective feedback and short remediation after the student answers.
- **Presenter**: formats/commits the final question payload back to the UI.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `env.example` to `.env` and fill in the values. At minimum, set one of the following API keys:

**Option A: OpenAI (Recommended)**
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**Option B: Groq**
```bash
GROQ_API_KEY=your_groq_api_key_here
```

**Option C: Anthropic**
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

The system will use OpenAI if available, otherwise fall back to Anthropic, then Groq. If none are set, the application will exit with an error.

### 3. Run the Application

**Web Interface (Recommended):**
```bash
chainlit run app.py -w
```

**CLI Mode:**
```bash
python final_agent.py
```


## RAG - Quick Start

```bash
# 1. Index content into ChromaDB (required for RAG)
python scripts/index_content.py --force

# 2. Run the system
python final_agent.py
```

To enable/disable RAG, set `USE_RAG=true/false` in `.env`



## Benchmarking

The project includes a robust benchmarking suite designed to rigorously evaluate the system's pedagogical capabilities. The goal is to ensure the agent correctly adapts to different student levels and adequately covers the provided curriculum.

### How It Works

The benchmark simulates a learning session by replacing the human user with a **Simulated Student Persona**. This persona is an LLM configured with specific cognitive traits and knowledge levels. The system and the persona interact in a loop:

1.  **System** generates a question based on current difficulty and history.
2.  **Persona** answers the question based on its profile.
3.  **System** evaluates the answer and adjusts difficulty.
4.  **Benchmark** records all interactions, metrics, and syllabus coverage.

### Personas

We test against two distinct profiles to validate adaptivity:
*   **Novice**: Makes frequent mistakes, especially on complex topics. Tests if the system lowers difficulty and offers remediation.
*   **Expert**: Consistently answers correctly. Tests if the system raises difficulty to challenge the user.

### Key Metrics
The report evaluates the system on:
*   **Effective Curriculum Coverage (ECC)**: Measures the system's effectiveness in guiding the student to master the full syllabus, rewarding broad topic coverage over repetition.
*   **Remediation Efficiency**: How well the system recovers after a student makes a mistake.
*   **Difficulty-Weighted Proficiency**: Evaluates if the system maintains the student in the "optimal learning zone" (neither bored nor overwhelmed).
*   **Error Sensitivity**: Whether the system reacts appropriately (drops difficulty) when errors occur.

These metrics are weighted and aggregated into a **Final Score** to provide a single, overall quality assessment of the adaptive session.

Metric definitions and scoring details live in [docs/benchmarking-metrics.md](docs/benchmarking-metrics.md).

## See more

- Benchmark report (RAG): [benchmark/reports/benchmark_20251218_194832-rag/report.md](benchmark/reports/benchmark_20251218_194832-rag/report.md)
- Benchmark report (no RAG): [benchmark/reports/benchmark_20251218_195552-no_rag/report.md](benchmark/reports/benchmark_20251218_195552-no_rag/report.md)
