"""Gestão de usuários (só administradores) e troca da própria senha.

Regra de segurança: o administrador não pode rebaixar, desativar nem excluir a própria conta.
Assim sempre sobra pelo menos um administrador ativo, quem está fazendo a alteração.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import auth
import limites
import models
import schemas
from database import get_db

router = APIRouter()


def _buscar(db: Session, usuario_id: int) -> models.UsuarioModel:
    usuario = db.get(models.UsuarioModel, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


def _proibir_na_propria_conta(alvo: models.UsuarioModel, admin: models.UsuarioModel, acao: str):
    if alvo.id == admin.id:
        raise HTTPException(status_code=400, detail=f"Você não pode {acao} a própria conta")


@router.get("/usuarios/", response_model=List[schemas.UsuarioDetalheResponse], tags=["Usuários"])
def listar_usuarios(db: Session = Depends(get_db), _: models.UsuarioModel = Depends(auth.exigir_admin)):
    return db.query(models.UsuarioModel).order_by(models.UsuarioModel.nome_usuario).all()


@router.post("/usuarios/", response_model=schemas.UsuarioDetalheResponse, status_code=status.HTTP_201_CREATED,
             tags=["Usuários"])
def criar_usuario(dados: schemas.UsuarioCreate, db: Session = Depends(get_db),
                  _: models.UsuarioModel = Depends(auth.exigir_admin)):
    if db.query(models.UsuarioModel).filter_by(nome_usuario=dados.nome_usuario).first():
        raise HTTPException(status_code=409, detail="Já existe um usuário com esse nome")
    usuario = models.UsuarioModel(
        nome_usuario=dados.nome_usuario,
        senha_hash=auth.gerar_hash(dados.senha),
        perfil=dados.perfil,
        ativo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioDetalheResponse, tags=["Usuários"])
def atualizar_usuario(usuario_id: int, dados: schemas.UsuarioUpdate, db: Session = Depends(get_db),
                      admin: models.UsuarioModel = Depends(auth.exigir_admin)):
    usuario = _buscar(db, usuario_id)
    if dados.perfil is not None and dados.perfil != usuario.perfil:
        _proibir_na_propria_conta(usuario, admin, "mudar o perfil da")
        usuario.perfil = dados.perfil
    if dados.ativo is not None and dados.ativo != usuario.ativo:
        _proibir_na_propria_conta(usuario, admin, "desativar")
        usuario.ativo = dados.ativo
    if dados.senha is not None:
        usuario.senha_hash = auth.gerar_hash(dados.senha)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/usuarios/{usuario_id}", tags=["Usuários"])
def excluir_usuario(usuario_id: int, db: Session = Depends(get_db),
                    admin: models.UsuarioModel = Depends(auth.exigir_admin)):
    usuario = _buscar(db, usuario_id)
    _proibir_na_propria_conta(usuario, admin, "excluir")
    db.delete(usuario)
    db.commit()
    return {"mensagem": f"Usuário {usuario.nome_usuario} excluído"}


@router.put("/auth/me/senha", tags=["Autenticação"])
@limites.limiter.limit(limites.LOGIN)
def trocar_minha_senha(request: Request, dados: schemas.TrocaSenhaRequest, db: Session = Depends(get_db),
                       usuario: models.UsuarioModel = Depends(auth.usuario_atual)):
    # Pede a senha atual para que um token esquecido numa máquina aberta não baste para tomar a conta.
    if not auth.senha_confere(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    usuario.senha_hash = auth.gerar_hash(dados.nova_senha)
    db.commit()
    return {"mensagem": "Senha alterada"}
