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

def main():
    parser = argparse.ArgumentParser(description="Run Adaptive AI Benchmarking")
    parser.add_argument("--persona", type=str, choices=["expert", "novice", "learner"], required=True, help="Simulated student persona")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--output", type=str, default=None, help="Output report file (default: benchmark_report_<timestamp>.md)")
    parser.add_argument("--sleep", type=float, default=0, help="Sleep duration between turns in seconds (default: 0)")
    
    args = parser.parse_args()
    
    # Generate default output filename with timestamp if not provided
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"benchmark_report_{timestamp}.md"
    
    print(f"Initializing benchmark for {args.persona} with {args.turns} turns...")
    
    # Factory logic
    if args.persona == "expert":
        persona = ExpertPersona()
    elif args.persona == "novice":
        persona = NovicePersona()
    elif args.persona == "learner":
        persona = LearnerPersona()
    else:
        raise ValueError("Invalid persona")
        
    student = SimulatedStudent(persona)
    runner = BenchmarkRunner(student, turns=args.turns, sleep_duration=args.sleep)
    
    report = runner.run()
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\nBenchmark completed. Report saved to {args.output}")

if __name__ == "__main__":
    main()

