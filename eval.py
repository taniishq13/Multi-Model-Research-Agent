from pipeline import run_research_pipeline

TOPICS = [
    "LLM agents in 2025",
    "CRISPR gene editing advances",
    "Fusion energy progress",
    "Quantum computing breakthroughs",
    "RAG vs fine-tuning tradeoffs",
]


def main():
    for topic in TOPICS:
        print(f"\n{'='*60}")
        print(f"Topic: {topic}")
        result = run_research_pipeline(topic)
        critique = result.get("critique")
        score = critique.score if critique else "N/A"
        revision_count = result.get("revision_count", 0)
        print(f"Score: {score} | Revisions: {revision_count}")
        print("="*60)


if __name__ == "__main__":
    main()
