from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

llm = ChatOllama(model="qwen2.5:3b")

class chatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chatBot(state):

    message = state['messages']

    response = llm.invoke(message)

    if not response.content and not response.tool_calls:
        response = AIMessage(
            content="I couldn't process your request. Please try again or rephrase your request."
        )

    return {'messages': [response]}

checkpointer= InMemorySaver()
graph = StateGraph(chatState)
graph.add_node('chatBot', chatBot)
graph.add_edge(START, 'chatBot')
graph.add_edge('chatBot', END)

chatBot = graph.compile(checkpointer=checkpointer)