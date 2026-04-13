from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .agents import PlannerAgent, RetrieverAgent, CoderAgent, ReviewerAgent, RefactorAgent, DebuggerAgent
from .config import PLUGINS_DIR
from .memory import SQLiteMemory, SimpleIndex
from .plugins import load_plugins
from .tools import run_ollama, run_python, run_cpp
from .logging_utils import get_logger

logger = get_logger(__name__)

class Orchestrator:
    def __init__(self):
        self.memory = SQLiteMemory()
        self.index = SimpleIndex("projects")
        self.plugins = load_plugins(PLUGINS_DIR)
        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent(self.index)
        self.coder = CoderAgent(llm=self.llm)
        self.reviewer = ReviewerAgent()
        self.refactorer = RefactorAgent()
        self.debugger = DebuggerAgent(self.run_code)
        self.max_loops = 8

    def llm(self, prompt: str):
        return run_ollama(prompt)

    def run_code(self, code: str):
        if "#include" in code or "std::" in code:
            return run_cpp(code)
        return run_python(code)

    def score(self, code: str, result: dict):
        score = 0
        if result.get("success"):
            score += 6
        if len(code) > 40:
            score += 1
        if "TODO" not in code:
            score += 1
        if "error" not in (result.get("stderr", "").lower()):
            score += 1
        return score

    def handle(self, task: str, repo_path: str | None = None):
        self.memory.put("task", "latest", {"task": task, "repo_path": repo_path})
        plan = self.planner.run(task, {})
        with ThreadPoolExecutor(max_workers=2) as pool:
            retrieval = pool.submit(self.retriever.run, task, {}).result()

        code = self.coder.run(task, {"retrieval": retrieval}).get("code", "")
        best_code = code
        best_score = -1
        best_result = {"success": False}
        history = []

        for _ in range(self.max_loops):
            review = self.reviewer.run(task, {"code": code})
            debug = self.debugger.run(task, {"code": code})
            result = debug["result"]
            s = self.score(code, result)
            history.append({"score": s, "review": review, "result": result})
            if s > best_score:
                best_score = s
                best_code = code
                best_result = result
            if result.get("success") and s >= 8:
                break
            code = self.refactorer.run(task, {"code": code})["code"]

        output = {"plan": plan, "retrieval": retrieval, "final_code": best_code, "best_score": best_score, "best_result": best_result, "history": history}
        for plugin in self.plugins:
            try:
                output = plugin.run(output)
            except Exception as e:
                logger.exception("Plugin failed: %s", e)
        self.memory.put("result", task[:80], output)
        return output
