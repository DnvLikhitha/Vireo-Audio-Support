# CLAUDE.md - Vireo Audio Support Project

## STRICT RULES (from system prompt)

1. **NEVER** run git commit, git push, git add, or any git command that changes history or the index. I commit and push manually. After each phase, tell me what files changed and suggest a commit message, then STOP and wait.
2. Work one work package (WP) at a time. At the end of each, stop and wait for my "go ahead".
3. Do not write any code in this step.
4. Show real outputs and numbers, never summarise from memory. If you cannot verify something, say so.
5. Do not use an LLM for per-ticket classification at runtime.

Then reply with: (a) your understanding of the task in 8 lines or fewer, (b) the data traps you will handle, (c) any ambiguity you want to confirm, (d) your plan for WP1 only.

## DATA TRAPS TO HANDLE (in this order)

1. **Legacy timestamps.** For `source_system == legacy_fd`, `resolved_at` was rebuilt from a UTC log while other fields are IST. Add 5h30m to legacy `resolved_at`. Evidence from exploration: about 72% of legacy handle times were negative (median about -5.1h) before the fix and 0 negative after.
2. **Handle time** = `first_response_at` to `resolved_at` (policy section 10), not creation to resolution. Tier 2 handle time is in days and must never be ranked against Tier 1.
3. **CSAT blanks** = no response. Exclude from averages. Never treat as zero. Report response count per agent.
4. **Legacy currency.** Policy section 9 says legacy money uses a native unit. Exploration found no 100x difference in refund-to-order-value ratios between systems. Re-check on legacy refunds before Sep 2025 and document the result either way. Do not invent a conversion.
5. **Duplicates.** Policy section 9 says some legacy tickets were re-imported. Exact-key matching found none. About 70 rows share near-identical messages. Investigate and report, without claiming there are none.
6. **`transfers`** exists only in the current helpdesk. Blank for legacy means unknown, not zero.
7. **Missing `order_id` (~35% of tickets).** Fall back to `customer_id` + `product_sku`. About 614 of ~4,100 fallbacks match multiple orders. Flag these as ambiguous and do not silently pick one.
8. **Junk IVR transcripts (~40 tickets).** Exclude from text analysis only. Keep them in operational metrics.
9. **Roster** has one row per assignment with from/to dates. Join by agent_id and date range.
10. **Category tag** is set by an intake bot and only sometimes corrected. Do not treat it as root cause.

## SESSION STARTUP INSTRUCTION

At the start of every session, read:
- CLAUDE_CODE_BRIEF.md
- PRD.md
- TECHSTACK.md

This ensures you have the complete context for the Vireo Audio Support analytics project.