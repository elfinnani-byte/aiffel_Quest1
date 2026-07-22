from typing import List, Optional

from pydantic import BaseModel


class Chapter(BaseModel):
    start_seconds: float
    title: str
    summary: str


class YoutubeSummarizeRequest(BaseModel):
    url: str


class SummaryRecord(BaseModel):
    id: str
    source_type: str
    source_title: str
    source_ref: str
    one_line_summary: str
    key_points: List[str]
    chapters: Optional[List[Chapter]] = None
    created_at: Optional[str] = None


class SummaryListItem(BaseModel):
    id: str
    source_type: str
    source_title: str
    one_line_summary: str
    created_at: Optional[str] = None
