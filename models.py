from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import true as sa_true
from sqlalchemy.orm import relationship

from database import Base


class ProdutoModel(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), index=True, nullable=False)
    categoria = Column(String(100), index=True, nullable=False)
    preco_medio = Column(Float, nullable=False, default=0.0)
    custo_aquisicao = Column(Float, nullable=True, default=0.0)
    quantidade_estoque = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=5)
    tendencia_score = Column(Float, nullable=False, default=0.0)
    data_atualizacao = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    recomendacoes = relationship("RecomendacaoModel", back_populates="produto", cascade="all, delete-orphan")


class TendenciaModel(Base):
    __tablename__ = "tendencias"
    __table_args__ = (UniqueConstraint("codigo", name="uq_tendencias_codigo"),)

    id = Column(Integer, primary_key=True, index=True)
    # id do registro em data/market_trends.json; vazio para tendências criadas pela API
    codigo = Column(String(50), nullable=True)
    termo = Column(String(150), index=True, nullable=False)
    categoria = Column(String(100), index=True, nullable=False)
    score_relevancia = Column(Float, nullable=False, default=50.0)
    sazonalidade = Column(String(50), nullable=True)
    nivel_risco = Column(String(50), nullable=False, default="Moderado")
    descricao = Column(Text, nullable=True)
    fonte = Column(String(100), nullable=True, default="Análise de Mercado / Redes")
    data_registro = Column(DateTime(timezone=True), server_default=func.now())


class RecomendacaoModel(Base):
    __tablename__ = "recomendacoes"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True)
    titulo = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=False)
    acao_sugerida = Column(String(100), nullable=False)
    justificativa = Column(Text, nullable=False)
    nivel_prioridade = Column(String(50), nullable=False, default="Média")
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    produto = relationship("ProdutoModel", back_populates="recomendacoes")


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nome_usuario = Column(String(50), unique=True, nullable=False)
    senha_hash = Column(String(100), nullable=False)
    # admin: gerencia usuários; usuario: usa a plataforma
    perfil = Column(String(20), nullable=False, default="usuario", server_default="usuario")
    # Desativar em vez de apagar mantém o histórico e corta o acesso na hora.
    ativo = Column(Boolean, nullable=False, default=True, server_default=sa_true())
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
