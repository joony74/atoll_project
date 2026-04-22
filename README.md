# COCO Study

COCO Study is a concept-first math learning AI.

## What it does

- analyzes a math problem into core concepts
- explains each concept in three layers
  1. concept explanation
  2. intuition explanation
  3. analogy or story explanation
- checks whether the learner actually understood
- rebuilds the explanation when understanding is weak
- stores knowledge, feedback, chat state, and dashboard stats as files

## Structure

```text
coco_study/
├─ app.py
├─ ui/
├─ engines/
├─ watch/
├─ knowledge/
├─ data/
├─ logs/
└─ config/
```

Runtime writes go to:

- source mode: the project directory
- packaged mode: `~/Documents/CocoAIStudy` by default

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Default free mode

COCO Study is configured to run in local free mode by default.
If a local Ollama endpoint is available, the main chat can use it as a no-cost local LLM.
Even if a remote endpoint is present in the environment, it will not be used unless you explicitly opt in.

## Optional local LLM support with Ollama

If you want to test a local no-cost conversational model first, you can connect Ollama:

```bash
ollama serve
ollama pull qwen2.5:7b
export COCO_LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434/api/chat
export COCO_LOCAL_LLM_MODEL=qwen2.5:7b
```

If you want the local LLM to participate in almost every main-chat turn during testing:

```bash
export COCO_MAIN_CHAT_LLM_ALWAYS=1
```

If you want to temporarily disable the local main-chat LLM and fall back to the rule engine only:

```bash
export COCO_ENABLE_MAIN_CHAT_LLM=0
```

## Optional remote LLM support

If you want to wire in an external LLM later:

```bash
pip install -r requirements-llm.txt
export COCO_ALLOW_REMOTE_LLM=1
export OPENAI_API_KEY=...
```

The current MVP works without paid LLM usage and falls back to local heuristic concept analysis and template lessons.

## MVP flow

1. 입력한 문제를 개념 분석
2. 3단계 설명 생성
3. 사용자의 이해도 답변 수집
4. 이해 부족 시 재설명
5. 피드백 저장 및 watch 폴더 반영
6. 대시보드에서 성장 상태 확인

## Sample data

- `knowledge/concepts/*.json`
- `knowledge/index/concepts_index.json`
- `watch/inbox/sample_concept_note.txt`

## Build desktop app

```bash
./build_macos_app.sh
```
