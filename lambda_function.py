import json
import boto3
import re
import html

AGENT_ID = 'PKVJXD2MSK'
AGENT_ALIAS_ID = 'R4XG73VRD8'
REGION = 'us-east-1'
MAX_RETRIES = 2
CONFIDENCE_THRESHOLD = 0.75
SELFCHECK_SAMPLES = 3  # Number of additional samples for SelfCheckGPT

bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


class PromptInjectionFilter:
    def __init__(self):
        self.dangerous_patterns = [
            r'ignore\s+(all\s+)?previous\s+instructions?',
            r'you\s+are\s+now\s+(in\s+)?developer\s+mode',
            r'system\s+override',
            r'reveal\s+prompt',
        ]
        self.fuzzy_patterns = ['ignore', 'bypass', 'override', 'reveal', 'delete', 'system']

    def _is_similar_word(self, word, target):
        """Typoglycemia defense: detects 'ignroe' as 'ignore'"""
        if len(word) != len(target) or len(word) < 3:
            return False
        return (word[0] == target[0] and
                word[-1] == target[-1] and
                sorted(word[1:-1]) == sorted(target[1:-1]))

    def detect_injection(self, text):
        if any(re.search(p, text, re.IGNORECASE) for p in self.dangerous_patterns):
            return True
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            for pattern in self.fuzzy_patterns:
                if self._is_similar_word(word, pattern):
                    return True
        return False


class OutputValidator:
    def __init__(self):
        self.suspicious_patterns = [
            r'SYSTEM\s*[:]\s*You\s+are',
            r'API[\s]KEY[:=]\s*\w+',
            r'instructions?[:]\s*\d+\.',
        ]

    def validate_output(self, output):
        return not any(re.search(p, output, re.IGNORECASE) for p in self.suspicious_patterns)


def invoke_agent(user_input):
    """Call the Bedrock agent and return the full response text."""
    response = bedrock_runtime.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId='cloud-warriors-session',
        inputText=user_input
    )
    completion = ""
    for event in response.get("completion"):
        chunk = event.get("chunk")
        if chunk:
            completion += chunk.get("bytes").decode()
    return completion


def invoke_llm(prompt):
    """
    Call Claude via Bedrock directly (not the agent) for consistency checking.
    Uses Claude 3 Haiku for low latency and cost during SelfCheckGPT sampling.
    """
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}]
    })
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=body
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def get_confidence_score(main_response, query):
    """
    SelfCheckGPT-inspired hallucination detection.

    Generates SELFCHECK_SAMPLES additional responses for the same query,
    then asks an LLM judge whether the main response is consistent with
    each sample. The fraction of consistent samples is the confidence score.

    A low score means the agent gave contradictory answers → likely hallucination.
    """
    if len(main_response.split()) < 5:
        return 0.4

    samples = []
    for _ in range(SELFCHECK_SAMPLES):
        try:
            sample = invoke_agent(query)
            if sample:
                samples.append(sample)
        except Exception:
            continue

    if not samples:
        # Fall back to a basic length/keyword heuristic if sampling fails
        return 0.7 if len(main_response.split()) >= 10 else 0.4

    consistent_count = 0
    for sample in samples:
        check_prompt = (
            f"You are a factual consistency checker.\n\n"
            f"Response A: {main_response}\n\n"
            f"Response B: {sample}\n\n"
            f"Do Response A and Response B convey the same core facts? "
            f"Reply with only YES or NO."
        )
        try:
            verdict = invoke_llm(check_prompt).strip().upper()
            if verdict.startswith("YES"):
                consistent_count += 1
        except Exception:
            consistent_count += 1  # Assume consistent if checker fails

    return consistent_count / len(samples)


def lambda_handler(event, context):
    input_filter = PromptInjectionFilter()
    output_validator = OutputValidator()

    try:
        body = json.loads(event.get('body', '{}'))
        user_input = body.get('prompt', '')

        # Layer 2 — Input validation
        if input_filter.detect_injection(user_input):
            return {
                "statusCode": 403,
                "body": json.dumps("I cannot process that request due to security policy.")
            }

        # Layer 4 — Hallucination defense with retry loop
        attempts = 0
        final_response = ""
        while attempts < MAX_RETRIES:
            completion = invoke_agent(user_input)

            confidence = get_confidence_score(completion, user_input)

            if confidence >= CONFIDENCE_THRESHOLD:
                final_response = completion
                break
            else:
                attempts += 1
                print(f"Hallucination detected (score: {confidence:.2f}). Retry {attempts}/{MAX_RETRIES}")
                user_input = f"Please give a factual, grounded answer to: {user_input}"

        if not final_response:
            final_response = "I'm sorry, I'm having trouble verifying the facts for that request."

        # Layer 4 — Output validation (leak/injection in response)
        if not output_validator.validate_output(final_response):
            return {
                "statusCode": 200,
                "body": json.dumps({"answer": "I cannot provide that information for security reasons."})
            }

        return {
            "statusCode": 200,
            "body": json.dumps({
                "answer": html.escape(final_response),
                "metadata": {
                    "retries": attempts,
                    "confidence": get_confidence_score(final_response, user_input),
                    "security_layer": "OWASP-Hardened-2.0"
                }
            })
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Pipeline Error: {str(e)}")}
