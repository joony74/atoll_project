# Problem Bank PDF Utilization

## Purpose

PDF documents can improve Coco's image/PDF recognition loop, but they should be treated as validation inputs, not as raw content to copy into the generated problem bank.

## Source Policy

- Keep third-party PDFs outside Git under `02.학습문제/_pdf_private/`.
- Store only source metadata, page hashes, OCR failure signatures, and normalization rules in Git.
- Do not redistribute downloaded PDFs, page images, copied problem text, or derived worksheets unless the source license clearly permits it.
- For sources that prohibit modification, redistribution, upload, or derivative works, use them only for private local OCR checks.

## Suggested PDF Roles

1. Reference-only source
   - Use page layout, unit sequencing, and problem-type distribution as high-level inspiration.
   - Do not copy problem text, numbers, diagrams, or answer keys.

2. Private OCR benchmark
   - User places a PDF locally.
   - Script renders pages to temporary images.
   - Coco runs OCR and solving.
   - Report keeps only pass/fail, page hash, recognized expression, and failure reason.

3. Public exam benchmark
   - Use only when redistribution and derivative use are allowed.
   - Prefer storing references and normalized templates over storing page images.

## Pipeline

1. Register PDF source metadata.
2. Render pages to image cache.
3. Segment page into question regions when possible.
4. Run `run_solve_pipeline` on each region or page.
5. Compare with an optional local answer key.
6. Save normalization failures into learned profiles.
7. Delete temporary page images unless explicitly kept for local debugging.

## Local Exact-Capture Workflow

When the goal is OCR/normalization training before release, use exact PDF captures only in ignored local folders:

```bash
venv_clean/bin/python scripts/build_private_pdf_problem_bank.py \
  --source all \
  --skai-per-grade 3 \
  --tile-rows 3 \
  --tile-cols 2 \
  --dpi 150 \
  --force-render \
  --manifest data/problem_bank/learned/coco_private_pdf_capture_manifest.json
```

This produces page images and problem-region tiles under `02.학습문제/05.문제은행/` and keeps downloaded PDFs under `02.학습문제/_pdf_private/`. Both folders are git-ignored.

## Curriculum Generation Rule

Generated Coco problems should be based on curriculum concepts and original templates. External PDFs may guide coverage, layout variation, and difficulty balance, but generated problem statements and diagrams must be newly created.

Do not generate 100 items by changing only the numbers in one template. A grade-level generated set must mix:

- expression, word, table, graph, geometry, and multi-step reasoning layouts where appropriate
- unit-specific problem forms from the current curriculum
- basic, application, and advanced tasks with different reading demands
- visual/table/PDF-like layouts that stress OCR differently
