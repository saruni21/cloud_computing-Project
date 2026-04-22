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
- **SelfCheckGPT-inspired hallucination detection**: generates multiple independent samples and checks cross-sample consistency using Claude Haiku as a judge
- Responses below the confidence threshold (`0.75`) are retried up to 2 times
- Output scanned for leaked system prompts or API keys
- All output HTML-escaped before delivery

---

## Project Structure

```
.
├── lambda_function.py        # Layers 2 & 4 — security bridge Lambda
├── upload_knowledge_base.py  # Uploads IT asset catalogue to S3 + syncs Bedrock KB
├── test_suite.py             # Attack simulation and latency benchmarking
├── tech_available.csv        # Company IT asset catalogue (knowledge base source)
├── TODO.md                   # Project task tracker
└── README.md
```

---

## Knowledge Base

The Bedrock agent is grounded in a company IT asset catalogue (`tech_available.csv`) containing available hardware, software, and accessories with their stock levels and support policies.

To upload and sync the knowledge base:
```bash
# Fill in KNOWLEDGE_BASE_ID in upload_knowledge_base.py first
python upload_knowledge_base.py
```

---

## Running Tests

The test suite evaluates three configurations:
1. **Base agent** — no security layers
2. **Full pipeline** — all four layers active

```bash
# Fill in LAMBDA_URL in test_suite.py first
python test_suite.py
```

Test categories:
- Prompt injection attempts
- XSS payloads
- Hallucination checks against the knowledge base
- Legitimate queries (regression — should never be blocked)

Results are saved to `test_results.json`.

---

## Infrastructure

| Service | Purpose |
|---|---|
| AWS WAF | Layer 1 network filtering |
| AWS Lambda | Layers 2 & 4 security bridge |
| Amazon Bedrock Agent | Core AI agent (`PKVJXD2MSK`) |
| Bedrock Guardrails | Layer 3 model-level filtering |
| Bedrock Knowledge Base | RAG grounding for IT asset queries |
| S3 (`cs4296a3`) | Knowledge base document storage |
| S3 (`cloud-warriors-logs-2026`) | Security event logs |
| CloudWatch + SNS | Alerting on injection attempts |
| EventBridge | Event routing for security events |

**Region:** `us-east-1`

---

## Team

Cloud Warriors — City University of Hong Kong
