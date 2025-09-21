from types import SimpleNamespace

from app.common.text_normalization import (
    NORMALIZATION_FORM,
    normalize_documents_nfc,
    normalize_to_nfc,
)


def test_normalize_documents_nfc_preserves_original_metadata():
    doc = SimpleNamespace(page_content="cafe\u0301", metadata={"source": "demo.txt"})

    normalized_docs = normalize_documents_nfc([doc])

    assert len(normalized_docs) == 1
    normalized_doc = normalized_docs[0]

    assert normalized_doc.page_content == "café"
    assert normalized_doc.metadata["source"] == "demo.txt"
    assert normalized_doc.metadata["original_page_content"] == "cafe\u0301"
    assert normalized_doc.metadata["normalization"] == NORMALIZATION_FORM
    assert normalized_doc.page_content != normalized_doc.metadata["original_page_content"]


def test_normalize_to_nfc_keeps_accented_words_distinct():
    combining_acute = "cafe\u0301"

    normalized = normalize_to_nfc(combining_acute)

    assert normalized == "café"
    assert normalized != "cafe"
    assert normalize_to_nfc("café") == "café"
    assert normalize_to_nfc("cafe") == "cafe"
