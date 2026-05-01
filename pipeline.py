from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agents import build_reader_agent, build_search_agent, get_writer_chain, get_critic_chain, CritiqueResult


class ResearchState(TypedDict):
    topic: str
    search_results: str
    scraped_content: str
    report: str
    critique: CritiqueResult
    revision_count: int


def search_node(state: ResearchState) -> dict:
    print("\n" + " =" * 50)
    print("step 1 - search agent is working ...")
    print("=" * 50)

    search_agent = build_search_agent()
    result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {state['topic']}")]
    })
    search_results = result['messages'][-1].content
    print("\n search result ", search_results)
    return {"search_results": search_results}


def reader_node(state: ResearchState) -> dict:
    print("\n" + " =" * 50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("=" * 50)

    reader_agent = build_reader_agent()
    result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{state['topic']}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })
    scraped_content = result['messages'][-1].content
    print("\nscraped content: \n", scraped_content)
    return {"scraped_content": scraped_content}


def writer_node(state: ResearchState) -> dict:
    print("\n" + " =" * 50)
    critique = state.get("critique")
    is_revision = critique is not None
    label = "revision" if is_revision else "draft"
    print(f"step 3 - Writer is producing {label} ...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    chain_input = {"topic": state["topic"], "research": research_combined}
    if is_revision:
        chain_input["previous_report"] = state["report"]
        chain_input["weaknesses"] = "\n".join(f"- {w}" for w in critique.weaknesses)

    writer_chain = get_writer_chain()
    report = writer_chain.invoke(chain_input)
    print("\n Final Report\n", report)

    updates: dict = {"report": report}
    if is_revision:
        updates["revision_count"] = state["revision_count"] + 1
    return updates


def should_revise(state: ResearchState) -> str:
    critique = state["critique"]
    if critique.score < 7 and state["revision_count"] < 1:
        print(f"\n[should_revise] Score {critique.score} < 7 — triggering revision")
        return "writer"
    print(f"\n[should_revise] Score {critique.score} — done")
    return "END"


def critic_node(state: ResearchState) -> dict:
    print("\n" + " =" * 50)
    print("step 4 - critic is reviewing the report ")
    print("=" * 50)

    critic_chain = get_critic_chain()
    critique = critic_chain.invoke({
        "report": state['report']
    })
    print("\n critic report \n", critique)
    return {"critique": critique}


def _build_graph(enable_revision: bool = True):
    graph = StateGraph(ResearchState)
    graph.add_node("search", search_node)
    graph.add_node("reader", reader_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", "reader")
    graph.add_edge("reader", "writer")
    graph.add_edge("writer", "critic")
    if enable_revision:
        graph.add_conditional_edges("critic", should_revise, {"writer": "writer", "END": END})
    else:
        graph.add_edge("critic", END)
    return graph.compile()


def run_research_pipeline(topic: str, enable_revision: bool = True) -> dict:
    pipeline = _build_graph(enable_revision)
    initial_state: ResearchState = {
        "topic": topic,
        "search_results": "",
        "scraped_content": "",
        "report": "",
        "critique": None,
        "revision_count": 0,
    }
    return pipeline.invoke(initial_state)


if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)
