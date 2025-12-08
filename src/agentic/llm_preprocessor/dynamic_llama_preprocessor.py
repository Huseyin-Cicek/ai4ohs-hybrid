from typing import Dict, List
import re

"""
Dynamic Llama.cpp Fine-Tuning Preprocessor v1.0
------------------------------------------------

Amaç:
- Model girişini optimize etmek.
- Uzun içerikleri kısaltmak, gereksiz kısımları çıkarmak.
- ESS/ISO/6331 maddelerini önceliklendirmek.
- Clean & normalized prompt üretmek.
"""



class DynamicLlamaPreprocessor:

    def clean(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_priority_content(self, text: str) -> str:
        """
        ESS / 6331 / ISO maddelerini önceliklendirir.
        """
        priorities = []
        for line in text.split("."):
            if any(key in line.lower() for key in ["ess", "6331", "iso", "hazard", "risk"]):
                priorities.append(line.strip())
        return ". ".join(priorities) or text

    def compress(self, text: str, limit: int = 2000) -> str:
        """
        Token limitine uygun şekilde kesilmiş içerik üretir.
        """
        if len(text) <= limit:
            return text
        return text[:limit] + "... [compressed]"

    def preprocess(self, prompt: str) -> str:
        clean = self.clean(prompt)
        pri = self.extract_priority_content(clean)
        comp = self.compress(pri)
        return comp
