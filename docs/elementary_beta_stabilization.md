# Elementary Beta Stabilization

## 목적

초등 코코엔진을 베타 단계로 올리기 전에, PDF/캡처/문항 분리/인식/풀이 후보가 같은 기준으로 반복 검증되도록 고정한다. 이 문서는 “지금 잘 되는지”가 아니라 “새 자료를 추가해도 같은 품질을 유지하는지”를 확인하는 운영 기준이다.

## 현재 기준선

- 기준 자료: `03.학습문제/05.문제은행/01.초등`
- EDITE 이미지: 712장
- 코코 캡처 흐름 기준 카드: 720개
- 최신 기준선 리포트: `data/problem_bank/learned/coco_capture_flow_toctoc_03_elementary_summary.json`
- 현재 결과: 720개 통과, 검토 0개, 오류 0개

## 베타 게이트

현재 자료 1종 기준선:

- 검증 카드 500개 이상
- OK 비율 99% 이상
- 검토 비율 1% 이하
- 오류 비율 0%

초등 베타 후보:

- 서로 다른 초등 PDF 소스 3종 이상
- 검증 카드 5000개 이상
- 전체 OK 비율 95% 이상

초등 서비스 후보:

- 서로 다른 초등 PDF 소스 5종 이상
- 검증 카드 10000개 이상
- 전체 OK 비율 98% 이상

## 실행 명령

빠른 감사만 실행:

```bash
venv_clean/bin/python scripts/run_elementary_beta_stabilization.py
```

새 PDF 루트를 실제 캡처 흐름으로 검증:

```bash
venv_clean/bin/python scripts/run_elementary_beta_stabilization.py \
  --run-validation \
  --root "03.학습문제/05.문제은행/01.초등" \
  --batch-size 10 \
  --clean \
  --write-every-batch
```

코코앱에 10개씩 직접 등록하면서 확인:

```bash
venv_clean/bin/python scripts/run_elementary_beta_stabilization.py \
  --run-validation \
  --root "03.학습문제/05.문제은행/01.초등" \
  --batch-size 10 \
  --app-register \
  --restart-app-after-batch \
  --write-every-batch
```

결과 리포트:

- `data/problem_bank/learned/elementary_beta_stabilization_report.json`
- `data/problem_bank/learned/elementary_beta_capture_validation_report.json`

## 실패 분류

검증에서 문제가 생기면 다음 순서로 분류한다.

- `crop_or_non_problem_page`: 표지, 목차, 정답 페이지만 남았거나 문제 영역이 잘못 잘림
- `problem_split_error`: 한 페이지 안의 여러 문제가 잘못 분리됨
- `ocr_text_loss`: 핵심 문장, 숫자, 단위가 빠짐
- `korean_text_corruption`: 한글이 영어/기호로 깨짐
- `visual_relation_missed`: 그림, 표, 그래프, 도형의 관계를 못 읽음
- `answer_candidate_wrong`: 답 후보가 원본과 맞지 않음
- `topic_or_level_wrong`: 초등 라우터/단원/유형 분류가 틀림
- `slow_pipeline`: 풀이 또는 카드 생성 시간이 베타 허용 범위를 넘음

## 운영 루틴

1. 새 초등 PDF를 `03.학습문제/05.문제은행/01.초등/{학년}/PDF`에 넣는다.
2. 기존 자르기 규칙으로 `EDITE` 이미지를 만든다.
3. 표지, 목차, 정답 페이지만 있는 이미지를 제거한다.
4. `run_elementary_beta_stabilization.py --run-validation`으로 캡처 흐름 검증을 돌린다.
5. 리포트에서 review/error가 나온 문항만 엔진에 반영한다.
6. 같은 구간을 다시 돌려 통과하면 해당 소스를 `elementary_beta_config.json`의 `source_sets`에 추가한다.
7. 베타 게이트가 통과될 때까지 서로 다른 출처의 PDF를 반복 추가한다.

## 현재 판단

현재 초등 엔진은 “단일 PDF 소스 기준선”은 통과했다. 다만 베타 안정화 기준으로는 아직 독립 소스 수와 검증 카드 수가 부족하므로, 다음 단계는 새 초등 PDF 소스를 2종 이상 더 확보해 같은 루틴으로 돌리는 것이다.
