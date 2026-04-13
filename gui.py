from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from .orchestrator import Orchestrator
from .memory import index_project
from .config import BASE_DIR

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Engineer Pro v4")
        self.geometry("1250x820")
        self.orch = Orchestrator()
        self.repo_path = None
        self.build()

    def build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        self.task = tk.StringVar()
        ttk.Label(top, text="المهمة:").pack(side="left")
        ttk.Entry(top, textvariable=self.task).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(top, text="اختيار Repo", command=self.pick_repo).pack(side="left", padx=4)
        ttk.Button(top, text="فهرسة", command=self.index_repo).pack(side="left", padx=4)
        ttk.Button(top, text="تشغيل", command=self.run_task).pack(side="left", padx=4)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body, padding=4)
        right = ttk.Frame(body, padding=4)
        body.add(left, weight=1)
        body.add(right, weight=2)

        self.tabs = ttk.Notebook(left)
        self.tabs.pack(fill="both", expand=True)

        self.log_box = tk.Text(self.tabs, wrap="word")
        self.code_box = tk.Text(self.tabs, wrap="word")
        self.plan_box = tk.Text(self.tabs, wrap="word")
        self.memory_box = tk.Text(self.tabs, wrap="word")
        self.tabs.add(self.log_box, text="النتيجة")
        self.tabs.add(self.code_box, text="الكود")
        self.tabs.add(self.plan_box, text="الخطة")
        self.tabs.add(self.memory_box, text="الذاكرة")

        self.right_tabs = ttk.Notebook(right)
        self.right_tabs.pack(fill="both", expand=True)
        self.retrieval_box = tk.Text(self.right_tabs, wrap="word")
        self.history_box = tk.Text(self.right_tabs, wrap="word")
        self.right_tabs.add(self.retrieval_box, text="الاسترجاع")
        self.right_tabs.add(self.history_box, text="سجل المحاولات")

        self._refresh_memory()

    def pick_repo(self):
        path = filedialog.askdirectory(title="اختر مجلد المشروع")
        if path:
            self.repo_path = path
            messagebox.showinfo("Repo", f"تم اختيار:\n{path}")

    def index_repo(self):
        if not self.repo_path:
            messagebox.showwarning("تنبيه", "اختر مشروعًا أولًا.")
            return
        count = index_project(Path(self.repo_path), self.orch.index)
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", f"تمت فهرسة {count} مقطعًا من المشروع.\n")
        self._refresh_memory()

    def run_task(self):
        task = self.task.get().strip()
        if not task:
            messagebox.showwarning("تنبيه", "اكتب مهمة أولًا.")
            return
        result = self.orch.handle(task, repo_path=self.repo_path)
        self.plan_box.delete("1.0", "end")
        self.plan_box.insert("end", json.dumps(result.get("plan", {}), ensure_ascii=False, indent=2))
        self.code_box.delete("1.0", "end")
        self.code_box.insert("end", result.get("final_code", ""))
        self.retrieval_box.delete("1.0", "end")
        self.retrieval_box.insert("end", json.dumps(result.get("retrieval", {}), ensure_ascii=False, indent=2))
        self.history_box.delete("1.0", "end")
        self.history_box.insert("end", json.dumps(result.get("history", []), ensure_ascii=False, indent=2))
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", json.dumps({
            "best_score": result.get("best_score"),
            "best_result": result.get("best_result"),
            "plugin_note": result.get("plugin_note"),
        }, ensure_ascii=False, indent=2))
        self._refresh_memory()

    def _refresh_memory(self):
        recent = self.orch.memory.recent(limit=25)
        self.memory_box.delete("1.0", "end")
        self.memory_box.insert("end", json.dumps(recent, ensure_ascii=False, indent=2))

def run_app():
    App().mainloop()
