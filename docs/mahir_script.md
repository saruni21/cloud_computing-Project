# Mahir's Script — Code Walkthrough + Results (~2 min)

**Cloud Warriors | CS4296 Cloud Computing | CityU Hong Kong**

---

## [0:00–0:20] — Repo Structure

**Screen: Terminal at project root — run `ls`**

"The project has four main parts: `src` for all the code, `data` for the knowledge base catalogue, `results` where test output goes, and `docs` for the report and this script. Two files in `src` do all the work — `lambda_function.py` is the security pipeline, and `test_suite.py` is how we measured it."

---

## [0:20–1:00] — lambda_function.py

**Screen: Open `src/lambda_function.py`, scroll to `PromptInjectionFilter`**

"This is Layer 2 — the input filter. It has two checks. First, regex: it catches standard patterns like 'ignore all previous instructions' or 'system override'. Second, typoglycemia fuzzy matching — this checks if a word is an anagram of a dangerous keyword with the same first and last letter. So `i-g-n-r-o-e` is caught as a scrambled version of `ignore`."

**Scroll down to `get_confidence_score`**

"This is Layer 4 — the hallucination check. Inspired by SelfCheckGPT. After the agent answers, we send the same query two more times with fresh session IDs, then compute trigram Jaccard similarity between all three responses. If the score is below 0.35, the answers are too inconsistent — we flag it and retry. If it still fails, we return a safe fallback. The HTML escaping at the end of `lambda_handler` is what produces those `&#x27;` entities you see in the output."

---

## [1:00–2:00] — Test Results

**Screen: Scroll through terminal output — start at Config 1 INJECTION, end at SUMMARY TABLE**

"The test suite runs 21 tests across three configs. Config 1, base agent — look at tests 7, 8, 9. Three leaks. The JSON audit attack on test 8 returned the full system prompt verbatim — persona, instructions, everything. Config 2 adds guardrails — 8 out of 9 injections are now refused. But test 7, the French translation attack, still gets through. The guardrail topic filter doesn't catch indirect multilingual framing."

**Scroll to Config 3**

"Config 3, full pipeline. Tests 1, 2, 3, 4, and 8 — all BLOCKED in under 1.3 seconds. Those never reach Bedrock at all. The remaining four get safe responses or confidence fallbacks. Zero leaks. The trade-off is in the summary table — legitimate queries take around 19 seconds through the full pipeline versus 2.5 seconds on the base agent. That's the cost of the SelfCheckGPT sampling loop making three Bedrock calls per request."

---

## Before You Record

- Terminal font: **18pt** (Terminal → Settings → Font Size)
- Scroll slowly — pause on each section header
- Zoom `lambda_function.py` to **125%** so class names are readable
- Pre-scroll terminal output to Config 1 before you hit record
