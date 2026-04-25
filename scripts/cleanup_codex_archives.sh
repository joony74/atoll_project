#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_DIR="${CODEX_ARCHIVE_DIR:-$HOME/.codex/archived_sessions}"
BACKUP_ROOT="${CODEX_ARCHIVE_BACKUP_ROOT:-$HOME/codex_archived_sessions_backup}"
THRESHOLD_GB="${CODEX_ARCHIVE_THRESHOLD_GB:-2}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/cleanup_codex_archives.sh [--dry-run] [--threshold-gb N]

Moves large Codex archived session logs out of ~/.codex/archived_sessions when
the folder exceeds the threshold. Files are moved to:

  ~/codex_archived_sessions_backup/YYYYmmdd_HHMMSS/

Environment overrides:
  CODEX_ARCHIVE_DIR             Archive directory to scan
  CODEX_ARCHIVE_BACKUP_ROOT     Backup root directory
  CODEX_ARCHIVE_THRESHOLD_GB    Threshold in GB, default 2
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --threshold-gb)
      THRESHOLD_GB="${2:-}"
      if [[ -z "$THRESHOLD_GB" ]]; then
        echo "Missing value for --threshold-gb" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! "$THRESHOLD_GB" =~ ^[0-9]+$ ]] || [[ "$THRESHOLD_GB" -lt 1 ]]; then
  echo "Threshold must be a positive integer GB value." >&2
  exit 2
fi

if [[ ! -d "$ARCHIVE_DIR" ]]; then
  echo "Archive directory does not exist: $ARCHIVE_DIR"
  exit 0
fi

threshold_kb=$((THRESHOLD_GB * 1024 * 1024))
current_kb="$(du -sk "$ARCHIVE_DIR" | awk '{print $1}')"

echo "Codex archive directory: $ARCHIVE_DIR"
echo "Current size: $(du -sh "$ARCHIVE_DIR" | awk '{print $1}')"
echo "Threshold: ${THRESHOLD_GB}GB"

if (( current_kb <= threshold_kb )); then
  echo "No cleanup needed."
  exit 0
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
backup_dir="$BACKUP_ROOT/$timestamp"
remaining_kb="$current_kb"
moved_count=0

echo "Cleanup needed. Moving largest archived session files until under threshold."
if (( DRY_RUN == 1 )); then
  echo "Dry run: no files will be moved."
else
  mkdir -p "$backup_dir"
fi

while IFS=$'\t' read -r size_kb file_path; do
  [[ -n "$file_path" ]] || continue

  if (( remaining_kb <= threshold_kb )); then
    break
  fi

  file_name="$(basename "$file_path")"
  human_size="$(du -sh "$file_path" | awk '{print $1}')"
  echo "Move: $human_size $file_name"

  if (( DRY_RUN == 0 )); then
    mv "$file_path" "$backup_dir/"
  fi

  remaining_kb=$((remaining_kb - size_kb))
  moved_count=$((moved_count + 1))
done < <(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name '*.jsonl' -print0 \
  | xargs -0 du -sk 2>/dev/null \
  | sort -rn)

if (( moved_count == 0 )); then
  echo "No .jsonl files found to move."
  exit 0
fi

if (( DRY_RUN == 1 )); then
  projected_mb=$((remaining_kb / 1024))
  echo "Dry run complete. Projected remaining size: ${projected_mb}MB"
else
  echo "Moved $moved_count file(s) to: $backup_dir"
  echo "Remaining archive size: $(du -sh "$ARCHIVE_DIR" | awk '{print $1}')"
fi
