# Elementary 50k Bank Plan

## 목표

초등 코코엔진을 “어떤 초등 문제든 이 정도면 됨” 수준으로 끌어올리기 위해 50,000장 규모의 학습/검증 카드 풀을 만든다. 50,000장은 모두 같은 의미의 카드가 아니며, 실제 이미지 해석과 내부 풀이엔진 고도화를 분리해서 쌓는다.

## 카드 트랙

- 실제 PDF 캡처 카드: 15,000장
  - OCR, 문제 자르기, 다문항 분리, 표/도형/그래프 해석을 검증한다.
- 정규화 JSON 카드: 20,000장
  - 문제 문장, 수식, 답, 풀이, 유형 라우팅을 고도화한다.
- 템플릿 변형 카드: 15,000장
  - 검증된 구조의 유사 문제 생성, 풀이 검산, 회귀 테스트에 사용한다.

## 현재 시작점

- `03.학습문제` Toctoc 기준선: 720/720 통과
- `02.학습문제` Skai PDF: 148개 PDF, 412개 EDITE 이미지, 재검증 대기
- 외부 JSON 문제은행 후보: 53,320개
- 템플릿 변형 후보: 15,000개 manifest 생성 가능

## 실행

초기 폴더와 후보 manifest를 만든다.

```bash
venv_clean/bin/python scripts/prepare_elementary_50k_bank.py \
  --init-dirs \
  --build-template-manifest
```

리포트만 다시 계산한다.

```bash
venv_clean/bin/python scripts/prepare_elementary_50k_bank.py
```

결과 파일:

- `data/problem_bank/learned/elementary_50k_readiness_report.json`
- `data/problem_bank/elementary_50k/template_variants_manifest.json`

## 검증 승격 규칙

카드는 생성되거나 수집됐다는 이유만으로 verified가 되지 않는다.

- 실제 PDF 캡처: 코코 캡처 플로우에서 OK여야 한다.
- 정규화 JSON: 문제/풀이/답이 있고, 초등 커리큘럼 필터를 통과해야 한다.
- 템플릿 변형: 렌더링 후 풀이엔진 검산을 통과해야 한다.
- 중복률은 3% 이하로 유지한다.

## 다음 순서

1. `02.학습문제` Skai PDF를 코코 캡처 플로우로 재검증한다.
2. 검증 통과분만 actual PDF capture verified로 올린다.
3. 외부 JSON 문제은행에서 초등 적합 문제 20,000개를 필터링한다.
4. 템플릿 변형 후보 15,000개를 렌더링/풀이 검산한다.
5. 실제 PDF 소스를 추가해 actual capture verified 15,000장을 채운다.

## 시작 검증 기록

Skai 초등 PDF 50개 캡처 카드 smoke 검증을 먼저 돌렸다.

- 최초 기준: 37/50 OK, `answer_mismatch` 13건
- PDF bbox 문제문장 보정 후: 40/50 OK, `answer_mismatch` 0건
- 이슈 분류 보강 후: 41/50 OK, `solve_needs_review` 9건

남은 9건은 정답 비교 오류가 아니라 초1 시각/쓰기형 풀이 보강 대상이다. 예시는 `수를 두 가지 방법으로 쓰기`, `수를 세어 빈칸에 쓰기`, `묶지 않은 것의 수 세기`, `순서에 맞게 빈칸 채우기`다. 이 유형은 50,000장 준비 단계에서 별도 보강 큐로 누적하고, 템플릿/시각해석 엔진을 고친 뒤 같은 캡처 카드로 재검증한다.

## 50,000개 후보 파일 수집 결과

다음 명령으로 기존 수집 파일과 외부 문제은행, 생성 템플릿을 합쳐 50,000개 후보 파일 풀을 만들었다.

```bash
venv_clean/bin/python scripts/collect_elementary_50k_sources.py --clean --target 50000
```

출력 위치:

- `data/problem_bank/elementary_50k/00_collected/source_collection_manifest.json`
- `data/problem_bank/elementary_50k/00_collected/records.jsonl`
- `data/problem_bank/learned/elementary_50k_source_collection_report.json`

현재 구성:

- 실제 PDF/이미지 캡처 소스: 3,917개
- 외부 정규화 JSON 후보: 15,001개
- 초등 템플릿 후보: 31,082개
- 합계: 50,000개

기본 수집은 초등 안정화용이므로 외부 데이터의 `advanced`, `middle_high` 등 비초등 후보는 제외했다. 부족분은 초등 템플릿 reserve 후보로 채웠다. 실제 PDF/이미지는 원본을 복사하지 않고 symlink로 묶었고, JSON/템플릿 후보는 개별 카드 파일로 materialize했다.

## 50,000개 학습 루틴 결과

수집 후보를 바로 학습 완료로 보지 않고, 정적 품질 게이트를 통과한 뒤 다음 큐로 분배한다.

```bash
venv_clean/bin/python scripts/run_elementary_50k_learning_cycle.py --clean
```

산출물:

- `data/problem_bank/learned/elementary_50k_learning_report.json`
- `data/problem_bank/learned/coco_elementary_50k_learning_profile.json`
- `data/problem_bank/elementary_50k/queues/learned_ready.jsonl`
- `data/problem_bank/elementary_50k/queues/actual_capture_validation_queue.jsonl`
- `data/problem_bank/elementary_50k/queues/template_render_validation_queue.jsonl`

현재 결과:

- 총 50,000개 적재
- 정규화 JSON 학습 즉시 사용 가능: 15,001개
- 실제 캡처/템플릿 검증 대기: 34,999개
- 보류: 0개
- 중복 제외: 0개
- 비초등 외부 레코드: 0개
- 정규화 JSON 답 커버리지: 100%

이 상태는 `static_learning_complete_validation_queues_ready`다. 즉, 내부 라우팅/검색/정규화/유사문제 생성을 위한 정적 학습 큐는 완료됐고, 남은 일은 코코앱 실제 캡처 검증 큐와 템플릿 렌더/풀이 검산 큐를 순차로 돌려 verified로 승격하는 것이다.

## 앱 로더 연결

`coco_elementary_50k_learning_profile.json`은 문제 생성 프로필 로더에서 `elementary_50k` 요약으로 함께 로드된다. 따라서 코코 학습엔진 상태에서는 다음 값이 바로 보인다.

- 초등 50k 학습 큐: 50,000개
- 초등 50k 즉시 학습 완료: 15,001개
- 초등 50k 검증 대기: 34,999개

기존 `coco_problem_generation_profile.v1` 형식은 유지하고, 50k 프로필은 별도 요약으로 붙인다. 아직 actual capture와 template render 큐는 검증 대기 상태이므로, 앱 캡처 검증과 렌더/풀이 검산을 통과한 항목부터 verified로 승격한다.
