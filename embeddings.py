"""Modelos de embedding usados pelo ChromaDB.

- "minilm-en": all-MiniLM-L6-v2, o padrão do ChromaDB. Treinado só com textos em inglês.
- "multilingue": paraphrase-multilingual-MiniLM-L12-v2 (50+ idiomas, inclusive português), em ONNX
  quantizado (118 MB). Roda com onnxruntime e tokenizers, sem PyTorch, então cabe na imagem ARM.
- "multilingue-fp32": o mesmo modelo sem quantização (470 MB), usado só na avaliação para medir
  quanto a quantização custa em qualidade.

O modelo da aplicação vem de EMBEDDING_MODELO. Cada modelo tem a própria coleção no ChromaDB
(os dois geram vetores de 384 dimensões, então misturá-los na mesma coleção não daria erro,
só resultados errados). A comparação entre os modelos está em docs/avaliacao_rag.md.
"""
import os
from functools import lru_cache
from typing import Any, Dict, List

import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

MODELO_PADRAO = "multilingue"
REPO_MULTILINGUE = "Xenova/paraphrase-multilingual-MiniLM-L12-v2"
TAMANHO_MAXIMO = 256  # tokens; as descrições da base têm bem menos que isso


def _baixar(arquivo: str) -> str:
    """Caminho local do arquivo do modelo. Na imagem Docker ele já vem baixado (ver Dockerfile)."""
    pasta = os.getenv("EMBEDDING_DIR")
    if pasta and os.path.exists(os.path.join(pasta, arquivo)):
        return os.path.join(pasta, arquivo)
    try:
        import truststore  # certificados do sistema, necessário atrás de proxy corporativo
        truststore.inject_into_ssl()
    except ImportError:
        pass
    from huggingface_hub import hf_hub_download
    return hf_hub_download(REPO_MULTILINGUE, arquivo)


class EmbeddingMultilingue(EmbeddingFunction[Documents]):
    def __init__(self, quantizado: bool = True):
        import onnxruntime
        from tokenizers import Tokenizer

        self.quantizado = quantizado
        self.tokenizer = Tokenizer.from_file(_baixar("tokenizer.json"))
        self.tokenizer.enable_truncation(TAMANHO_MAXIMO)
        self.tokenizer.enable_padding()
        modelo = "onnx/model_quantized.onnx" if quantizado else "onnx/model.onnx"
        self.sessao = onnxruntime.InferenceSession(_baixar(modelo), providers=["CPUExecutionProvider"])
        self.entradas = {e.name for e in self.sessao.get_inputs()}

    def __call__(self, input: Documents) -> Embeddings:
        codificados = self.tokenizer.encode_batch(list(input))
        ids = np.array([c.ids for c in codificados], dtype=np.int64)
        mascara = np.array([c.attention_mask for c in codificados], dtype=np.int64)
        alimentar = {"input_ids": ids, "attention_mask": mascara}
        if "token_type_ids" in self.entradas:
            alimentar["token_type_ids"] = np.zeros_like(ids)
        saida = self.sessao.run(None, alimentar)[0]  # (lote, tokens, 384)

        # Média dos vetores dos tokens reais (ignora o preenchimento), como no sentence-transformers.
        peso = mascara[..., None].astype(np.float32)
        media = (saida * peso).sum(axis=1) / np.clip(peso.sum(axis=1), 1e-9, None)
        normalizados = media / np.linalg.norm(media, axis=1, keepdims=True)
        return [v.astype(np.float32) for v in normalizados]

    @staticmethod
    def name() -> str:
        return "moda_multilingue_minilm"

    def get_config(self) -> Dict[str, Any]:
        return {"quantizado": self.quantizado}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "EmbeddingMultilingue":
        return EmbeddingMultilingue(quantizado=config.get("quantizado", True))


FABRICAS = {
    "minilm-en": ONNXMiniLM_L6_V2,
    "multilingue": lambda: EmbeddingMultilingue(quantizado=True),
    "multilingue-fp32": lambda: EmbeddingMultilingue(quantizado=False),
}


def modelo_configurado() -> str:
    modelo = os.getenv("EMBEDDING_MODELO", MODELO_PADRAO)
    if modelo not in FABRICAS:
        raise ValueError(f"EMBEDDING_MODELO inválido: {modelo}. Opções: {', '.join(FABRICAS)}")
    return modelo


@lru_cache(maxsize=None)
def funcao_embedding(modelo: str):
    return FABRICAS[modelo]()


def nome_colecao(modelo: str) -> str:
    return f"tendencias_moda_{modelo.replace('-', '_')}"


def modelos_disponiveis() -> List[str]:
    return list(FABRICAS)
