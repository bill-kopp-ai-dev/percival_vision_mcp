import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.vision_model_catalog import (  # noqa: E402
    find_alternatives,
    get_catalog_metadata,
    get_model_card,
    list_model_cards,
    load_catalog,
    normalize_task_type,
)


class TestVisionModelCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_catalog(use_cache=False)

    def test_catalog_schema_and_metadata(self) -> None:
        metadata = get_catalog_metadata(self.catalog)
        self.assertEqual(metadata["schema_version"], "2.0")
        self.assertEqual(metadata["provider"], "venice.ai")
        self.assertGreater(metadata["model_count"], 0)
        self.assertIn("general_vision", metadata["supported_task_types"])

    def test_task_filters_and_normalization(self) -> None:
        general_cards = list_model_cards("general_vision", catalog=self.catalog)
        ocr_cards = list_model_cards(normalize_task_type("read_text"), catalog=self.catalog)
        self.assertTrue(general_cards)
        self.assertTrue(ocr_cards)
        self.assertTrue(all("general_vision" in card["task_types"] for card in general_cards))
        self.assertTrue(all("ocr" in card["task_types"] for card in ocr_cards))

    def test_card_lookup_and_alternatives(self) -> None:
        card = get_model_card("openai-gpt-4o-mini-2024-07-18", catalog=self.catalog)
        self.assertIsNotNone(card)
        assert card is not None
        self.assertIn("general_vision", card["task_types"])
        self.assertIn("cost_estimation", card)

        alternatives = find_alternatives(
            model_id="openai-gpt-4o-mini-2024-07-18",
            task_type="general_vision",
            max_results=3,
            catalog=self.catalog,
        )
        self.assertLessEqual(len(alternatives), 3)
        self.assertTrue(all(alt["id"] != "openai-gpt-4o-mini-2024-07-18" for alt in alternatives))


if __name__ == "__main__":
    unittest.main()
