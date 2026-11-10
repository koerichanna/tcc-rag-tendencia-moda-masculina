from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class CategoriaProduto(str, Enum):
    CAMISAS = "Camisas"
    CALCAS = "Calças"
    CAMISETAS = "Camisetas"
    CALCADOS = "Calçados"
    BERMUDAS = "Bermudas"
    JAQUETAS = "Jaquetas"


class CategoriaTendencia(str, Enum):
    CAMISAS = "Camisas"
    CALCAS = "Calças"
    CAMISETAS = "Camisetas"
    CALCADOS = "Calçados"
    BERMUDAS = "Bermudas"
    JAQUETAS = "Jaquetas"
    GERAL = "Geral"


class NivelRisco(str, Enum):
    BAIXO = "Baixo"
    MODERADO = "Moderado"
    ALTO = "Alto"


# Texto sem espaços nas pontas e com tamanho controlado.
Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
Preco = Annotated[float, Field(ge=0.0, le=100_000.0)]
Quantidade = Annotated[int, Field(ge=0, le=1_000_000)]
Score = Annotated[float, Field(ge=0.0, le=100.0)]


# Entrada: só aceita as categorias do enum. A resposta usa str porque o banco pode ter
# registros antigos ou criados pelo LLM com outras categorias.
class ProdutoCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: Nome = Field(..., examples=["Camisa de Linho Manga Curta"])
    categoria: CategoriaProduto = Field(..., examples=["Camisas"])
    preco_medio: Preco = Field(..., examples=[189.90])
    custo_aquisicao: Optional[Preco] = Field(0.0, examples=[85.00])
    quantidade_estoque: Quantidade = Field(0, examples=[15])
    estoque_minimo: Quantidade = Field(5, examples=[5])
    tendencia_score: Score = Field(0.0, examples=[85.5])


class ProdutoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: Optional[Nome] = None
    categoria: Optional[CategoriaProduto] = None
    preco_medio: Optional[Preco] = None
    custo_aquisicao: Optional[Preco] = None
    quantidade_estoque: Optional[Quantidade] = None
    estoque_minimo: Optional[Quantidade] = None
    tendencia_score: Optional[Score] = None


class ProdutoResponse(BaseModel):
    id: int
    nome: str
    categoria: str
    preco_medio: float
    custo_aquisicao: Optional[float] = None
    quantidade_estoque: int
    estoque_minimo: int
    tendencia_score: float
    data_atualizacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TendenciaCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    termo: Nome = Field(..., examples=["Calça Wide Leg"])
    categoria: CategoriaTendencia = Field(..., examples=["Calças"])
    score_relevancia: Score = Field(50.0, examples=[60.0])
    sazonalidade: Optional[str] = Field("Atemporal", max_length=50, examples=["Primavera/Verão"])
    nivel_risco: NivelRisco = Field(NivelRisco.MODERADO, examples=["Baixo"])
    descricao: Optional[str] = Field(None, max_length=2000, examples=["Calças de modelagem ampla em sarja."])
    fonte: Optional[str] = Field("Cadastro manual", max_length=100, examples=["Cadastro manual"])


class TendenciaResponse(BaseModel):
    id: int
    termo: str
    categoria: str
    score_relevancia: float
    sazonalidade: Optional[str] = None
    nivel_risco: str
    descricao: Optional[str] = None
    fonte: Optional[str] = None
    data_registro: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RecomendacaoBase(BaseModel):
    produto_id: Optional[int] = Field(None, gt=0)
    titulo: str = Field(..., min_length=2, max_length=200, examples=["Reforçar estoque de camisas de linho"])
    categoria: str = Field(..., max_length=100, examples=["Camisas"])
    acao_sugerida: str = Field(..., max_length=100, examples=["Aumentar Pedido"])
    justificativa: str = Field(..., min_length=2, max_length=5000,
                               examples=["Interesse de busca estável e estoque abaixo do mínimo."])
    nivel_prioridade: str = Field("Média", max_length=50, examples=["Alta"])


class RecomendacaoCreate(RecomendacaoBase):
    pass


class RecomendacaoResponse(RecomendacaoBase):
    id: int
    data_criacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConsultaRAGRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    # O texto vai para o prompt do LLM: limitar o tamanho controla custo e abuso.
    pergunta: str = Field(..., min_length=5, max_length=500,
                          examples=["Devo aumentar o estoque de jaquetas para o inverno?"])
    categoria: Optional[CategoriaTendencia] = Field(None, examples=["Jaquetas"])
    produto_id: Optional[int] = Field(None, gt=0, examples=[1])


class ConsultaRAGResponse(BaseModel):
    pergunta: str
    diagnostico: str
    acao_recomendada: str
    nivel_risco: str
    justificativa_explicavel: str
    fontes_consultadas: List[str] = []
    recomendacao_id: Optional[int] = None


class GerarTendenciasIARequest(BaseModel):
    tema: Optional[str] = Field("Tendências de Moda Masculina Atual", min_length=3, max_length=200,
                                examples=["Alfaiataria moderna e casual chic"])
