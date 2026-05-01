import csv
import time

from pipeline import run_research_pipeline

TOPICS = [
    "LLM agents in 2025",
    "CRISPR gene editing advances",
    "Fusion energy progress",
    "Quantum computing breakthroughs",
    "RAG vs fine-tuning tradeoffs",
]

FIELDNAMES = ["topic", "score", "revision_count", "latency_seconds"]


def main():
    rows = []

    for topic in TOPICS:
        print(f"\n{'='*60}")
        print(f"Topic: {topic}")

        t0 = time.perf_counter()
        result = run_research_pipeline(topic)
        latency_seconds = round(time.perf_counter() - t0, 2)

        critique = result.get("critique")
        score = critique.score if critique else "N/A"
        revision_count = result.get("revision_count", 0)

        print(f"Score: {score} | Revisions: {revision_count}")
        print("="*60)

        rows.append({
            "topic": topic,
            "score": score,
            "revision_count": revision_count,
            "latency_seconds": latency_seconds,
        })

    with open("eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
