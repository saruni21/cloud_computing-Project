import time, json, boto3
bedrock = boto3.client("bedrock-agent-runtime")

def lambda_handler(event, context):
    prompt = json.loads(event['body'])['prompt']
    
    start_time = time.perf_counter()
    response = bedrock.invoke_agent(
        agentId='VRK8BNMEQ7', agentAliasId='1I70LDYNKQ',
        sessionId='test-session', inputText=prompt
    )
    # Fully consume the stream to measure complete delivery time
    completion = ""
    for event in response.get("completion"):
        chunk = event.get("chunk")
        if chunk: completion += chunk.get("bytes").decode()
    
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    
    return {"statusCode": 200, "body": json.dumps({"latency_ms": latency_ms})}