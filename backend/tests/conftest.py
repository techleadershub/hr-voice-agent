"""Test setup: stub heavy production deps so route-level tests can load
backend.main without requiring openai / langchain / langgraph / qdrant /
sentence-transformers to be installed.

Anything in this file runs before test collection picks up the test modules.
"""

import os
import sys
import types
from unittest.mock import MagicMock

# Make the repo importable as `backend.*`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _install_stub(name: str, **attrs):
    """Register a fake module under `name` if it isn't already importable."""
    if name in sys.modules:
        return
    try:
        __import__(name)
        return
    except ImportError:
        pass
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod


# --- third-party deps that backend imports ---
_install_stub("openai", AsyncOpenAI=MagicMock(), OpenAI=MagicMock())

# langchain_openai.ChatOpenAI is used at *import time* inside agent modules
_install_stub("langchain_openai", ChatOpenAI=MagicMock())

# langchain_core submodules
_install_stub("langchain_core")
_install_stub(
    "langchain_core.prompts",
    ChatPromptTemplate=MagicMock(),
)
_install_stub(
    "langchain_core.output_parsers",
    PydanticOutputParser=MagicMock(),
    StrOutputParser=MagicMock(),
)

# langchain.text_splitter
_install_stub("langchain")
_install_stub("langchain.text_splitter", RecursiveCharacterTextSplitter=MagicMock())

# langgraph
_install_stub("langgraph")


class _StubStateGraph:
    def __init__(self, *_a, **_kw): pass
    def add_node(self, *_a, **_kw): pass
    def add_edge(self, *_a, **_kw): pass
    def set_entry_point(self, *_a, **_kw): pass
    def compile(self, *_a, **_kw):
        return MagicMock()


_install_stub("langgraph.graph", StateGraph=_StubStateGraph, END="__end__")

# sentence-transformers / qdrant — used by services that main.py imports
_install_stub("sentence_transformers", SentenceTransformer=MagicMock())


class _StubPointStruct:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# qdrant_client must be a *package* so `from qdrant_client.http import models` works
def _install_qdrant_stubs():
    if "qdrant_client" in sys.modules:
        return
    try:
        __import__("qdrant_client")
        return
    except ImportError:
        pass
    pkg = types.ModuleType("qdrant_client")
    pkg.__path__ = []  # mark as package
    pkg.QdrantClient = MagicMock()
    sys.modules["qdrant_client"] = pkg

    http = types.ModuleType("qdrant_client.http")
    http.__path__ = []
    sys.modules["qdrant_client.http"] = http

    models = types.ModuleType("qdrant_client.http.models")
    models.Distance = MagicMock(COSINE="cosine")
    models.VectorParams = MagicMock()
    models.PointStruct = _StubPointStruct
    sys.modules["qdrant_client.http.models"] = models
    http.models = models

    top_models = types.ModuleType("qdrant_client.models")
    top_models.Distance = models.Distance
    top_models.VectorParams = models.VectorParams
    top_models.PointStruct = _StubPointStruct
    sys.modules["qdrant_client.models"] = top_models


_install_qdrant_stubs()
