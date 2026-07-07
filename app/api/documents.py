import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.crud.document import create_document, get_documents_by_user_id
from app.models.user import User
from app.schemas.document import DocumentCreateResponse, DocumentListItem, DocType
from app.services.parsers.factory import parse_document
from app.services.storage import get_presigned_url, upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/parse",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def parse_document_endpoint(
    doc_type: DocType = Query(..., description="Тип документа"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/jpg", "application/pdf"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG or PDF files are allowed",
        )

    extension = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
    file_bytes = await file.read()

    try:
        parsed_data = parse_document(doc_type.value, file_bytes, file.filename, file.content_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    storage_key = upload_file(
        file_bytes=file_bytes,
        content_type=file.content_type or "application/octet-stream",
        user_id=current_user.id,
        extension=extension,
    )

    document = await create_document(
        db=db,
        user_id=current_user.id,
        doc_type=doc_type.value,
        file_storage_key=storage_key,
        file_bucket="airdos-documents",
        parsed_data=parsed_data,
    )
    await db.commit()

    file_url = get_presigned_url(storage_key)

    return DocumentCreateResponse(
        id=document.id,
        user_id=document.user_id,
        doc_type=document.doc_type,
        file_url=file_url,
        file_storage_key=document.file_storage_key,
        file_bucket=document.file_bucket,
        parsed_data=document.parsed_data,
        created_at=document.created_at,
    )


@router.get(
    "",
    response_model=list[DocumentListItem],
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    documents = await get_documents_by_user_id(db, current_user.id)

    return [
        DocumentListItem(
            id=doc.id,
            doc_type=doc.doc_type,
            file_url=get_presigned_url(doc.file_storage_key, doc.file_bucket),
            file_storage_key=doc.file_storage_key,
            file_bucket=doc.file_bucket,
            parsed_data=doc.parsed_data,
            created_at=doc.created_at,
        )
        for doc in documents
    ]
