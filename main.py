import logging
import os
import time
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

import auth
import limites
import models
import rag_engine
import schemas
from database import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("projeto_moda")

app = FastAPI(
    title="API de Tendências de Moda Masculina",
    description="API com suporte a RAG para análise de tendências e recomendações no varejo de moda masculina",
    version="1.0.0"
)

@app.middleware("http")
async def monitorar_observabilidade(request: Request, call_next):
    inicio = time.time()
    response = await call_next(request)
    duracao_ms = (time.time() - inicio) * 1000
    response.headers["X-Response-Time-Ms"] = f"{duracao_ms:.2f}"
    if request.url.path.startswith(("/rag", "/ia", "/dashboard")):
        logger.info(f"Observabilidade: {request.method} {request.url.path} -> {response.status_code} ({duracao_ms:.2f}ms)")
    return response

app.state.limiter = limites.limiter
app.add_exception_handler(RateLimitExceeded, limites.limite_excedido)

# Em produção o frontend chama a API pelo mesmo domínio (/api), então CORS só é necessário
# no desenvolvimento, quando o Vite roda em outra porta. Autenticação vai no cabeçalho
# Authorization, sem cookies, por isso allow_credentials=False.
ORIGENS_CORS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_CORS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/", tags=["Status"])
def ler_raiz():
    return {
        "status": "online",
        "projeto": "Sistema RAG de Moda Masculina",
        "versao": "1.0.0"
    }

@app.get("/health", tags=["Status"])
def verificar_saude():
    return {
        "status": "healthy",
        "servico": "api-moda-rag",
        "ambiente": "operacional",
        "timestamp": time.time()
    }

@app.post("/auth/login", response_model=schemas.TokenResponse, tags=["Autenticação"])
@limites.limiter.limit(limites.LOGIN)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = auth.autenticar(db, form.username, form.password)
    if usuario is None:
        # Mesma mensagem para usuário inexistente e senha errada: não revela quais usuários existem.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": auth.criar_token(usuario.nome_usuario)}

@app.get("/auth/me", response_model=schemas.UsuarioResponse, tags=["Autenticação"])
def usuario_logado(usuario: models.UsuarioModel = Depends(auth.usuario_atual)):
    return usuario

