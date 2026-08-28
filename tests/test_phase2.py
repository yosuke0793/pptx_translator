import tempfile

from pptx_translator.cache.cache_manager import CacheManager
from pptx_translator.ocr.detector import OCRResultItem
from pptx_translator.ocr.target_classifier import TargetClassifier
from pptx_translator.ocr.text_grouper import TextGrouper


def test_cache_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir)
        cache.set_ocr("hash123", "japan", [{"text": "テスト", "bbox": [0, 0, 10, 10]}])
        res = cache.get_ocr("hash123", "japan")
        assert res is not None
        assert res[0]["text"] == "テスト"

        cache.set_translation("日本語", "ja", "en", "Japanese")
        assert cache.get_translation("日本語", "ja", "en") == "Japanese"


def test_text_grouper():
    item1 = OCRResultItem(text="解析", bbox=[10, 10, 50, 20], polygon=[], confidence=0.95)
    item2 = OCRResultItem(text="結果", bbox=[65, 10, 50, 20], polygon=[], confidence=0.95)
    grouper = TextGrouper()
    grouped = grouper.group([item1, item2])

    assert len(grouped) == 1
    assert grouped[0].text == "解析 結果"


def test_target_classifier():
    classifier = TargetClassifier()

    item_jp = OCRResultItem(text="応力分布", bbox=[0, 0, 10, 10], polygon=[], confidence=0.95)
    is_target, reason = classifier.is_target(item_jp)
    assert is_target

    item_low_conf = OCRResultItem(text="応力分布", bbox=[0, 0, 10, 10], polygon=[], confidence=0.50)
    is_target, reason = classifier.is_target(item_low_conf, min_confidence=0.90)
    assert not is_target
    assert "low_confidence" in reason

    item_math = OCRResultItem(text="x + y = 10", bbox=[0, 0, 10, 10], polygon=[], confidence=0.95)
    is_target, reason = classifier.is_target(item_math)
    assert not is_target
