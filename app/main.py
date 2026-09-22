import json
import random
import boto3
from flask import Flask, render_template_string

app = Flask(__name__)

BEDROCK_REGION = "eu-west-1"
MODEL_ID = "eu.anthropic.claude-sonnet-5"

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

TOPICS = [
    "space", "the ocean", "ancient history", "animals",
    "the human body", "technology", "food", "science"
]

PAGE = """
<!doctype html>
<html>
<head>
    <title>Fun Fact Generator</title>
    <style>
        body {
            font-family: -apple-system, sans-serif;
            max-width: 600px;
            margin: 80px auto;
            text-align: center;
            background: #f5f5f7;
        }
        h1 { color: #1d1d1f; }
        #fact {
            font-size: 1.3em;
            margin: 40px 0;
            min-height: 80px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        button {
            font-size: 1em;
            padding: 12px 28px;
            border: none;
            border-radius: 8px;
            background: #0071e3;
            color: white;
            cursor: pointer;
        }
        button:disabled { background: #999; }
    </style>
</head>
<body>
    <h1>Fun Fact Generator!</h1>
    <div id="fact">Click the button to get a fact, powered by AWS Bedrock.</div>
    <button id="btn" onclick="getFact()">New fact!</button>

    <script>
    async function getFact() {
        const btn = document.getElementById('btn');
        const factDiv = document.getElementById('fact');
        btn.disabled = true;
        factDiv.innerText = "Thinking...";
        try {
            const res = await fetch('/fact');
            const data = await res.json();
            factDiv.innerText = data.fact;
        } catch (e) {
            factDiv.innerText = "Something went wrong calling Bedrock.";
        }
        btn.disabled = false;
    }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/fact")
def fact():
    topic = random.choice(TOPICS)
    prompt = f"Tell me one surprising, true fun fact about {topic}. Respond with just the fact in 1-2 sentences, no preamble."

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
        )
        result = json.loads(response["body"].read())
        text = result["content"][0]["text"].strip()
    except Exception as e:
        text = f"Error calling Bedrock: {e}"

    return {"fact": text}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)