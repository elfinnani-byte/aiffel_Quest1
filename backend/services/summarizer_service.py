import json

import anthropic

from backend.config import ANTHROPIC_API_KEY

_MODEL_NAME = "claude-opus-4-8"
_MAX_CHARS = 400_000  # Claude 컨텍스트 한도 내에서의 안전장치

_YOUTUBE_SYSTEM_PROMPT = """다음은 유튜브 영상의 자막입니다. 자막을 바탕으로 제목 추정, 한줄 요약, \
핵심 포인트, 타임스탬프 챕터 요약을 만드세요.

핵심 포인트는 5~8개, 챕터는 자막의 시간 흐름에 맞춰 3~8개로 나눠주세요.
챕터의 start_seconds는 반드시 숫자(초 단위)로 작성하세요.
자막이 한국어가 아니더라도 모든 출력(제목, 요약, 핵심 포인트, 챕터 내용)은 반드시 한국어로 작성하세요.

one_line_summary, key_points, chapters.summary 텍스트에는 마크다운 인라인 서식을 활용하세요: \
중요한 키워드나 수치는 **굵게**, 고유명사/기술 용어는 `코드` 서식으로 표시하세요."""

_PDF_SYSTEM_PROMPT = """다음은 PDF 문서에서 추출한 텍스트입니다. 문서를 바탕으로 제목 추정, \
한줄 요약, 핵심 포인트를 만드세요.

핵심 포인트를 작성할 때 다음을 지켜주세요:
- 문서의 분량과 다루는 주제 수에 비례해서 개수를 정하세요. 짧은 문서는 5~8개, \
내용이 많고 여러 섹션/주제로 나뉜 문서는 10~20개까지 늘려서 모든 주요 섹션과 논지가 \
빠짐없이 반영되도록 하세요.
- 각 포인트는 한 문장으로 뭉뚱그리지 말고, 구체적인 수치·근거·예시·용어를 최대한 그대로 \
살려서 2~3문장 분량으로 충분히 설명하세요.
- 원문에서 중요하게 다뤄진 세부 내용(정의, 비교, 결론, 한계점 등)을 임의로 생략하지 마세요.

문서가 한국어가 아니더라도 모든 출력(제목, 요약, 핵심 포인트)은 반드시 한국어로 작성하세요.

one_line_summary, key_points 텍스트에는 마크다운 인라인 서식을 활용하세요: 중요한 키워드나 수치는 \
**굵게**, 고유명사/기술 용어는 `코드` 서식으로 표시하세요."""

_YOUTUBE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "one_line_summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_seconds": {"type": "number"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["start_seconds", "title", "summary"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "one_line_summary", "key_points", "chapters"],
    "additionalProperties": False,
}

_PDF_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "one_line_summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "one_line_summary", "key_points"],
    "additionalProperties": False,
}

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def summarize_youtube_transcript(transcript_entries: list) -> dict:
    lines = [f"[{int(e['start'])}] {e['text']}" for e in transcript_entries]
    transcript_text = _truncate("\n".join(lines))
    return _generate(
        system=_YOUTUBE_SYSTEM_PROMPT,
        user_content=f"자막 (형식: [시작초] 텍스트):\n{transcript_text}",
        schema=_YOUTUBE_SCHEMA,
    )


def summarize_document_text(document_text: str) -> dict:
    document_text = _truncate(document_text)
    return _generate(
        system=_PDF_SYSTEM_PROMPT,
        user_content=f"문서 내용:\n{document_text}",
        schema=_PDF_SCHEMA,
    )


def _generate(system: str, user_content: str, schema: dict) -> dict:
    client = _get_client()
    try:
        response = client.messages.create(
            model=_MODEL_NAME,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=system,
            output_config={"format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.RateLimitError:
        raise ValueError(
            "Claude API 사용량 한도를 초과했습니다. 잠시 후 다시 시도하거나 API 키의 "
            "요금제/크레딧을 확인해주세요."
        )
    except anthropic.AuthenticationError:
        raise ValueError("ANTHROPIC_API_KEY가 올바르지 않습니다. API 키를 확인해주세요.")
    except anthropic.PermissionDeniedError:
        raise ValueError("이 API 키는 해당 모델을 사용할 권한이 없습니다.")
    except anthropic.APIStatusError:
        raise ValueError("AI 요약 요청이 거부되었습니다. 잠시 후 다시 시도해주세요.")
    except anthropic.APIConnectionError:
        raise ValueError("AI 서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.")

    if response.stop_reason == "refusal":
        raise ValueError("AI가 이 요청에 대한 요약 생성을 거부했습니다.")

    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        raise ValueError("AI가 요약을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.")

    return json.loads(text)


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CHARS:
        return text
    return text[:_MAX_CHARS]
