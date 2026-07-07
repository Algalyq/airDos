import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


async def create_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    doc_type: str,
    file_storage_key: str,
    file_bucket: str,
    parsed_data: dict,
) -> Document:
    document = Document(
        user_id=user_id,
        doc_type=doc_type,
        file_storage_key=file_storage_key,
        file_bucket=file_bucket,
        parsed_data=parsed_data,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def get_documents_by_user_id(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document_by_id(
    db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
