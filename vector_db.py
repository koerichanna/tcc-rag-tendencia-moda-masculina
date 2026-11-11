"""Acesso ao ChromaDB e busca híbrida das tendências.

Cada documento é guardado em duas formas:
- o texto que vira vetor (`documents`): só termo, categoria, estilo e descrição da peça;
- o texto completo entregue ao LLM (metadado `texto_completo`): inclui risco, score e os números
  do Google Trends.
Os números e rótulos repetidos em todos os documentos atrapalhavam a busca vetorial; separar as
duas formas foi o que mais melhorou a recuperação (docs/avaliacao_rag.md).
"""
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import chromadb

import busca
import embeddings

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
CANDIDATOS = 10  # quantos resultados de cada busca entram na fusão

# Um cliente por processo: abrir o banco a cada consulta deixava a busca lenta e instável.
@lru_cache(maxsize=1)
def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_trends_collection():
    """Coleção do modelo de embedding configurado (EMBEDDING_MODELO, ver embeddings.py)."""
    modelo = embeddings.modelo_configurado()
    return get_chroma_client().get_or_create_collection(
        name=embeddings.nome_colecao(modelo),
        embedding_function=embeddings.funcao_embedding(modelo),
        metadata={"description": "Tendências de moda masculina", "modelo_embedding": modelo},
    )

def _documento(doc_id, texto_busca, meta):
    return {"id": doc_id, "documento": meta.get("texto_completo", texto_busca), "metadados": meta}

def buscar(query: str, n_results: int = 3, where: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Busca híbrida: junta o ranking vetorial e o BM25 por Reciprocal Rank Fusion."""
    colecao = get_trends_collection()
    filtro = {"where": where} if where else {}

    # Todos os documentos do filtro (a base tem dezenas, não milhares): alimentam o BM25.
    todos = colecao.get(include=["documents", "metadatas"], **filtro)
    if not todos["ids"]:
        return []
    por_id = {i: (d, m) for i, d, m in zip(todos["ids"], todos["documents"], todos["metadatas"])}

    densa = colecao.query(query_texts=[query], n_results=min(CANDIDATOS, len(por_id)), **filtro)["ids"][0]
    bm25 = busca.BM25(todos["documents"])
    lexical = [todos["ids"][i] for i in bm25.buscar(query, k=CANDIDATOS)]

    return [_documento(i, *por_id[i]) for i in busca.fundir_rankings(lexical, densa)[:n_results]]

def buscar_tendencias_similares(query: str, n_results: int = 3, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
    return buscar(query, n_results, {"categoria": categoria} if categoria else None)

def obter_tendencia(doc_id: str) -> Optional[Dict[str, Any]]:
    """Documento de uma tendência pelo id da base (usado no vínculo produto → tendência)."""
    resultado = get_trends_collection().get(ids=[doc_id], include=["documents", "metadatas"])
    if not resultado["ids"]:
        return None
    return _documento(resultado["ids"][0], resultado["documents"][0], resultado["metadatas"][0])
