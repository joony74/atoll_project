"""Session orchestration layer contracts.

Owns:
- current document session
- current active problem
- progression cursor
- handoff between router and engines

Should not:
- parse OCR directly
- compute math answers directly
"""

