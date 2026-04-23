# CocoAI Study

CocoAI Study는 pywebview 데스크톱 런처와 Streamlit UI를 조합한 수학 학습 앱입니다.
현재 프로젝트 기준 런타임은 `desktop_app.py -> app.py -> app/*` 구조로 동작합니다.

## Current Structure

```text
atoll_project/
├─ desktop_app.py        # 데스크톱 런처
├─ app.py                # Streamlit 진입점
├─ app/                  # 채팅, 분석, 엔진, 모델 로직
├─ assets/               # 로고와 앱 아이콘
├─ config/               # 설정 자산
├─ data/                 # 샘플/학습 데이터
├─ docs/                 # 설계 및 릴리즈 문서
├─ 02.학습문제/          # 수동 확인용 샘플 이미지
└─ build_macos_app.sh    # macOS 앱 번들 빌드
```

## Main Features

- 메인챗과 학습리스트 챗 분리
- 이미지 업로드와 화면 캡처 등록
- Ollama 기반 메인/학습 챗 응답
- 수학 문제 구조화와 풀이 파이프라인
- 세션 복원과 사이드바 점검 카드

## Run Locally

브라우저에서 바로 확인할 때:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

데스크톱 창으로 띄울 때는 `pywebview`가 추가로 필요합니다.

```bash
python3 desktop_app.py
```

## Ollama

로컬 Ollama를 붙여 메인챗과 학습챗을 함께 사용할 수 있습니다.

```bash
ollama serve
ollama pull qwen2.5:7b
export COCO_LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434/api/chat
export COCO_LOCAL_LLM_MODEL=qwen2.5:7b
```

필요하면 아래 플래그로 제어할 수 있습니다.

```bash
export COCO_MAIN_CHAT_LLM_ALWAYS=1
export COCO_ENABLE_MAIN_CHAT_LLM=1
export COCO_ENABLE_STUDY_CHAT_LLM=1
```

## Build

macOS 앱 번들:

```bash
./build_macos_app.sh
```

Windows 실험용 빌드 스크립트:

```bash
build_windows_exe.bat
```
