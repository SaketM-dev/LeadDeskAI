"""Versioned knowledge article API. All writes create audit records; approval is explicit."""
import json
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers.v1_leads import require_api_token

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


class ArticleCreate(BaseModel):
    kind: Literal["course", "faq", "policy"]
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    body: Optional[str] = Field(default=None, min_length=1, max_length=20000)


@router.get("/documents", dependencies=[Depends(require_api_token)])
def list_articles(
    q: Optional[str] = Query(default=None, min_length=1, max_length=100),
    kind: Optional[Literal["course", "faq", "policy"]] = None,
    status_filter: Literal["approved", "draft", "archived", "all"] = Query(default="approved", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Search versioned articles; defaults to approved content only."""
    clauses = []
    params = {"limit": limit}
    if status_filter != "all":
        clauses.append("status = :article_status")
        params["article_status"] = status_filter
    if kind:
        clauses.append("kind = :kind")
        params["kind"] = kind
    if q:
        clauses.append("(title ILIKE :query OR body ILIKE :query)")
        params["query"] = f"%{q.strip()}%"
    where = " AND ".join(clauses) if clauses else "TRUE"
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(f"""
                SELECT id, kind, title, body, status, version, created_at, updated_at
                FROM public.knowledge_articles
                WHERE {where}
                ORDER BY updated_at DESC, id DESC
                LIMIT :limit
            """), params).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Knowledge base is unavailable. Apply the admissions workflow migration.")
    return {"data": [dict(row) for row in rows], "page": {"next_cursor": None}}


@router.post("/documents", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_token)])
def create_article(payload: ArticleCreate):
    """Create a draft and version record; draft facts are not approved for AI use."""
    title, body = payload.title.strip(), payload.body.strip()
    if not title or not body:
        raise HTTPException(status_code=422, detail="title and body cannot be blank.")
    try:
        with engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO public.knowledge_articles (kind, title, body, status, version)
                VALUES (:kind, :title, :body, 'draft', 1)
                RETURNING id, kind, title, body, status, version, created_at, updated_at
            """), {"kind": payload.kind, "title": title, "body": body}).mappings().one()
            connection.execute(text("""
                INSERT INTO public.knowledge_article_versions
                    (article_id, version, title, body, status)
                VALUES (:article_id, 1, :title, :body, 'draft')
            """), {"article_id": str(row["id"]), "title": title, "body": body})
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'knowledge_article.created', 'knowledge_article', :article_id, CAST(:details AS jsonb))
            """), {"article_id": str(row["id"]), "details": json.dumps({"version": 1, "actor": "shared_token"})})
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Article could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(row), "notice": "Saved as draft; it is not approved for AI use."}


@router.patch("/documents/{article_id}", dependencies=[Depends(require_api_token)])
def update_article(article_id: str, payload: ArticleUpdate):
    """Create a new draft version and preserve prior article versions."""
    try:
        parsed_id = str(UUID(article_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="article_id must be a valid UUID.")
    changes = payload.dict(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide title or body to create a new version.")
    for key, value in changes.items():
        if not value.strip():
            raise HTTPException(status_code=422, detail=f"{key} cannot be blank.")
        changes[key] = value.strip()
    try:
        with engine.begin() as connection:
            current = connection.execute(text("""
                SELECT id, kind, title, body, version
                FROM public.knowledge_articles WHERE id = :article_id FOR UPDATE
            """), {"article_id": parsed_id}).mappings().first()
            if current is None:
                raise HTTPException(status_code=404, detail="Knowledge article not found.")
            title = changes.get("title", current["title"])
            body = changes.get("body", current["body"])
            version = current["version"] + 1
            row = connection.execute(text("""
                UPDATE public.knowledge_articles
                SET title = :title, body = :body, status = 'draft', version = :version, updated_at = now()
                WHERE id = :article_id
                RETURNING id, kind, title, body, status, version, created_at, updated_at
            """), {"article_id": parsed_id, "title": title, "body": body, "version": version}).mappings().one()
            connection.execute(text("""
                INSERT INTO public.knowledge_article_versions
                    (article_id, version, title, body, status)
                VALUES (:article_id, :version, :title, :body, 'draft')
            """), {"article_id": parsed_id, "version": version, "title": title, "body": body})
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'knowledge_article.version_created', 'knowledge_article', :article_id, CAST(:details AS jsonb))
            """), {"article_id": parsed_id, "details": json.dumps({"version": version, "actor": "shared_token"})})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Article version could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(row), "notice": "New version saved as draft; approval is required before AI use."}


@router.post("/documents/{article_id}/approve", dependencies=[Depends(require_api_token)])
def approve_article(article_id: str):
    """Approve the current draft version. Production role authorization is not yet available."""
    try:
        parsed_id = str(UUID(article_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="article_id must be a valid UUID.")
    try:
        with engine.begin() as connection:
            current = connection.execute(text("""
                SELECT id, version, status FROM public.knowledge_articles
                WHERE id = :article_id FOR UPDATE
            """), {"article_id": parsed_id}).mappings().first()
            if current is None:
                raise HTTPException(status_code=404, detail="Knowledge article not found.")
            if current["status"] != "draft":
                raise HTTPException(status_code=409, detail="Only a draft article can be approved.")
            connection.execute(text("""
                UPDATE public.knowledge_article_versions
                SET status = 'archived'
                WHERE article_id = :article_id AND status = 'approved'
            """), {"article_id": parsed_id})
            connection.execute(text("""
                UPDATE public.knowledge_article_versions
                SET status = 'approved'
                WHERE article_id = :article_id AND version = :version
            """), {"article_id": parsed_id, "version": current["version"]})
            row = connection.execute(text("""
                UPDATE public.knowledge_articles
                SET status = 'approved', updated_at = now()
                WHERE id = :article_id
                RETURNING id, kind, title, body, status, version, created_at, updated_at
            """), {"article_id": parsed_id}).mappings().one()
            connection.execute(text("""
                INSERT INTO public.audit_events (actor_id, event_type, entity_type, entity_id, details)
                VALUES (NULL, 'knowledge_article.approved', 'knowledge_article', :article_id, CAST(:details AS jsonb))
            """), {"article_id": parsed_id, "details": json.dumps({"version": current["version"], "actor": "shared_token"})})
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Article approval could not be saved. Apply the admissions workflow migration.")
    return {"data": dict(row), "notice": "Current version approved. Shared-token access does not enforce an administrator role."}
