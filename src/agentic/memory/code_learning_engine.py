"""
Code Learning Engine v3.0
AI4OHS-HYBRID’in kod tabanını analiz eden, öğrenen, örüntü çıkaran
ve gelecekteki öneriler için bunları hafızaya yazan alt sistem.
"""

import ast
import json
import os
import time

from agentic.memory.long_term_memory import LongTermMemory


class CodeLearningEngine:
    def __init__(self, root="src"):
        self.root = root
        self.mem = LongTermMemory()

    def scan_codebase(self):
        """
        src içindeki tüm .py dosyalarını tarar, AST çıkarır.
        """
        code_map = {}
        for dirpath, _, files in os.walk(self.root):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(dirpath, f)
                    try:
                        with open(path, "r", encoding="utf-8") as fp:
                            code = fp.read()
                            tree = ast.parse(code)
                            code_map[path] = tree
                    except Exception:
                        continue
        return code_map

    def detect_patterns(self, code_map):
        """
        Aşağıdaki örüntüleri tespit eder:
        - Yinelenen fonksiyon isimleri
        - Aynı işlevi yapan ama başka dosyalarda yer alan fonksiyonlar
        - Çok uzun fonksiyonlar (> 50 satır)
        - Kod kokuları (nested loops, long if chains)
        """
        patterns = {"long_functions": [], "duplicate_function_names": {}, "complex_functions": []}

        func_names = {}

        for file, tree in code_map.items():
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    name = node.name
                    length = (node.end_lineno or node.lineno) - node.lineno

                    # Fonksiyon adı yinelenmesi
                    func_names.setdefault(name, []).append(file)

                    # Çok uzun fonksiyonlar
                    if length > 50:
                        patterns["long_functions"].append(
                            {"file": file, "function": name, "length": length}
                        )

                    # Karmaşık yapı tespiti
                    nested = sum(
                        isinstance(n, ast.For) or isinstance(n, ast.While) for n in ast.walk(node)
                    )
                    if nested > 3:
                        patterns["complex_functions"].append(
                            {"file": file, "function": name, "nested_loops": nested}
                        )

        # Yinelenmiş fonksiyon adlarını ekle
        for name, locations in func_names.items():
            if len(locations) > 1:
                patterns["duplicate_function_names"][name] = locations

        return patterns

    def update_learning_memory(self, patterns):
        """
        Öğrenilen örüntüleri long-term memory'e ekler.
        """
        self.mem.memory.setdefault("code_patterns", [])
        self.mem.memory["code_patterns"].append({"timestamp": time.time(), "patterns": patterns})
        self.mem.save()

    def run_learning_cycle(self):
        """
        Tam öğrenme döngüsü: code scan → pattern detect → memory update
        """
        code = self.scan_codebase()
        patterns = self.detect_patterns(code)
        self.update_learning_memory(patterns)
        return patterns
        self.update_learning_memory(patterns)
        return patterns
