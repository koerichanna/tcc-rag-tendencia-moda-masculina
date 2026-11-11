"""Busca lexical (BM25) e fusão de rankings, usadas na busca híbrida de vector_db.py.

A busca vetorial acha a peça certa quando a pergunta usa outras palavras ("calça larga" → wide
leg); o BM25 acerta em cheio quando a pergunta repete o nome da tendência. Juntar as duas listas
por Reciprocal Rank Fusion deu o melhor resultado na avaliação (docs/avaliacao_rag.md).
"""
import math
import statistics
import unicodedata
from collections import Counter

# Palavras sem valor de busca; sem tirá-las o BM25 casaria "de", "para", "vale" etc.
PARADAS_TEXTO = (
    "a o as os de da do das dos e em no na nos nas um uma uns umas para por com sem que se ao aos "
    "é está estão ser tem têm ainda vale pena compensa devo boa bom bem vende vendem vendendo "
    "saída procura procurado alta tendência como mais muito qual quais isso esse essa"
)


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


PARADAS = set(_sem_acento(PARADAS_TEXTO).split())


def radical(palavra: str) -> str:
    """Reduz plural e gênero ("acolchoadas", "acolchoado" → "acolchoad"). Bem mais simples que um
    stemmer completo, mas resolve o caso mais comum em nomes de peças."""
    if len(palavra) > 4 and palavra.endswith("s"):
        palavra = palavra[:-1]
    if len(palavra) > 4 and palavra[-1] in "ao":
        palavra = palavra[:-1]
    return palavra


def tokenizar(texto: str):
    palavras = "".join(c if c.isalnum() else " " for c in _sem_acento(texto)).split()
    return [radical(p) for p in palavras if p not in PARADAS and len(p) > 1]


class BM25:
    """Okapi BM25: pontua documentos que repetem as palavras da pergunta, pesando as palavras raras."""

    def __init__(self, documentos, k1=1.5, b=0.75):
        self.docs = [Counter(tokenizar(d)) for d in documentos]
        self.tamanhos = [sum(d.values()) for d in self.docs]
        self.k1, self.b = k1, b
        self.media = statistics.fmean(self.tamanhos) if self.tamanhos else 0.0
        frequencia = Counter(p for d in self.docs for p in d)
        n = len(self.docs)
        self.idf = {p: math.log(1 + (n - f + 0.5) / (f + 0.5)) for p, f in frequencia.items()}

    def buscar(self, consulta: str, k: int = 3):
        """Índices dos k documentos com maior nota (só os que têm alguma palavra em comum)."""
        termos = tokenizar(consulta)
        notas = []
        for i, (contagem, tamanho) in enumerate(zip(self.docs, self.tamanhos)):
            nota = 0.0
            for t in termos:
                tf = contagem.get(t, 0)
                if tf:
                    nota += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * tamanho / self.media))
            if nota > 0:
                notas.append((nota, i))
        notas.sort(reverse=True)
        return [i for _, i in notas[:k]]


def fundir_rankings(*rankings, k=60):
    """Reciprocal Rank Fusion: soma 1/(k + posição) de cada lista. Não depende da escala das notas,
    então junta BM25 e similaridade vetorial sem calibração."""
    notas = {}
    for ranking in rankings:
        for posicao, doc_id in enumerate(ranking, start=1):
            notas[doc_id] = notas.get(doc_id, 0.0) + 1 / (k + posicao)
    return sorted(notas, key=notas.get, reverse=True)
