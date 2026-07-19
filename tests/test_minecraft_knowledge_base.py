import unittest
from pathlib import Path


KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base" / "minecraft"
TECHNICAL_DOCUMENTS = (
    "07_生电_红石时序与算法.md",
    "08_生电_物流分类与存储.md",
    "09_生电_刷怪农场与区块.md",
    "10_生电_测试与版本差异.md",
)


class MinecraftKnowledgeBaseTests(unittest.TestCase):
    def test_expected_documents_exist_with_retrieval_tags(self):
        for document in TECHNICAL_DOCUMENTS:
            content = (KB_DIR / document).read_text(encoding="utf-8")
            self.assertTrue(content.startswith("# "))
            self.assertIn("标签：生电", content)

    def test_technical_documents_include_code_or_state_models(self):
        for document in TECHNICAL_DOCUMENTS:
            content = (KB_DIR / document).read_text(encoding="utf-8")
            self.assertIn("```", content)

    def test_manifest_lists_technical_documents(self):
        manifest = (KB_DIR / "README.md").read_text(encoding="utf-8")
        for document in TECHNICAL_DOCUMENTS:
            self.assertIn(document, manifest)


if __name__ == "__main__":
    unittest.main()
