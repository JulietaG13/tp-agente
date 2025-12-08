import argparse
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.simulated_student import SimulatedStudent, ExpertPersona, NovicePersona, LearnerPersona
from benchmark.runner import BenchmarkRunner


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Adaptive AI Benchmarking")
    parser.add_argument("--persona", type=str, choices=["expert", "novice", "learner"], required=True, 
                       help="Simulated student persona")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--output", type=str, default=None, 
                       help="Output report file (default: reports/benchmark_report_<timestamp>.md)")
    parser.add_argument("--sleep", type=float, default=0, 
                       help="Sleep duration between turns in seconds (default: 0)")
    return parser.parse_args()


def ensure_reports_directory_exists():
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def generate_timestamped_report_path(reports_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(reports_dir, f"benchmark_report_{timestamp}.md")


def determine_output_path(output_arg):
    reports_dir = ensure_reports_directory_exists()
    
    if output_arg is None:
        return generate_timestamped_report_path(reports_dir)
    
    if os.path.isabs(output_arg):
        return output_arg
    
    return os.path.join(reports_dir, output_arg)


def create_persona_from_name(persona_name):
    persona_map = {
        "expert": ExpertPersona,
        "novice": NovicePersona,
        "learner": LearnerPersona
    }
    return persona_map[persona_name]()


def execute_benchmark(persona, turns, sleep_duration):
    student = SimulatedStudent(persona)
    runner = BenchmarkRunner(student, turns=turns, sleep_duration=sleep_duration)
    return runner.run()


def save_report(report, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nBenchmark completed. Report saved to {output_path}")


def main():
    args = parse_arguments()
    output_path = determine_output_path(args.output)
    
    print(f"Initializing benchmark for {args.persona} with {args.turns} turns...")
    
    persona = create_persona_from_name(args.persona)
    report = execute_benchmark(persona, args.turns, args.sleep)
    save_report(report, output_path)

if __name__ == "__main__":
    main()

