"""Unit tests for document ETL processor.

These tests validate that we can turn an input file into chunk dicts with stable metadata.
They monkeypatch Unstructured partitioning/chunking for determinism.
"""

import os

# Set test environment variables BEFORE any backend imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "test-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://test-vault.vault.azure.net/")


def test_process_file_returns_chunks_with_metadata(monkeypatch):
    from backend.etl.processor import processor as doc_processor
    import backend.etl.processor as processor_module

    class DummyMeta:
        page_number = 3
        filetype = "text/plain"

    class DummyChunk:
        def __init__(self, text: str):
            self._text = text
            self.metadata = DummyMeta()

        def __str__(self) -> str:
            return self._text

    def fake_partition(*, file, file_filename, content_type, strategy):
        # Return a list of elements (type irrelevant because chunker is mocked)
        return ["elem-1", "elem-2"]

    def fake_chunk_by_title(elements, **kwargs):
        assert elements == ["elem-1", "elem-2"]
        return [DummyChunk("Hello world"), DummyChunk("Second chunk")]

    monkeypatch.setattr(processor_module, "partition", fake_partition)
    monkeypatch.setattr(processor_module, "chunk_by_title", fake_chunk_by_title)

    chunks = doc_processor.process_file(b"hello", filename="cogai-thread.txt", content_type="text/plain")

    assert isinstance(chunks, list)
    assert len(chunks) == 2
    assert chunks[0]["text"] == "Hello world"
    assert chunks[0]["metadata"]["filename"] == "cogai-thread.txt"
    assert chunks[0]["metadata"]["source"] == "unstructured_etl"
    assert chunks[0]["metadata"]["page_number"] == 3
    assert chunks[0]["metadata"]["filetype"] == "text/plain"
