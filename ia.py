import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

print("--- Asistente eGarage (Escribe 'salir' para terminar) ---")
while True:
    prompt = input("\nPregunta / Tarea: ")
    if prompt.lower() in ['salir', 'exit']:
        break
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres un experto en desarrollo de software, Python y bases de datos para el sistema eGarage."},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-120b",
    )
    print("\n" + chat_completion.choices[0].message.content)
