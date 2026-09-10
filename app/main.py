import json
import os

import boto3
from flask import Flask, jsonify, request

app = Flask(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-2")
MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
)

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/invoke", methods=["POST"])
def invoke():
    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt")

    if not prompt:
        return jsonify({"error": "Request body must include a 'prompt' field"}), 400

    bedrock_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(bedrock_request),
        )
        response_body = json.loads(response["body"].read())
        reply_text = response_body["content"][0]["text"]
        return jsonify({"reply": reply_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
