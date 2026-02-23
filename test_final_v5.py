
import os
import sys
import json
from langchain_core.messages import HumanMessage
sys.path.append(os.path.abspath('.'))
from agent_local_v5 import build_v5

def test_final():
    agent = build_v5()
    goal = "Décris l'image test_vision.png dans le dossier input."
    inputs = {
        "goal": goal,
        "messages": [HumanMessage(content=goal)],
        "facts": [],
        "iteration": 0,
        "verdict": "RETRY"
    }
    
    print("--- AGENT START ---")
    for op in agent.stream(inputs):
        node = list(op.keys())[0]
        print(f"Node: {node}")
        if node == "writer":
            print("--- REPORT START ---")
            print(op["writer"]["messages"][-1].content)
            print("--- REPORT END ---")

if __name__ == "__main__":
    test_final()
