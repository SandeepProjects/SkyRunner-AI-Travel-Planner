import os
import operator
from typing import TypedDict, Annotated, List, Any
import psycopg
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

load_dotenv()

groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip(" ;\"'")
groq_model = (os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile").strip(" ;\"'")
database_url = (os.getenv("DATABASE_URL") or "").strip(" ;\"'")

llm = ChatGroq(
    model=groq_model,
    api_key=groq_api_key
)

class TravelState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

def flight_agent(state: TravelState):
    query = state.get("user_query", "")
    flight_data = search_flights(query)
    
    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight results fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def hotel_agent(state: TravelState):
    query = state.get("user_query", "")
    tavily_query = f"Best hotels for {query}"
    hotel_results = tavily_search(tavily_query)

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def itinerary_agent(state: TravelState):
    prompt = f"""
    Create a travel itinerary using the following information:

    User Query:
    {state.get('user_query', '')}
    
    Flight results:
    {state.get('flight_results', '')}
    
    Hotel results:
    {state.get('hotel_results', '')}
    """
    
    response = llm.invoke([
        SystemMessage(content="You are an expert travel planning assistant. Use the data provided to create a comprehensive travel itinerary."),
        HumanMessage(content=prompt)
    ])
    
    return {
        "itinerary": response.content,
        "messages": [AIMessage(content=f"Itinerary created.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def build_graph():
    graph = StateGraph(TravelState)

    graph.add_node("flight_node", flight_agent)
    graph.add_node("hotel_node", hotel_agent)
    graph.add_node("itinerary_node", itinerary_agent)

    # Simple workflow: Start -> Flight -> Hotel -> Itinerary -> End
    graph.add_edge(START, "flight_node")
    graph.add_edge("flight_node", "hotel_node")
    graph.add_edge("hotel_node", "itinerary_node")
    graph.add_edge("itinerary_node", END)

    return graph

def run_travel_agent(user_query: str, thread_id: str = "skyrunner_dashboard") -> dict:
    graph_builder = build_graph()
    
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    
    result = {
        "success": False,
        "user_query": user_query,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "final_answer": "",
        "llm_calls": 0,
        "thread_id": thread_id,
        "agent_steps": []
    }
    
    try:
        with psycopg.connect(database_url, **connection_kwargs) as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            app = graph_builder.compile(checkpointer=checkpointer)

            thread = {"configurable": {"thread_id": thread_id}}
            
            initial_state = {
                "user_query": user_query,
                "messages": [HumanMessage(content=user_query)],
                "llm_calls": 0
            }

            for event in app.stream(initial_state, thread, stream_mode="values"):
                if "messages" in event and len(event["messages"]) > 0:
                    latest_message = event["messages"][-1]
                    if isinstance(latest_message, AIMessage):
                        result["agent_steps"].append(latest_message.content)

            final_state = app.get_state(thread).values
            result["success"] = True
            result["flight_results"] = final_state.get("flight_results", "")
            result["hotel_results"] = final_state.get("hotel_results", "")
            result["itinerary"] = final_state.get("itinerary", "")
            result["final_answer"] = final_state.get("itinerary", "")
            result["llm_calls"] = final_state.get("llm_calls", 0)
            
    except Exception as e:
        result["final_answer"] = f"Error running agent: {str(e)}"
        
    return result

def main():
    user_input = "Find flights from LCA to ATH and suggest hotels for 2 nights."
    print(f"User Query: {user_input}")
    print("\n--- Running Graph ---\n")
    
    result = run_travel_agent(user_input, thread_id="cli_test_thread")
    
    if result["agent_steps"]:
        for step in result["agent_steps"]:
            print(f"Agent Update: {step}")
            
    print("\n=== FINAL ITINERARY ===\n")
    print(result["itinerary"] if result["itinerary"] else result["final_answer"])
    print(f"\nTotal LLM calls: {result['llm_calls']}")

if __name__ == "__main__":
    main()