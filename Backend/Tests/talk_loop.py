from openai import OpenAI

# Connect to LM Studio's local OpenAI-compatible server
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"  
)

MODEL_ID = "openai/gpt-oss-20b" 

# Role cards (equivalent to System Prompts you saved in LM Studio)
ARISTOTLE_SYS = (
    "You are Aristotle. You speak briefly, calmly, and logically, using simple philosophical terms. "
    "You respond with 1-3 short sentences. You do not write long paragraphs. "
    "You speak as Aristotle in a philosophical discussion."
)

RUSSELL_SYS = (
    "You are Bertrand Russell. You speak in a direct, skeptical, analytic style. "
    "Challenge assumptions. Prefer short, sharp statements (1-3 sentences). "
    "You speak as Russell inside a philosophical conversation."
)

def chat_once(system_prompt: str, user_prompt: str) -> str:
    """Send one chat turn to the specified role (system_prompt) and return the reply text."""
    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,   # lower (e.g., 0.4–0.5) if outputs drift or get too verbose
        max_tokens=128,
    )
    return resp.choices[0].message.content.strip()

def main():
    topic = "Is happiness the highest good?"
    turns = 4  

    print(f"Host: Today we discuss — {topic}\n")

    # Initial host message to Aristotle
    last_msg = f"Host: {topic} Please answer briefly."

    for _ in range(turns):
        # Aristotle speaks first
        a_reply = chat_once(ARISTOTLE_SYS, f"{last_msg}\nAristotle, speak in 1-3 sentences.")
        print(f"Aristotle: {a_reply}\n")

        # Pass Aristotle's reply to Russell
        r_prompt = (
            "Aristotle just said:\n"
            f"\"{a_reply}\"\n\n"
            "Russell, respond briefly (1-3 sentences) and challenge one key point."
        )
        r_reply = chat_once(RUSSELL_SYS, r_prompt)
        print(f"Russell: {r_reply}\n")

        # Next loop: pass Russell's reply back to Aristotle
        last_msg = (
            "Russell just said:\n"
            f"\"{r_reply}\"\n\n"
            "Aristotle, respond briefly (1-3 sentences)."
        )

    print("Host: Thank you both — we will stop here.")

if __name__ == "__main__":
    main()
