# PRD: 요약비서 (AI 유튜브·PDF 요약 서비스)

## 1. 개요
릴리스(lilys.ai)처럼, 사용자가 YouTube 영상 링크 또는 PDF 파일을 입력하면 AI가 핵심 내용을
자동으로 요약해주는 웹 서비스. Aiffel Main Quest 1 과제로 기획·개발한다.

## 2. 문제 정의
- 강의 영상, 세미나 녹화본, 리포트/논문 PDF 등은 분량이 길어 전체를 다 보거나 읽기 어렵다.
- 핵심만 빠르게 파악하고, 필요할 때만 원본의 해당 구간(타임스탬프)으로 돌아가고 싶다.
- 이 서비스는 긴 영상/문서를 짧은 시간 안에 "한줄 요약 + 핵심 포인트 + (영상의 경우) 구간별
  타임스탬프 요약" 형태로 압축해 제공함으로써 이 문제를 해결한다.

## 3. 타겟 유저
- 강의·세미나 영상을 복습해야 하는 학생/수강생
- 다수의 리포트·논문 PDF를 훑어봐야 하는 직장인, 리서처
- 유튜브 콘텐츠를 빠르게 스크리닝하고 싶은 일반 사용자

## 4. 핵심 기능 (MVP)
1. **YouTube 요약 생성**: YouTube URL을 입력하면 자막을 추출해 AI가 한줄 요약, 핵심 포인트
   (5~8개), 타임스탬프 기반 챕터 요약을 생성한다.
2. **PDF 요약 생성**: PDF 파일을 업로드하면 텍스트를 추출해 AI가 한줄 요약과 핵심 포인트를
   생성한다.
3. **요약 히스토리 목록 조회**: 지금까지 생성한 요약들을 최신순으로 목록에서 확인한다.
4. **요약 상세 조회**: 목록에서 항목을 선택하면 전체 요약 내용(한줄요약/핵심포인트/챕터)을
   상세 화면(또는 패널)에서 확인한다.
5. **요약 삭제**: 더 이상 필요 없는 요약 기록을 히스토리에서 삭제한다.

### MVP 제외 범위 (Out of scope)
- 자막이 없는 영상의 음성 인식(STT) 처리
- 로그인/회원가입 및 유저별 데이터 분리
- 요약 결과 공유/내보내기 기능

## 5. 화면 구성
1. **요약 생성 화면 (홈)**
   - 탭: "YouTube 링크" / "PDF 업로드"
   - 입력 폼 + 요약 요청 버튼, 로딩 상태 표시
   - 생성 완료 시 한줄요약/핵심포인트/(영상)챕터를 결과 카드로 표시
2. **히스토리 화면**
   - 저장된 요약 목록 (제목, 종류, 생성일 표시)
   - 항목 클릭 시 상세 내용 조회
   - 항목별 삭제 버튼

## 6. 데이터 구조
Firebase Firestore `summaries` 컬렉션, 문서 스키마:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | string | Firestore 자동 문서 ID |
| source_type | "youtube" \| "pdf" | 입력 종류 |
| source_title | string | 영상 제목 또는 PDF 파일명 |
| source_ref | string | YouTube URL 또는 원본 파일명 |
| one_line_summary | string | 한줄 요약 |
| key_points | string[] | 핵심 포인트 목록 |
| chapters | { start_seconds: number, title: string, summary: string }[] \| null | 타임스탬프 챕터 요약 (YouTube만) |
| created_at | timestamp | 생성 시각 |

## 7. 사용 기술
- Frontend: HTML/CSS/JavaScript (정적 파일, Vercel에서 직접 서빙)
- Backend: FastAPI (Python), Vercel Python 서버리스 함수로 배포
- LLM: Anthropic Claude API
- YouTube 자막 추출: youtube-transcript-api
- PDF 텍스트 추출: pypdf
- DB: Firebase Firestore
- 배포: Vercel