@app.post("/produtos/", response_model=schemas.ProdutoResponse, status_code=status.HTTP_201_CREATED, tags=["Produtos"], dependencies=[Depends(auth.usuario_atual)])
def criar_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = models.ProdutoModel(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.get("/produtos/", response_model=List[schemas.ProdutoResponse], tags=["Produtos"])
def listar_produtos(categoria: str = None, db: Session = Depends(get_db)):
    query = db.query(models.ProdutoModel)
    if categoria:
        query = query.filter(models.ProdutoModel.categoria.ilike(f"%{categoria}%"))
    return query.all()

@app.get("/produtos/{produto_id}", response_model=schemas.ProdutoResponse, tags=["Produtos"])
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.ProdutoModel).filter(models.ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.put("/produtos/{produto_id}", response_model=schemas.ProdutoResponse, tags=["Produtos"], dependencies=[Depends(auth.usuario_atual)])
def atualizar_produto(produto_id: int, dados: schemas.ProdutoUpdate, db: Session = Depends(get_db)):
    produto = db.query(models.ProdutoModel).filter(models.ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    update_data = dados.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(produto, key, value)

    db.commit()
    db.refresh(produto)
    return produto

@app.delete("/produtos/{produto_id}", tags=["Produtos"], dependencies=[Depends(auth.usuario_atual)])
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.ProdutoModel).filter(models.ProdutoModel.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(produto)
    db.commit()
    return {"mensagem": f"Produto {produto_id} removido com sucesso"}

@app.post("/tendencias/", response_model=schemas.TendenciaResponse, status_code=status.HTTP_201_CREATED, tags=["Tendências"], dependencies=[Depends(auth.usuario_atual)])
def cadastrar_tendencia(tendencia: schemas.TendenciaCreate, db: Session = Depends(get_db)):
    db_tendencia = models.TendenciaModel(**tendencia.model_dump())
    db.add(db_tendencia)
    db.commit()
    db.refresh(db_tendencia)
    return db_tendencia

@app.get("/tendencias/", response_model=List[schemas.TendenciaResponse], tags=["Tendências"])
def listar_tendencias(categoria: str = None, db: Session = Depends(get_db)):
    query = db.query(models.TendenciaModel)
    if categoria:
        query = query.filter(models.TendenciaModel.categoria.ilike(f"%{categoria}%"))
    return query.order_by(models.TendenciaModel.score_relevancia.desc()).all()

@app.post("/recomendacoes/", response_model=schemas.RecomendacaoResponse, status_code=status.HTTP_201_CREATED, tags=["Recomendações"], dependencies=[Depends(auth.usuario_atual)])
def registrar_recomendacao(recomendacao: schemas.RecomendacaoCreate, db: Session = Depends(get_db)):
    db_rec = models.RecomendacaoModel(**recomendacao.model_dump())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec

@app.get("/recomendacoes/", response_model=List[schemas.RecomendacaoResponse], tags=["Recomendações"])
def listar_recomendacoes(limite: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return (
        db.query(models.RecomendacaoModel)
        .order_by(models.RecomendacaoModel.data_criacao.desc(), models.RecomendacaoModel.id.desc())
        .limit(limite)
        .all()
    )

@app.post("/rag/consultar", response_model=schemas.ConsultaRAGResponse, tags=["Motor RAG"])
@limites.limiter.limit(limites.LLM)
def consultar_assistente_rag(request: Request, solicitacao: schemas.ConsultaRAGRequest, db: Session = Depends(get_db)):
    return rag_engine.consultar_rag(
        pergunta=solicitacao.pergunta,
        categoria=solicitacao.categoria,
        produto_id=solicitacao.produto_id,
        db=db,
        salvar_historico=True
    )

@app.get("/dashboard/kpis", tags=["Dashboard"])
def obter_metricas_dashboard(db: Session = Depends(get_db)):
    total_produtos = db.query(models.ProdutoModel).count()
    total_tendencias = db.query(models.TendenciaModel).count()
    total_recomendacoes = db.query(models.RecomendacaoModel).count()

    estoque_baixo = db.query(models.ProdutoModel).filter(
        models.ProdutoModel.quantidade_estoque <= models.ProdutoModel.estoque_minimo
    ).count()

    top_tendencias = db.query(models.TendenciaModel).order_by(
        models.TendenciaModel.score_relevancia.desc()
    ).limit(5).all()

    tendencias_risco = {
        "Baixo": db.query(models.TendenciaModel).filter(models.TendenciaModel.nivel_risco == "Baixo").count(),
        "Moderado": db.query(models.TendenciaModel).filter(models.TendenciaModel.nivel_risco == "Moderado").count(),
        "Alto": db.query(models.TendenciaModel).filter(models.TendenciaModel.nivel_risco == "Alto").count(),
    }

    return {
        "total_produtos": total_produtos,
        "total_tendencias": total_tendencias,
        "total_recomendacoes": total_recomendacoes,
        "produtos_estoque_critico": estoque_baixo,
        "distribuicao_risco": tendencias_risco,
        "top_tendencias": [
            {
                "id": t.id,
                "termo": t.termo,
                "categoria": t.categoria,
                "score": t.score_relevancia,
                "risco": t.nivel_risco,
                "sazonalidade": t.sazonalidade
            }
            for t in top_tendencias
        ]
    }

@app.post("/ia/gerar-tendencias", tags=["Inteligência Artificial"], dependencies=[Depends(auth.usuario_atual)])
@limites.limiter.limit(limites.GERAR_TENDENCIAS)
def api_gerar_tendencias_ia(request: Request, solicitacao: schemas.GerarTendenciasIARequest = None, db: Session = Depends(get_db)):
    tema = solicitacao.tema if (solicitacao and solicitacao.tema) else "Tendências de Moda Masculina Atual"
    novas = rag_engine.gerar_novas_tendencias_com_ia(tema=tema, db=db)
    return {
        "mensagem": f"{len(novas)} tendências processadas",
        "tema": tema,
        "tendencias": novas
    }

@app.post("/ia/analisar-produto/{produto_id}", tags=["Inteligência Artificial"], dependencies=[Depends(auth.usuario_atual)])
@limites.limiter.limit(limites.LLM)
def api_analisar_produto_ia(request: Request, produto_id: int, db: Session = Depends(get_db)):
    resultado = rag_engine.analisar_produto_com_ia(produto_id=produto_id, db=db)
    if "erro" in resultado:
        raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado

@app.get("/ia/briefing-executivo", tags=["Inteligência Artificial"])
@limites.limiter.limit(limites.LLM)
def api_obter_briefing_executivo_ia(request: Request, db: Session = Depends(get_db)):
    return rag_engine.gerar_briefing_executivo_ia(db=db)


