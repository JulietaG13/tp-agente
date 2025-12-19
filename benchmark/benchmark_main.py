import argparse
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.core.simulated_student import SimulatedStudent, ExpertPersona, NovicePersona, LearnerPersona
from benchmark.core.runner import BenchmarkRunner
from benchmark.reporting.data_serializer import BenchmarkDataSerializer
from final.rag.labeler_agent import ChunkSubtopicLabeler
from final.rag.session_context import RagContext, set_rag_context, default_persist_directory


def _chunk_words(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _select_samples(chunks: list[str], max_samples: int = 7) -> list[str]:
    if not chunks:
        return []
    if len(chunks) <= max_samples:
        return list(chunks)

    picks: list[str] = [chunks[0]]
    if len(chunks) > 2:
        picks.append(chunks[1])
    mid = len(chunks) // 2
    picks.append(chunks[mid])
    if mid + 1 < len(chunks):
        picks.append(chunks[mid + 1])
    if len(chunks) > 3:
        picks.append(chunks[-2])
    picks.append(chunks[-1])
    return picks[:max_samples]


def _extract_benchmark_subtopics(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()
    chunks = _chunk_words(raw, chunk_size=400, overlap=50)
    samples = _select_samples(chunks, max_samples=7)
    return ChunkSubtopicLabeler().extract_taxonomy(samples=samples, max_subtopics=30)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Adaptive AI Benchmarking")
    parser.add_argument("--persona", type=str, choices=["expert", "novice", "learner"], required=True, 
                       help="Simulated student persona")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--sleep", type=float, default=0, 
                       help="Sleep duration between turns in seconds (default: 0)")
    return parser.parse_args()


def create_benchmark_output_directory():
    """Create timestamped directory for benchmark output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(benchmark_dir, "reports", f"benchmark_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def save_benchmark_data(raw_data: dict, output_dir: str) -> str:
    """Save raw benchmark data to JSON file."""
    serializer = BenchmarkDataSerializer()
    data_path = os.path.join(output_dir, "data.json")
    serializer.save_to_file(raw_data, data_path)
    
    return data_path


def create_persona_from_name(persona_name):
    persona_map = {
        "expert": ExpertPersona,
        "novice": NovicePersona,
        "learner": LearnerPersona
    }
    return persona_map[persona_name]()


def execute_benchmark(persona, turns, sleep_duration) -> dict:
    student = SimulatedStudent(persona)
    runner = BenchmarkRunner(student, turns=turns, sleep_duration=sleep_duration)
    return runner.run()


def main():
    args = parse_arguments()

    output_dir = create_benchmark_output_directory()

    benchmark_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ["CONTENT_PATH"] = os.path.join(benchmark_dir, "content", "SD-Com.txt")
    os.environ["USE_RAG"] = os.environ.get("USE_RAG", "true")
    os.environ["USE_OPEN_ENDED_QUESTIONS"] = os.environ.get("USE_OPEN_ENDED_QUESTIONS", "true")

    content_path = os.environ["CONTENT_PATH"]
    collection_name = os.environ.get("BENCHMARK_COLLECTION_NAME", "course_content")
    persist_directory = os.environ.get("CHROMA_PERSIST_DIRECTORY", default_persist_directory())
    if not os.path.isabs(persist_directory):
        repo_root = os.path.dirname(benchmark_dir)
        persist_directory = os.path.abspath(os.path.join(repo_root, persist_directory))

    subtopics = _extract_benchmark_subtopics(content_path)
    set_rag_context(
        RagContext(
            persist_directory=persist_directory,
            collection_name=collection_name,
            subtopics=tuple(subtopics),
        )
    )
    
    print(f"Initializing benchmark for {args.persona} with {args.turns} turns...")
    
    persona = create_persona_from_name(args.persona)
    raw_data = execute_benchmark(persona, args.turns, args.sleep)

    data_path = save_benchmark_data(raw_data, output_dir)
    print(f"\nBenchmark data saved to {data_path}")

    metadata = raw_data.get('metadata', {})
    if 'average_generation_time_seconds' in metadata:
        print("\n=== Timing Statistics ===")
        print(f"Average generation time: {metadata['average_generation_time_seconds']}s")
        print(f"Min generation time: {metadata['min_generation_time_seconds']}s")
        print(f"Max generation time: {metadata['max_generation_time_seconds']}s")
        print(f"Total generation time: {metadata['total_generation_time_seconds']}s")

    print(f"\nTo generate report, run: python generate_report.py {data_path}")

if __name__ == "__main__":
    main()

