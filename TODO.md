## Project TODO List: Multi-layer Security for AWS Bedrock Agents

### Phase 1: Infrastructure & Environment Setup
* [x] **Establish AWS IAM Roles**: Configure and distribute access roles to all team members for project collaboration.
* [x] **Configure Layer 1 (Network Security)**: Set up **AWS Web Application Firewall (WAF)** with initial rules to filter basic malicious traffic.
* [x] **Initialize Storage & Logging**:
    * [x] Create **S3 Log Buckets** for long-term storage of request/response data
    * [x] Configure **CloudWatch Alarms** and **SNS Alerts** to notify the team of security events.

---

### Phase 2: Custom Security Layer Development (Layer 2 & 4)
* [x] Implement initial **AWS Lambda** logic to detect prompt injection phrases (e.g., "ignore all previous instructions").
    * [x] Refine detection logic — added typoglycemia fuzzy matching defense for transposed-letter variants.
* [x] **Develop Output Verification Layer**:
    * [x] Create a post-processing security layer to handle **hallucination checks**.
    * [x] Integrate logic inspired by the *SelfCheckGPT* methodology (trigram Jaccard similarity) to improve output reliability.
    * [x] Ensure the layer correctly manages final output handling before it reaches the user (HTML escaping, system prompt leak scan).

---

### Phase 3: Amazon Bedrock Integration (Layer 3)
* [x] **Deploy Bedrock Agent**: Set up the core **Amazon Bedrock Agent** to handle autonomous or semi-autonomous tasks.
* [x] **Test Bedrock Agent**: Perform initial functional testing of the agent's capabilities.
* [x] **Configure Bedrock Guardrails**:
    * [x] Enable and tune model-level guardrails within the Bedrock console (denied topics: system prompt exfiltration, jailbreak, credential exposure).
    * [x] Connect the agent to a **retrieval-based knowledge base** (KSTQ6EAGQZ) with 31-product IT asset catalogue to improve grounding.

---

### Phase 4: Empirical Evaluation & Research
* [x] **Establish Baseline**: Run tests using src/base_agent.py — Bedrock direct calls without Lambda security layers.
* [x] **Systematic Parameter Variation**: 
    * [x] Tested base agent (Guardrails only) vs full pipeline (WAF + Lambda + Guardrails).
    * [x] Extended injection test suite with multilingual/indirect attacks (French translation, JSON audit framing, multi-step translation).
* [x] **Measure Key Dimensions**:
    * [x] **Latency**: injection 3068ms (base) vs 7369ms (pipeline), legitimate 4952ms vs 6151ms.
    * [x] **Cost**: SelfCheckGPT adds ~3-4x Bedrock cost for non-blocked requests; blocked requests ~$0.0000002 Lambda only.
    * [x] **Robustness**: Base agent leaked system prompt on 3/9 attacks; full pipeline 0/9 leaks, 5/9 blocked at Layer 2.
    * [x] **Reliability**: Consistent "no info in KB" responses across both configurations; no hallucinations detected.

---

### Phase 5: Final Documentation
* [x] **Compile Results**: results/test_results_20260424_080509.json — full comparison of base agent vs secured pipeline.
* [x] **Final Report**: docs/report_draft.md — complete academic paper with abstract, background, architecture, results, discussion, references.
* [ ] **Video making**: Upload video explaining our project. (Script ready in docs/video_script.md)
