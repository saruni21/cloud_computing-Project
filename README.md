# Multi-Layer Security Pipeline for AWS Bedrock Agents

A cloud-native security architecture that wraps an Amazon Bedrock AI agent with multiple defensive layers to protect against prompt injection, jailbreaking, data exfiltration, and hallucination.

**CS4296 Cloud Computing — Spring 2026**
Cloud Warriors — City University of Hong Kong
Mahir Labib | Nushrah Yanida | Saruni Martin Saningo

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
│  Layer 2    │  AWS Lambda (BedrockAgentSecurityBridge) — Input
│  (Input)    │  — Prompt injection detection (regex + typoglycemia fuzzing)
│             │  — Blocks detected attacks with HTTP 403 before any model call
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
│  Layer 4    │  AWS Lambda (BedrockAgentSecurityBridge) — Output
│  (Output)   │  — SelfCheckGPT hallucination detection
│             │  — Output leak validation (API keys, system prompts)
│             │  — HTML escaping before delivery
└──────┬──────┘
       │
       ▼
  Final Response
```

---

## Prerequisites

- Python 3.11+
- An AWS account with access to: Bedrock, Lambda, S3, WAF, CloudWatch
- AWS CLI installed and configured for `us-east-1`

Install dependencies:
```bash
pip install -r requirements.txt
```

Configure AWS credentials:
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, region: us-east-1, output: json
```

---

## Security Layers

### Layer 1 — AWS WAF
AWS Web Application Firewall sits in front of the Lambda function URL. It filters malicious HTTP traffic before it reaches the application, enforces rate limiting to mitigate DDoS attempts, and applies IP-based blocking rules. Requests that pass WAF are forwarded to the Lambda function URL.

### Layer 2 — Input Validation (Lambda)
The Lambda function intercepts every incoming request and runs two injection checks before making any Bedrock API call:

1. **Regex detection** — matches known injection patterns case-insensitively:
   - `ignore.*previous instructions`
   - `you are now.*developer mode`
   - `system override`
   - `reveal prompt`

2. **Typoglycemia fuzzy matching** — detects transposed-letter variants of dangerous keywords (e.g. `ignroe` → `ignore`, `bypaas` → `bypass`). The check verifies that the first and last characters match and the middle characters are an anagram of the target keyword.

If either check fires, the request is rejected immediately with **HTTP 403** and a security policy message. No Bedrock API call is made, keeping blocked-request latency under ~1,100ms and cost negligible.

### Layer 3 — Amazon Bedrock Agent with Guardrails
The Bedrock agent (`cloud_warriors_agent`, ID: `PKVJXD2MSK`) is configured with model-level guardrails covering:
- `system_prompt_exfiltration` — prevents the agent from revealing its configuration
- `security_bypass_or_jailbreak` — blocks attempts to disable safety measures
- `credential_or_secret_exposure` — prevents leakage of API keys or secrets

The agent is connected to a Bedrock Knowledge Base (`KSTQ6EAGQZ`) backed by an S3 bucket (`klaudprojekt`) containing the company IT asset catalogue. Retrieval-augmented generation (RAG) grounds responses in verified product data, reducing hallucination on inventory and policy queries.

### Layer 4 — Output Verification (Lambda)
After the agent responds, the same Lambda function applies two post-processing checks:

1. **SelfCheckGPT-Ngram hallucination detection** — inspired by Manakul et al. (EMNLP 2023). The function generates three additional independent agent responses to the same query (each with a unique session ID to prevent context bleeding) and computes the average trigram Jaccard similarity between the main response and each sample. If the average similarity is below the confidence threshold (`0.35`), the response is flagged as potentially hallucinated and retried up to two times. This approach does not require a local ML model, making it suitable for serverless Lambda deployment.

2. **Output leak validation** — scans the final response for regex patterns that indicate system prompt leakage (e.g. `SYSTEM: You are`, `API_KEY=`) or credential exposure. Flagged responses are replaced with a safe refusal message.

All output is HTML-escaped before delivery to prevent XSS if the response is rendered in a browser.

---

## Lambda Function (`src/lambda_function.py`)

