"""Agentic RAG with LangGraph state machine."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain_google_vertexai import ChatVertexAI

class RAGState(TypedDict):
    query: str; documents: List[str]; answer: str
    relevance_score: float; iterations: int; strategy: str

def create_agentic_rag():
    llm = ChatVertexAI(model_name="gemini-1.5-pro-002")
    graph = StateGraph(RAGState)

    def classify_query(state):
        prompt = f"Classify as simple/complex/multi-hop: {state['query']}"
        strategy = llm.invoke(prompt).content.strip().lower()
        return {**state, "strategy": strategy}

    def retrieve(state):
        return {**state, "documents": [f"doc_{i}" for i in range(5)]}

    def grade_documents(state):
        score = 0.9 if state["strategy"] == "simple" else 0.6
        return {**state, "relevance_score": score}

    def generate(state):
        context = "\n".join(state["documents"])
        answer = llm.invoke(f"Context: {context}\nQ: {state['query']}").content
        return {**state, "answer": answer}

    def should_correct(state): return "correct" if state["relevance_score"] < 0.7 else "generate"

    graph.add_node("classify", classify_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade", grade_documents)
    graph.add_node("generate", generate)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", should_correct, {"correct": "retrieve", "generate": "generate"})
    graph.add_edge("generate", END)
    return graph.compile()
