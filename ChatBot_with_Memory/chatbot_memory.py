import os
import uuid
from typing import List
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore

DB_URI = os.getenv("DB_URI", "postgresql://postgres:postgres@localhost:5432/chatmemory")
NAMESPACE = ("user", "u1", "details")  # where this user's memories live in Postgres

llm = ChatOllama(model="qwen2.5:3b")

class NewFacts(BaseModel):
    facts: List[str]

extractor = llm.with_structured_output(NewFacts)

def remember(state: MessagesState, store: BaseStore):
    known = [item.value["data"] for item in store.search(NAMESPACE)]

    result = extractor.invoke([
        SystemMessage(content=("Extract stable facts about the user (name, preferences, projects) from their message. "
            "Skip anything already known. Return an empty list if there is nothing new.\n"
            f"Already known: {known}")),
            state["messages"][-1],
    ])

    for fact in (result.facts if result else[]):
        if fact not in known:
            store.put(NAMESPACE, str(uuid.uuid4()),{"data":fact})
            print("[saved to Postgres]", fact)

    return{}

def chat(state: MessagesState, store: BaseStore):
    