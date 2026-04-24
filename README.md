# Multi-Layer Security Pipeline for AWS Bedrock Agents

A cloud-native security architecture that wraps an Amazon Bedrock AI agent with multiple defensive layers to protect against prompt injection, jailbreaking, data exfiltration, and hallucination.

---

## Architecture Overview

```
User Request
     │
     ▼
┌─────────────┐
│  Layer 1    │  AWS WAF — blocks malicious HTTP traffic, rate limiting, IP rules
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Layer 2    │  AWS Lambda (BedrockAgentSecurityBridge)
│  (Input)    │  — Prompt injection detection (regex + typoglycemia fuzzing)
│             │  — System prompt leak prevention
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Layer 3    │  Amazon Bedrock Agent + Guardrails
│             │  — Model-level guardrails (denied topics, misconduct filter)
│             │  — Retrieval-augmented generation via Knowledge Base
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Layer 4    │  AWS Lambda (BedrockAgentSecurityBridge)
│  (Output)   │  — SelfCheckGPT hallucination detection
│             │  — Output leak validation (API keys, system prompts)
│             │  — HTML escaping before delivery
└──────┬──────┘
       │
       ▼
  Final Response
```

---

## Security Layers

### Layer 1 — AWS WAF
- Filters malicious HTTP traffic before it reaches the application
- Rate limiting to mitigate DDoS attempts
- IP-based blocking rules

### Layer 2 — Input Validation (Lambda)
- Regex detection of known prompt injection patterns
- Typoglycemia fuzzing defense (e.g. detects `ignroe` as `ignore`)
- Blocks requests matching dangerous patterns with HTTP 403

### Layer 3 — Amazon Bedrock Guardrails
- Denied topic filtering: `system_prompt_exfiltration`, `security_bypass_or_jailbreak`, `credential_or_secret_exposure`
- Misconduct detection
- Knowledge base grounding to reduce hallucinations

### Layer 4 — Output Verification (Lambda)
- **SelfCheckGPT-inspired hallucination detection**: generates multiple independent samples and checks cross-sample consistency using trigram Jaccard similarity (SelfCheckGPT-Ngram)
- Responses below the confidence threshold (`0.75`) are retried up to 2 times
- Output scanned for leaked system prompts or API keys
- All output HTML-escaped before delivery

---

## Project Structure

```
.
├── src/
│   ├── lambda_function.py        # Layers 2 & 4 — security bridge Lambda (deployed to AWS)
│   ├── test_suite.py             # Full pipeline vs baseline comparison test suite
│   ├── base_agent.py             # Baseline test script (direct Bedrock, no security layers)
│   └── upload_knowledge_base.py  # Uploads IT asset catalogue to S3 + syncs Bedrock KB
├── data/
│   └── tech_available.csv        # Company IT asset catalogue (knowledge base source)
├── results/
│   ├── base_agent_results.json   # Baseline test results
│   └── test_results_*.json       # Timestamped full pipeline test results
├── docs/
│   ├── report_draft.md           # Full academic report
│   ├── video_script.md           # Demo video script
│   └── project_requirements.pdf  # Assignment specification
├── TODO.md
└── README.md
```

---

## Knowledge Base

The Bedrock agent is grounded in a company IT asset catalogue (`data/tech_available.csv`) containing available hardware, software, and accessories with their stock levels and support policies.

To upload and sync the knowledge base:
```bash
python src/upload_knowledge_base.py
```

---

## Running Tests

The test suite evaluates three configurations:
1. **Base agent** — no security layers
2. **Full pipeline** — all four layers active

```bash
python src/test_suite.py
```

Test categories:
- Prompt injection attempts (9 tests including multilingual/indirect attacks)
- XSS payloads (4 tests)
- Hallucination checks against the knowledge base (5 tests)
- Legitimate queries — should never be blocked (3 tests)

Results are saved to `results/test_results_<timestamp>.json`.

---

## Infrastructure

| Service | Purpose |
|---|---|
| AWS WAF | Layer 1 network filtering |
| AWS Lambda | Layers 2 & 4 security bridge |
| Amazon Bedrock Agent | Core AI agent (`PKVJXD2MSK`) |
| Bedrock Guardrails | Layer 3 model-level filtering |
| Bedrock Knowledge Base | RAG grounding for IT asset queries |
| S3 (`klaudprojekt`) | Knowledge base document storage |
| S3 (`cloud-warriors-logs-2026`) | Security event logs |
| CloudWatch + SNS | Alerting on injection attempts |
| EventBridge | Event routing for security events |

**Region:** `us-east-1`

---

## Team

Cloud Warriors — City University of Hong Kong
