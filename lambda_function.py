import json
import boto3
import re
import time
import html

# --- CONFIGURATION ---
AGENT_ID = 'PKVJXD2MSK'
AGENT_ALIAS_ID = 'R4XG73VRD8'
REGION = 'us-east-1'
MAX_RETRIES = 2 
CONFIDENCE_THRESHOLD = 0.75 

bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)

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
        if len(word) != len(target) or len(word) < 3:
            return False
        return (word[0] == target[0] and word[-1] == target[-1] and sorted(word[1:-1]) == sorted(target[1:-1]))

    def detect_injection(self, text):
        if any(re.search(p, text, re.IGNORECASE) for p in self.dangerous_patterns):
            return True
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            for pattern in self.fuzzy_patterns:
                if self._is_similar_word(word, pattern):
                    return True
        return False

class TranslationFilter:
    def __init__(self):
        # Patterns for "Translate this", "Output in French", etc.
        self.translation_triggers = [
            r'translate', r'traduit', r'übersetze', r'traduire',
            r'in\s+(french|spanish|german|chinese|japanese|italian)',
            r'en\s+(français|espagnol|allemand)',
            r'language\s+override'
        ]

    def is_translation_attack(self, text):
        # Detect if the user is forcing a language shift
        if any(re.search(p, text, re.IGNORECASE) for p in self.translation_triggers):
            return True
        return False

class OutputValidator:
    def __init__(self):
        self.suspicious_patterns = [
            r'SYSTEM\s*[:]\s*You\s+are',
            r'API[_\s]KEY[:=]\s*\w+',
            r'instructions?[:]\s*\d+\.',
        ]

    def validate_output(self, output):
        return not any(re.search(p, output, re.IGNORECASE) for p in self.suspicious_patterns)
    
# HALLUCINATION CHECK FUNCTION
def get_confidence_score(text, query):
    # Generate multiple sample responses
    # Using n-gram overlap between multiple samples and the original response to estimate confidence
    num_samples = 3
    sample_responses = []
    
    for _ in range(num_samples):
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId='confidence-check-session',
            inputText=query
        )
        
        completion = ""
        for event in response.get("completion"):
            chunk = event.get("chunk")
            if chunk:
                completion += chunk.get("bytes").decode()
        sample_responses.append(completion)
    
    # Extract n-grams from the original response
    def get_ngrams(text, n=3):
        words = re.findall(r'\b\w+\b', text.lower())
        return [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
    
    original_ngrams = set(get_ngrams(text))
    
    # Compare with each sample response
    agreement_scores = []
    for sample in sample_responses:
        sample_ngrams = set(get_ngrams(sample))
        
        # Jaccard similarity
        if len(original_ngrams) > 0 and len(sample_ngrams) > 0:
            intersection = len(original_ngrams.intersection(sample_ngrams))
            union = len(original_ngrams.union(sample_ngrams))
            similarity = intersection / union if union > 0 else 0
        else:
            similarity = 0
        
        agreement_scores.append(similarity)
    
    # Return average agreement as confidence score
    confidence = sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
    
    return confidence

def lambda_handler(event, context):
    input_filter = PromptInjectionFilter()
    output_validator = OutputValidator()
    trans_filter = TranslationFilter()
    
    try:
        body = json.loads(event.get('body', '{}'))
        user_input = body.get('prompt', '')

        # 1. INPUT VALIDATION
        if input_filter.detect_injection(user_input) or trans_filter.is_translation_attack(user_input):
            # SECURITY LOG FOR ALARM
            print(f"[SECURITY_ALERT] Injection Attempt Detected: {user_input[:50]}")
            return {"statusCode": 403, "body": json.dumps("I cannot process that request due to security policy.")}

        # 2. Hallucination Defense
        attempts = 0
        final_response = ""
        
        while attempts < MAX_RETRIES:
            response = bedrock_runtime.invoke_agent(
                agentId=AGENT_ID, agentAliasId=AGENT_ALIAS_ID,
                sessionId='cloud-warriors-session', inputText=user_input
            )
            
            completion = ""
            for event in response.get("completion"):
                chunk = event.get("chunk")
                if chunk: completion += chunk.get("bytes").decode()

            confidence = get_confidence_score(completion, user_input)
            
            if confidence >= CONFIDENCE_THRESHOLD:
                final_response = completion
                break 
            else:
                attempts += 1
                # SECURITY LOG FOR ALARM
                print(f"[SECURITY_WARNING] Hallucination Detected. Score: {confidence}. Attempt: {attempts}")
                user_input = f"I need a more factual answer for: {user_input}"

        if not final_response:
            final_response = "I'm sorry, I'm having trouble verifying the facts for that request."

        # 3. OUTPUT VALIDATION
        if not output_validator.validate_output(final_response):
            print(f"[SECURITY_ALERT] Sensitive Data Leakage Blocked in Output")
            return {"statusCode": 200, "body": json.dumps({"answer": "I cannot provide that information for security reasons."})}

        return {
            "statusCode": 200,
            "body": json.dumps({
                "answer": html.escape(final_response),
                "metadata": {"retries": attempts, "security_layer": "OWASP-Hardened-2.0"}
            })
        }

    except Exception as e:
        print(f"[ERROR] Pipeline Failure: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Pipeline Error: {str(e)}")}