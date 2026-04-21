## Project TODO List: Multi-layer Security for AWS Bedrock Agents

### Phase 1: Infrastructure & Environment Setup
* [x] **Establish AWS IAM Roles**: Configure and distribute access roles to all team members for project collaboration.
* [x] **Configure Layer 1 (Network Security)**: Set up **AWS Web Application Firewall (WAF)** with initial rules to filter basic malicious traffic.
* [x] **Initialize Storage & Logging**:
    * [x] Create **S3 Log Buckets** for long-term storage of request/response data
    * [x] Configure **CloudWatch Alarms** and **SNS Alerts** to notify the team of security events.

---

### Phase 2: Custom Security Layer Development (Layer 2)
* [x] Implement initial **AWS Lambda** logic to detect prompt injection phrases (e.g., "ignore all previous instructions").
    * [ ] Refine detection logic using serverless functions or EC2-hosted instances to handle more complex adversarial inputs.
* [ ] **Develop Output Verification Layer**:
    * [ ] Create a post-processing security layer to handle **hallucination checks**.
    * [ ] Integrate logic inspired by the *SelfCheckGPT* methodology to improve output reliability.
    * [ ] Ensure the layer correctly manages final output handling before it reaches the user.

---

### Phase 3: Amazon Bedrock Integration (Layer 3)
* [x] **Deploy Bedrock Agent**: Set up the core **Amazon Bedrock Agent** to handle autonomous or semi-autonomous tasks.
* [x] **Test Bedrock Agent**: Perform initial functional testing of the agent's capabilities.
* [ ] **Configure Bedrock Guardrails**:
    * [ ] Enable and tune model-level guardrails within the Bedrock console.
    * [ ] Connect the agent to a **retrieval-based knowledge base** to improve grounding and reduce hallucinations.

---

### Phase 4: Empirical Evaluation & Research
* [ ] **Establish Baseline**: Run tests using a "basic" Bedrock version without your added security layers.
* [ ] **Systematic Parameter Variation**: 
    * [ ] Test the impact of enabling/disabling guardrails.
    * [ ] Adjust filtering thresholds and output verification steps to find the optimal configuration.
* [ ] **Measure Key Dimensions**:
    * [ ] **Latency**: Track the time overhead introduced by each defensive layer.
    * [ ] **Cost**: Calculate operational expenses for the multi-layered approach.
    * [ ] **Robustness**: Stress-test the pipeline with malformed or adversarial inputs.
    * [ ] **Reliability**: Evaluate the accuracy and grounding of the model's outputs.

---

### Phase 5: Final Documentation
* [ ] **Compile Results**: Compare the empirical data between the proposed pipeline and the baseline.
* [ ] **Final Report**: Document the effectiveness and security improvements of the multi-layered application-level pipeline.
* [ ] **Video making**: Upload video explaining our project.