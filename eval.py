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

FIELDNAMES = ["topic", "score", "revision_count", "latency_seconds", "mode"]

MODES = [
    ("baseline", False),
    ("with_revision", True),
]


def main():
    rows = []

    for mode_label, enable_revision in MODES:
        print(f"\n{'#'*60}")
        print(f"Mode: {mode_label}")
        print(f"{'#'*60}")

        for topic in TOPICS:
            print(f"\n{'='*60}")
            print(f"Topic: {topic}")

            t0 = time.perf_counter()
            result = run_research_pipeline(topic, enable_revision=enable_revision)
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
                "mode": mode_label,
            })

    with open("eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*60}")
    print("Summary — average score by mode:")
    for mode_label, _ in MODES:
        mode_rows = [r for r in rows if r["mode"] == mode_label and isinstance(r["score"], int)]
        avg = round(sum(r["score"] for r in mode_rows) / len(mode_rows), 2) if mode_rows else "N/A"
        print(f"  {mode_label}: {avg}")
    print("="*60)


if __name__ == "__main__":
    main()
