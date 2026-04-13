from __future__ import annotations

class PlannerAgent:
    def run(self, task: str, context: dict) -> dict:
        return {"plan": ["فهم الطلب", "استرجاع السياق", "توليد كود", "تشغيل", "إصلاح", "تحسين"], "task": task}

class RetrieverAgent:
    def __init__(self, index):
        self.index = index
    def run(self, task: str, context: dict) -> dict:
        return {"hits": self.index.search(task, k=5)}

class CoderAgent:
    def __init__(self, llm=None):
        self.llm = llm
    def run(self, task: str, context: dict) -> dict:
        hits = context.get("retrieval", {}).get("hits", [])
        if self.llm:
            prompt = f"Return a full, working answer for this task as code if appropriate. Task: {task}\nContext: {hits}"
            out = self.llm(prompt)
            if out:
                return {"code": out}
        hint = ""
        if hits:
            top = hits[0]
            hint = f"# Related file: {top['meta'].get('path')}\n# Snippet:\n{top['text'][:500]}\n\n"
        code = f'''{hint}def solve():
    return {{
        "task": {task!r},
        "status": "generated",
        "note": "Local scaffold"
    }}

if __name__ == "__main__":
    print(solve())
'''
        return {"code": code}

class ReviewerAgent:
    def run(self, task: str, context: dict) -> dict:
        code = context.get("code", "")
        issues = []
        if "TODO" in code:
            issues.append("Contains TODO markers.")
        return {"approved": not issues, "issues": issues}

class RefactorAgent:
    def run(self, task: str, context: dict) -> dict:
        code = context.get("code", "")
        return {"code": code.replace("Local scaffold", "Local scaffold (refined)")}

class DebuggerAgent:
    def __init__(self, run_fn):
        self.run_fn = run_fn
    def run(self, task: str, context: dict) -> dict:
        return {"result": self.run_fn(context.get("code", ""))}
