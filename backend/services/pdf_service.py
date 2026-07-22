import io

from pypdf import PdfReader


def extract_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception:
        raise ValueError("PDF 파일을 읽을 수 없습니다. 파일이 손상되지 않았는지 확인해주세요.")

    if reader.is_encrypted:
        raise ValueError("암호로 보호된 PDF는 지원하지 않습니다.")

    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages_text).strip()

    if not text:
        raise ValueError(
            "PDF에서 텍스트를 추출할 수 없습니다. 스캔 이미지로 된 PDF는 지원하지 않습니다."
        )

    return text
