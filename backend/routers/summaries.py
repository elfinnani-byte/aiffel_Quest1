from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import YoutubeSummarizeRequest
from backend.services import firestore_service, pdf_service, summarizer_service, youtube_service

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.post("/youtube")
def create_youtube_summary(payload: YoutubeSummarizeRequest):
    try:
        video_id = youtube_service.extract_video_id(payload.url)
        transcript = youtube_service.fetch_transcript(video_id)
        result = summarizer_service.summarize_youtube_transcript(transcript)

        record = {
            "source_type": "youtube",
            "source_title": result.get("title") or "제목 없음",
            "source_ref": payload.url,
            "one_line_summary": result.get("one_line_summary", ""),
            "key_points": result.get("key_points", []),
            "chapters": result.get("chapters"),
        }
        return firestore_service.create_summary(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/pdf")
async def create_pdf_summary(file: UploadFile = File(...)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    file_bytes = await file.read()
    try:
        text = pdf_service.extract_text(file_bytes)
        result = summarizer_service.summarize_document_text(text)

        record = {
            "source_type": "pdf",
            "source_title": result.get("title") or file.filename,
            "source_ref": file.filename,
            "one_line_summary": result.get("one_line_summary", ""),
            "key_points": result.get("key_points", []),
            "chapters": None,
        }
        return firestore_service.create_summary(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("")
def list_summaries():
    try:
        return firestore_service.list_summaries()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{summary_id}")
def get_summary(summary_id: str):
    try:
        summary = firestore_service.get_summary(summary_id)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if summary is None:
        raise HTTPException(status_code=404, detail="요약을 찾을 수 없습니다.")
    return summary


@router.delete("/{summary_id}")
def delete_summary(summary_id: str):
    try:
        deleted = firestore_service.delete_summary(summary_id)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="요약을 찾을 수 없습니다.")
    return {"deleted": True}