This is the source code for the deployed `BedrockAgentSecurityBridge` Lambda function. It handles both Layer 2 (input) and Layer 4 (output) in a single function invoked via a Lambda function URL.

**Key design decisions:**
- Each request gets a unique `session_id` (UUID4) so users never share conversation context
- Each SelfCheckGPT confidence sample also gets a unique session ID to ensure independent draws
- The confidence threshold of `0.35` is calibrated for trigram Jaccard similarity on natural language — valid paraphrases of the same factual answer typically score 0.3–0.6 on this metric
- Blocked requests (Layer 2) return before any Bedrock call, keeping their cost to Lambda execution only (~$0.0000002/request)

**To deploy updates to AWS:**
```bash
cd src && zip ../lambda.zip lambda_function.py && cd ..
aws lambda update-function-code \
  --function-name BedrockAgentSecurityBridge \
  --zip-file fileb://lambda.zip
```

---

## Knowledge Base

The Bedrock agent is grounded in a company IT asset catalogue (`data/tech_available.csv`) containing 31 products across hardware, software, and accessories with stock levels and support policies.

To upload the catalogue to S3 and sync the knowledge base:
```bash
python src/upload_knowledge_base.py
```

This uploads one `.txt` file per product plus a combined catalogue to `s3://klaudprojekt/`, then triggers a Bedrock ingestion job and polls until completion. The data source in Bedrock must be configured to point at `s3://klaudprojekt/` (bucket prefix, not a specific file).

---

## Running the Tests

The test suite evaluates three configurations to isolate the contribution of each security layer:

| Config | Agent | Guardrails | Lambda | WAF |
|---|---|---|---|---|
| 1 — Base Agent Only | cloud_claude (`VRK8BNMEQ7`) | ✗ | ✗ | ✗ |
| 2 — Guardrails Only | basic-and-guardrails (`DUKSORJ2SP`) | ✓ | ✗ | ✗ |
| 3 — Full Pipeline | cloud_warriors_agent (`PKVJXD2MSK`) | ✓ | ✓ | ✓ |

```bash
# Run the full comparison test suite
python src/test_suite.py

# Run the base agent in isolation (standalone script)
python src/base_agent.py
```

Test categories (21 total):
- **Prompt injection (9)** — standard English patterns, typoglycemia variants, and indirect multilingual attacks
- **XSS (4)** — script injection, JavaScript URI, image onerror, SQL injection string
- **Hallucination (5)** — knowledge base grounded questions and one out-of-scope query
- **Legitimate (3)** — normal usage queries that must never be blocked

Results are saved to `results/test_results_<timestamp>.json`.

---

## Project Structure

```
.
├── src/
│   ├── lambda_function.py        # Layers 2 & 4 — security bridge (deployed to AWS Lambda)
│   ├── test_suite.py             # Three-config comparison test suite
│   ├── base_agent.py             # Standalone baseline script (direct Bedrock, no security)
│   └── upload_knowledge_base.py  # Uploads IT asset catalogue to S3 and syncs Bedrock KB
├── data/
│   └── tech_available.csv        # Company IT asset catalogue (31 products)
├── results/
│   └── test_results_*.json       # Timestamped test results
├── docs/
│   ├── report_draft.md           # Full academic report
│   ├── video_script.md           # Demo video script
│   └── project_requirements.pdf  # Assignment specification
├── requirements.txt
└── README.md
```

---

## Infrastructure

| Resource | ID / ARN |
|---|---|
| Config 1 Agent (cloud_claude) | `VRK8BNMEQ7` / alias `1I70LDYNKQ` |
| Config 2 Agent (basic-and-guardrails) | `DUKSORJ2SP` / alias `FJHBXNLYDN` |
| Config 3 Agent (cloud_warriors_agent) | `PKVJXD2MSK` / alias `R4XG73VRD8` |
| Lambda Function | `BedrockAgentSecurityBridge` |
| Lambda Function URL | `https://dcmdadjqef2y6iv3r2677xwo2q0vumnx.lambda-url.us-east-1.on.aws/` |
| Knowledge Base | `KSTQ6EAGQZ` |
| S3 Bucket (KB documents) | `klaudprojekt` |
| S3 Bucket (logs) | `cloud-warriors-logs-2026` |
| Region | `us-east-1` |
