import requests
import json

api_key = "sk-8ab5033baa5945bd96c958bd5a243157"
url = "https://api.deepseek.com/chat/completions"

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def ask(prompt):
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    while True:
        prompt = input("Pregunta: ")
        if prompt.lower() in ["salir", "exit"]:
            break
        print(ask(prompt))
