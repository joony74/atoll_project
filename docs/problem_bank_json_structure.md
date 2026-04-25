# Problem Bank JSON Structure

The problem bank is stored as JSON shards plus a lightweight JSON index.
This keeps app startup fast: Coco can load the index first, then open the
full problem record only when the learner selects a problem.

## Directory Layout

```text
data/problem_bank/
  catalog.json
  schema/
    problem_bank_record.schema.json
    problem_bank_manifest.schema.json
  sources/
    competition_math/
      manifest.json
      index/problem_index.json
      shards/
        algebra/level_5.json
        geometry/level_3.json
        ...
```

## Record Shape

Each problem record has these top-level sections:

- `source`: dataset origin, original index, license, split.
- `content`: raw LaTeX problem and solution, plus plain search text.
- `answer`: extracted final answer, candidates, extraction method.
- `taxonomy`: domain, subject, level, concepts, tags.
- `structure`: flags for diagrams, Asymptote, tables, choices.
- `learning`: prerequisites, step outline, hints, common mistakes.
- `search`: searchable problem/solution text and keywords.
- `metadata`: created time, quality flags, review reasons.

The important design choice is that `solution_latex` is preserved exactly.
Coco can render or summarize it, but the source solution remains intact.

## Why Shards Instead Of One Big JSON File

One full JSON file is simple but makes the app read roughly all 12,500
records whenever it needs a list. Shards let us load only the needed subject
or level. The lightweight index contains only fields needed for search and
listing.

## Learning Engine Flow

1. Load `catalog.json`.
2. Load each bank's `index/problem_index.json`.
3. Filter by subject, level, concept, answer type, or rendering needs.
4. Open the shard only for selected problem IDs.
5. Use `content.solution_latex` as the trusted solution.
6. Generate Korean tutor explanation, hints, and follow-up practice from the
   normalized record.

## Runtime Adapter

The app reads the bank through `app.problem_bank.repository`.

- `list_banks()` returns catalog entries.
- `search_problems(...)` returns lightweight index rows only.
- `load_problem(problem_id)` opens the matching shard and returns the full record.
- `record_to_analysis(record)` converts a bank record into the same
  `structured_problem` and `solve_result` shape used by uploaded images.
- `record_to_document(record)` wraps that analysis in a study-document payload.

That last conversion is the bridge into the existing study chat engine. A bank
problem can be selected without creating an image file, while the chat still sees
the familiar `analysis.structured_problem` and `analysis.solve_result` fields.

## API Surface

The initial API endpoints are:

```text
GET  /problem-bank/banks
GET  /problem-bank/banks/{bank_id}/manifest
POST /problem-bank/search
GET  /problem-bank/problems/{problem_id}
GET  /problem-bank/problems/{problem_id}/analysis
GET  /problem-bank/problems/{problem_id}/document
```

The UI should call `/problem-bank/search` for list/search screens, then call
`/problem-bank/problems/{problem_id}/document` when the learner wants to open a
problem as a study item.

## Review Flags

Records can be usable even when they need review. For example, MATH records
with no `\\boxed{...}` final answer get:

```json
{
  "quality": {
    "solution_available": true,
    "final_answer_extracted": false,
    "needs_review": true,
    "review_reasons": ["missing_boxed_answer"]
  }
}
```
