from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langgraph.graph import START, END, StateGraph

load_dotenv(override=True)

llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.8)

class GraphState(BaseModel):
    user_input: str = Field(description="The user input to the graph.")
    decision: Optional[Literal["story", "joke"]] = Field(default=None, description="The decision of the graph.")
    final_output: Optional[str] = Field(default=None, description="The final output of the graph.")

def validator(state: GraphState):
    user_input = state.user_input
    prompt = PromptTemplate(
        template=
        """
        You are a helpful AI assistant, your job is to decide if the user input is a story or a joke.
        Always respond with a single word, either "story" or "joke".

        Here is the user input: {user_input}
        """,
        input_variables=["user_input"]
    )
    chain = prompt | llm
    response = chain.invoke({"user_input": user_input})
    return {"decision": response.content}
    
def router(state: GraphState):
    decision = state.decision
    if decision == "story":
        return "story"
    else:
        return "joke"
    
def story_node(_: GraphState):
    prompt = PromptTemplate(
        template="Tell me a randmon story, not longer than 100 words."
    )
    chain = prompt | llm
    response = chain.invoke({})
    return {"final_output": response.content}

    
def joke_node(_: GraphState):
    prompt = PromptTemplate(
        template="Tell me a randmon joke, not longer than 20 words."
    )
    chain = prompt | llm
    response = chain.invoke({})
    return {"final_output": response.content}

builder = StateGraph(GraphState)

builder.add_node("validator", validator)
builder.add_node("story_node", story_node)
builder.add_node("joke_node", joke_node)

builder.add_edge(START, "validator")
builder.add_conditional_edges("validator", router, {
    "story": "story_node",
    "joke": "joke_node"
})
builder.add_edge("story_node", END)
builder.add_edge("joke_node", END)

graph = builder.compile()

# response = graph.invoke({"user_input": "tell me a story."})

# print(response)

# print(graph.get_graph().draw_ascii())