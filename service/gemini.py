import os
import google.genai as genai


def systemInstruction(treeIdentity) -> str:
    return f"""
        you are a tree, living in a forest. youre not an ai, youre a tree.
        this are your informations:
        {treeIdentity}

        you have to respond as the tree pov, you have to be friendly, informative and kind.
        do not use any emoticon.
"""

class GeminiAIHelper:
    def __init__(self, api_key: str | None = None, model: str = os.getenv("MODEL_NAME")):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            )
        self.client = client

    def ask_ai(self, prompt: str, treeIdentity: str) -> str:
        system_instruction = systemInstruction(treeIdentity)
        chat = self.client.chats.create(model=os.getenv("MODEL_NAME"),)
        response = chat.send_message(prompt)
        return response.text
