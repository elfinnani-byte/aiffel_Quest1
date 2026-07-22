import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

_URL_PATTERNS = [
    r"(?:v=)([0-9A-Za-z_-]{11})",
    r"youtu\.be/([0-9A-Za-z_-]{11})",
    r"shorts/([0-9A-Za-z_-]{11})",
    r"embed/([0-9A-Za-z_-]{11})",
]


def extract_video_id(url: str) -> str:
    for pattern in _URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("올바른 YouTube URL이 아닙니다.")


def fetch_transcript(video_id: str) -> list:
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
    except TranscriptsDisabled:
        raise ValueError("이 영상은 자막이 비활성화되어 있어 요약할 수 없습니다.")
    except VideoUnavailable:
        raise ValueError("영상을 찾을 수 없습니다. URL을 확인해주세요.")
    except RequestBlocked:
        raise ValueError(
            "YouTube가 서버 요청을 일시적으로 차단했습니다. 잠시 후 다시 시도해주세요."
        )
    except CouldNotRetrieveTranscript:
        raise ValueError("이 영상의 자막 정보를 가져올 수 없습니다.")

    transcript = None
    for lang in ("ko", "en"):
        try:
            transcript = transcript_list.find_manually_created_transcript([lang])
            break
        except NoTranscriptFound:
            continue
    if transcript is None:
        for lang in ("ko", "en"):
            try:
                transcript = transcript_list.find_generated_transcript([lang])
                break
            except NoTranscriptFound:
                continue
    if transcript is None:
        try:
            transcript = next(iter(transcript_list))
        except StopIteration:
            raise ValueError("이 영상에서 자막을 찾을 수 없습니다.")

    try:
        entries = transcript.fetch()
    except Exception:
        raise ValueError("자막을 불러오는 중 오류가 발생했습니다.")

    return _normalize_entries(entries)


def _normalize_entries(entries) -> list:
    normalized = []
    for entry in entries:
        if isinstance(entry, dict):
            normalized.append(
                {
                    "text": entry["text"],
                    "start": entry["start"],
                    "duration": entry.get("duration", 0),
                }
            )
        else:
            normalized.append(
                {
                    "text": entry.text,
                    "start": entry.start,
                    "duration": getattr(entry, "duration", 0),
                }
            )
    return normalized
