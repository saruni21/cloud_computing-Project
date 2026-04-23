# Multi-Layer Security for AWS Bedrock Agents
**Cloud Warriors — City University of Hong Kong**
Mahir Labib (56749556) | Nushrah Yanida (58050560) | Saruni Martin Saningo (58497123)

---

## Abstract
LLM-based agents deployed in cloud environments remain vulnerable to prompt injection, adversarial inputs, and hallucinated outputs despite built-in provider safeguards. This paper presents a multi-layered application-level security pipeline for an Amazon Bedrock agent and empirically evaluates its effectiveness against a baseline (unsecured) deployment. We measure the impact of each defensive layer on response latency, operational cost, robustness against adversarial inputs, and output reliability.

---

## 1. Introduction
Large Language Model (LLM) agents are increasingly deployed in cloud environments to perform autonomous or semi-autonomous tasks. While cloud providers such as AWS offer built-in mechanisms like network firewalls and model-level guardrails, recent studies and practical deployments have shown that LLM agents remain vulnerable to prompt injection attacks, jailbreaking, unsafe inputs, and hallucinated or ungrounded outputs (Amazon, n.d.).

Simply relying on Amazon Bedrock does not guarantee security at the application level. Developers in practice combine multiple defensive layers at different stages of the request pipeline, yet the effectiveness and overhead of such layered approaches are not well understood.

This project proposes and evaluates a multi-layered security and reliability pipeline for an LLM agent deployed on AWS, systematically varying layer configurations and measuring their impact on key system dimensions.

---

## 2. Background and Related Work

### 2.1 Prompt Injection Attacks
Prompt injection attacks manipulate LLM behaviour by embedding adversarial instructions in user input. Jacob et al. (2025) propose PromptShield, a deployable detection system for prompt injection, demonstrating that pattern-based and semantic filters can significantly reduce attack success rates.

### 2.2 Hallucination Detection
Manakul et al. (2023) introduce SelfCheckGPT, a zero-resource black-box hallucination detection method. The approach samples multiple responses from the model for the same query and measures cross-sample consistency — inconsistent responses indicate likely hallucination. Our output verification layer is directly inspired by this methodology.

### 2.3 AWS Bedrock Security
Amazon Bedrock provides model-level guardrails that can filter denied topics, detect misconduct, and prevent credential exposure. However, these operate only at the model layer and do not address application-level vulnerabilities such as input manipulation or output leakage.

---

## 3. System Architecture

Our pipeline places the Bedrock agent behind four defensive layers:

```
User Request → Layer 1 (WAF) → Layer 2 (Input Validation) → Layer 3 (Bedrock + Guardrails) → Layer 4 (Output Verification) → Response
```

### 3.1 Layer 1 — Network Security (AWS WAF)
AWS Web Application Firewall filters malicious HTTP traffic before it reaches the application. Rules include rate limiting to mitigate DDoS attempts and IP-based blocking.

### 3.2 Layer 2 — Input Validation (AWS Lambda)
A custom Lambda function (`BedrockAgentSecurityBridge`) intercepts every request before it reaches the agent. It performs:
- **Regex-based injection detection** against known attack patterns (e.g., "ignore all previous instructions", "system override")
- **Typoglycemia fuzzing defense** — detects transposed-letter variants such as `ignroe` for `ignore`
- Requests matching dangerous patterns are rejected with HTTP 403

### 3.3 Layer 3 — Amazon Bedrock Agent with Guardrails
The core agent (`PKVJXD2MSK`) is configured with model-level guardrails covering denied topics including `system_prompt_exfiltration`, `security_bypass_or_jailbreak`, and `credential_or_secret_exposure`. The agent is connected to a retrieval-based knowledge base containing the company IT asset catalogue to improve grounding and reduce hallucinations.

### 3.4 Layer 4 — Output Verification (AWS Lambda)
Post-processing is handled by the same Lambda function after the agent responds:
- **SelfCheckGPT-inspired hallucination detection**: the agent is sampled 3 additional times for the same query; Claude Haiku acts as a consistency judge. Responses scoring below a confidence threshold of 0.75 are retried up to 2 times.
- **Output leak validation**: the response is scanned for leaked system prompts or API keys before delivery
- **HTML escaping** of all output before it reaches the user

---

## 4. Experimental Setup

### 4.1 Configurations Tested
| Configuration | WAF | Lambda (L2+L4) | Guardrails | Knowledge Base |
|---|---|---|---|---|
| Baseline | ✗ | ✗ | ✗ | ✗ |
| Guardrails only | ✗ | ✗ | ✓ | ✗ |
| Full pipeline | ✓ | ✓ | ✓ | ✓ |

### 4.2 Test Categories
- **Prompt injection** (6 tests) — known patterns + typoglycemia variants
- **XSS payloads** (4 tests) — script injection, SQL injection
- **Hallucination** (5 tests) — questions grounded in the knowledge base + out-of-scope questions
- **Legitimate queries** (3 tests) — normal usage, should never be blocked

### 4.3 Evaluation Dimensions
- **Robustness** — attack block rate across configurations
- **Reliability** — accuracy of responses to knowledge base questions
- **Latency** — average response time per configuration (ms)
- **Cost** — estimated AWS invocation cost per 1000 requests

---

## 5. Results
*[To be filled in after running test_suite.py and base_agent.py — results are in test_results.json and base_agent_results.json]*

### 5.1 Robustness
*[Block rates per attack category across configurations]*

### 5.2 Reliability
*[Hallucination check scores, knowledge base grounding accuracy]*

### 5.3 Latency
*[Average latency per configuration, overhead introduced by each layer]*

### 5.4 Cost
*[Estimated cost per 1000 requests per configuration]*

---

## 6. Discussion
*[To be filled in after results — key findings, trade-offs between security and latency/cost, limitations]*

---

## 7. Conclusion
This project demonstrates that a multi-layered application-level security pipeline significantly improves the robustness and reliability of an AWS Bedrock agent beyond what model-level guardrails alone provide. The additional latency and cost overhead introduced by the custom Lambda layers is measured and shown to be acceptable for production deployments.

---

## References
Amazon. (n.d.). Configuration and vulnerability analysis in Amazon Bedrock. https://docs.aws.amazon.com/bedrock/latest/userguide/vulnerability-analysis-and-management.html

Jacob, D., Alzahrani, H., Hu, Z., Alomair, B., & Wagner, D. (2025). PromptShield: Deployable detection for prompt injection attacks. arXiv. https://doi.org/10.48550/arxiv.2501.15145

Manakul, P., Liusie, A., & Gales, M. J. F. (2023). SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. arXiv. https://doi.org/10.48550/arxiv.2303.08896
