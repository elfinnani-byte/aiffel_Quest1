import json

import firebase_admin
from firebase_admin import credentials, firestore

from backend.config import FIREBASE_SERVICE_ACCOUNT_JSON

_COLLECTION = "summaries"
_db = None


def _get_db():
    global _db
    if _db is not None:
        return _db

    if not FIREBASE_SERVICE_ACCOUNT_JSON:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.")

    if not firebase_admin._apps:
        service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def create_summary(data: dict) -> dict:
    db = _get_db()
    payload = dict(data)
    payload["created_at"] = firestore.SERVER_TIMESTAMP
    _, doc_ref = db.collection(_COLLECTION).add(payload)
    saved = doc_ref.get().to_dict()
    return _serialize(doc_ref.id, saved)


def list_summaries() -> list:
    db = _get_db()
    docs = (
        db.collection(_COLLECTION)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [_serialize(doc.id, doc.to_dict()) for doc in docs]


def get_summary(summary_id: str):
    db = _get_db()
    doc = db.collection(_COLLECTION).document(summary_id).get()
    if not doc.exists:
        return None
    return _serialize(doc.id, doc.to_dict())


def delete_summary(summary_id: str) -> bool:
    db = _get_db()
    doc_ref = db.collection(_COLLECTION).document(summary_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


def _serialize(doc_id: str, data: dict) -> dict:
    result = dict(data)
    result["id"] = doc_id
    created_at = result.get("created_at")
    if created_at is not None and hasattr(created_at, "isoformat"):
        result["created_at"] = created_at.isoformat()
    return result
