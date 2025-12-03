import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from final.benchmark.simulated_student import SimulatedStudent, ExpertPersona, NovicePersona, LearnerPersona
from final.benchmark.runner import BenchmarkRunner

def main():
    parser = argparse.ArgumentParser(description="Run Adaptive AI Benchmarking")
    parser.add_argument("--persona", type=str, choices=["expert", "novice", "learner"], required=True, help="Simulated student persona")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to simulate")
    parser.add_argument("--output", type=str, default="benchmark_report.md", help="Output report file")
    
    args = parser.parse_args()
    
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
    runner = BenchmarkRunner(student, turns=args.turns)
    
    report = runner.run()
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\nBenchmark completed. Report saved to {args.output}")

if __name__ == "__main__":
    main()

