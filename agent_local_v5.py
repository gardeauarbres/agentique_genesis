import os
import json
import subprocess
import logging
import hashlib
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated
from pydantic import BaseModel, Field
from datetime import datetime

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
import sys
import concurrent.futures
import chromadb
from chromadb.config import Settings

# ====== CONFIGURATION ======
MODEL_NAME = "qwen2.5:7b-instruct"
VISION_MODEL = "llava:7b"
ROOT_DIR = os.path.abspath(r"C:\agent")
INPUT_DIR = os.path.join(ROOT_DIR, "input")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
LOG_FILE = os.path.join(OUTPUT_DIR, "agent.log")
JSON_MEMORY_FILE = os.path.join(OUTPUT_DIR, "memory.json")
CHROMA_DIR = os.path.join(OUTPUT_DIR, "chroma_db")
EMBED_MODEL = "nomic-embed-text"

for d in (INPUT_DIR, OUTPUT_DIR, SCRIPTS_DIR, CHROMA_DIR): os.makedirs(d, exist_ok=True)

ALLOWED_SCRIPTS = {"hello.py", "list_input.py", "analyze_csv.py"}
SANDBOX_IMAGE = "agent-sandbox-v5"
SANDBOX_DOCKERFILE = os.path.join(ROOT_DIR, "Dockerfile.sandbox")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Instances globales pour les outils partagés
llm_vision = ChatOllama(model=VISION_MODEL, temperature=0)
ddgs = DDGS()

# ====== MEMOIRE PERSISTANTE (ChromaDB) ======
def _get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(name="agent_memory")

def _get_embedding(text: str):
    try:
        res = requests.post("http://localhost:11434/api/embeddings", json={"model": EMBED_MODEL, "prompt": text})
        return res.json()["embedding"]
    except Exception as e:
        logging.error(f"Embedding error: {e}")
        return [0.0] * 768 # Fallback

def _save_memory_v6(fact: str):
    collection = _get_chroma_collection()
    embedding = _get_embedding(fact)
    doc_id = hashlib.md5(fact.encode()).hexdigest()
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[fact],
        metadatas=[{"ts": datetime.now().isoformat()}]
    )

def _recall_memory_v6(query: str):
    collection = _get_chroma_collection()
    embedding = _get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5
    )
    if results and results["documents"]:
        return "\n".join(results["documents"][0]) or "Pas de correspondance."
    return "Pas de memoire."

# Backwards compatibility / Transition
def _save_memory(fact: str): _save_memory_v6(fact)
def _recall_memory(query: str): return _recall_memory_v6(query)

# ====== TOOLS ======

@tool
def list_files(recursive: bool = False) -> str:
    """Liste les fichiers dans input."""
    try:
        files = os.listdir(INPUT_DIR)
        files.sort()
        return "\n".join(files) if files else "Vide."
    except Exception as e: return str(e)

@tool
def read_file(filename: str) -> str:
    """Lit un fichier dans input."""
    try:
        with open(os.path.join(INPUT_DIR, filename), "r", encoding="utf-8", errors="replace") as f:
            return f.read(100_000)
    except Exception as e: return str(e)

@tool
def web_search(query: str) -> str:
    """Recherche sur Internet."""
    try:
        results = list(ddgs.text(query, max_results=5))
        return "\n".join([f"- {r.get('title')} ({r.get('href')}): {r.get('body')}" for r in results])
    except Exception as e: return str(e)

@tool
def web_fetch(url: str) -> str:
    """Lit une page web."""
    try:
        import urllib3
        urllib3.disable_warnings()
        res = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(res.text, "html.parser")
        for e in soup(["script", "style"]): e.decompose()
        return soup.get_text(separator=' ', strip=True)[:30_000]
    except Exception as e: return str(e)

@tool
def write_and_run_code(code: str) -> str:
    """Execute Python dans Docker (numpy, pandas). Limité à 30s, 256MB, Pas de réseau."""
    try:
        res = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "256m", "--cpus", "0.5", SANDBOX_IMAGE, "python", "-c", code], capture_output=True, text=True, timeout=30)
        return f"Out: {res.stdout}\nErr: {res.stderr}"
    except subprocess.TimeoutExpired:
        return "Erreur: Le script a dépassé la limite de temps (30s)."
    except Exception as e: return str(e)

@tool
def memorize(fact: str) -> str:
    """Stocke un fait important dans la memoire persistante."""
    _save_memory(fact)
    return f"Fait memorise: {fact[:50]}..."

@tool
def recall_memory(query: str) -> str:
    """Retrouve des faits passes dans la memoire via mots Cles."""
    return f"Resultat de la memoire:\n{_recall_memory(query)}"

