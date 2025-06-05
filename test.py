# import requests

# response = requests.post(
#     "http://138.2.171.35:11434/api/generate",
#     json={
#         "prompt": "Hello, how are you?",
#         "model": "llama3:8b",
#         "stream": False
#     }
# )

# print(response.json())

# response = requests.post(
#     "http://localhost:11434/api/generate",
#     json={
#         "prompt": "Hello, how are you?",
#         "model": "llama3:8b",
#         "stream": False
#     }
# )

# print(response.json())


import requests

response = requests.post(
    "http://138.2.171.35:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": "Why is the sky blue?"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))



