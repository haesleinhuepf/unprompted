
from openai import OpenAI
import matplotlib.figure
import base64
import io
from typing import List, Any, Union

def fig_to_base64(fig: matplotlib.figure.Figure) -> str:
    """Convert a Matplotlib Figure to a base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_bytes = buf.read()
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"

def prompt(list_of_objects: List[Any], text_prompt: str, ollama_url="http://localhost:11434/v1", model="gemma3:4b") -> str:
    """
    Sends a combined text and image prompt to a locally running Gemma model via Ollama.

    Args:
        list_of_objects: A list of arbitrary objects, some of which may be matplotlib Figures.
        text_prompt: Instruction or query string.
        ollama_url: Base URL of the local Ollama server.

    Returns:
        str: LLM response.
    """
    client = OpenAI(
        base_url=ollama_url,
        api_key="ollama"  # dummy value for local use
    )

    # Prepare text content and image messages
    text_parts = []
    image_messages = []

    for i, obj in enumerate(list_of_objects):
        if isinstance(obj, matplotlib.figure.Figure):
            img_data_url = fig_to_base64(obj)
            image_messages.append({"type": "image_url", "image_url": {"url": img_data_url}})
            text_parts.append(f"[img{len(image_messages)}]")

        else:
            text_parts.append(str(obj))

    # Combine text parts into one message
    full_text = text_prompt + "\n".join(text_parts)

    # Compose the full message payload
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": full_text},
                *image_messages
            ]
        }
    ]

    # Send the chat completion request
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()