@tool
def describe_image(filename: str) -> str:
    """Analyse une image dans le dossier input via le modèle de vision local (Llava)."""
    target = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(target): return f"Erreur: Image {filename} introuvable."
    import base64
    try:
        with open(target, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        msg = HumanMessage(content=[
            {"type": "text", "text": """Analyse cette image de manière structurée :
1. **Description Générale** : Ce que l'on voit au premier coup d'œil.
2. **Éléments Clés** : Détails importants, textes visibles, objets spécifiques.
3. **Contexte technique** : Couleurs dominantes, éclairage, type d'image (photo, graphique, code, etc.).
Réponds avec précision pour aider un agent intelligent à comprendre l'objectif de l'image."""},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
        ])
        res = llm_vision.invoke([msg])
        return f"Analyse de {filename} :\n{res.content}"
    except Exception as e:
        return f"Erreur vision: {str(e)}"

tools = [list_files, read_file, web_search, web_fetch, write_and_run_code, memorize, recall_memory, describe_image]
TOOLS_BY_NAME = {t.name: t for t in tools}

class AgentState(TypedDict):
    goal: str
    messages: List[Any]
    facts: List[str]
    iteration: int
    verdict: str

def build_v5(model_name: str = MODEL_NAME, vision_model: str = VISION_MODEL):
    global llm_vision
    llm_vision = ChatOllama(model=vision_model, temperature=0)
    # LLM local pour cette instance du graph
    llm_local = ChatOllama(model=model_name, temperature=0, format="json")
    llm_text_local = ChatOllama(model=model_name, temperature=0)
    llm_tools_local = llm_text_local.bind_tools(tools)
    llm_vision_local = ChatOllama(model=vision_model, temperature=0)

    # Injection du modèle de vision dans les outils si nécessaire ou via le state
    # Ici on va plutôt passer le modèle au planner via le système

    def planner_node(state: AgentState):
        system = f"Tu es le Planner V5 (Modèle: {model_name}). Utilise 'recall_memory' en premier. 'memorize' les faits clés. Pour voir une image, utilise 'describe_image'."
        msg = llm_tools_local.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [msg]}

    def researcher_node(state: AgentState):
        last = state["messages"][-1]
        msgs = []
        new_tool_count = state.get("tool_count", 0)
        new_search_count = state.get("search_count", 0)
        
        if hasattr(last, "tool_calls"):
            for tc in last.tool_calls:
                new_tool_count += 1
                if tc["name"] == "web_search":
                    new_search_count += 1
                
                fn = TOOLS_BY_NAME.get(tc["name"])
                
                # Cas spécial pour vision : on injecte le modèle choisi
                if tc["name"] == "describe_image":
                    # On pourrait passer vision_model ici si l'outil le supportait. 
                    # Pour l'instant on utilise llm_vision global mais on pourrait le rendre local.
                    pass
                
                res = fn.invoke(tc["args"]) if fn else "Err"
                msgs.append(ToolMessage(tool_call_id=tc["id"], content=str(res)))
        return {"messages": msgs, "tool_count": new_tool_count, "search_count": new_search_count}

    def writer_node(state: AgentState):
        res = llm_text_local.invoke([SystemMessage(content="Rédige le rapport final en Markdown.")] + state["messages"])
        return {"messages": [res]}

    def verifier_node(state: AgentState):
        res = llm_local.invoke([SystemMessage(content="JSON PASS/RETRY/STOP (e.g. {\"verdict\": \"PASS\"})")] + state["messages"])
        try: v = json.loads(res.content).get("verdict", "PASS")
        except: v = "PASS"
        return {"verdict": v, "iteration": state["iteration"] + 1}

    w = StateGraph(AgentState)
    w.add_node("planner", planner_node); w.add_node("tools", researcher_node)
    w.add_node("writer", writer_node); w.add_node("verifier", verifier_node)
    w.set_entry_point("planner")
    w.add_conditional_edges("planner", lambda s: "tools" if hasattr(s["messages"][-1], "tool_calls") and s["messages"][-1].tool_calls else "writer")
    w.add_edge("tools", "planner"); w.add_edge("writer", "verifier")
    w.add_conditional_edges("verifier", lambda s: "writer" if s["verdict"] == "RETRY" and s["iteration"] < 5 else END)
    return w.compile()

if __name__ == "__main__":
    agent = build_v5()
    goal = input("Objectif V5: ")
    inputs = {"goal": goal, "messages": [HumanMessage(content=goal)], "facts": [], "iteration": 0, "verdict": "RETRY"}
    for op in agent.stream(inputs): print(f"Node: {list(op.keys())[0]}")
