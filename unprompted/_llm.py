
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

def prompt(list_of_objects: List[Any], code: str, ollama_url="http://localhost:11434/v1", model="gemma3:12b", temperature=0.0) -> str:
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
    outputs = "\n".join(text_parts)

    # Compose the full message payload
    messages = [
        {
            "role": "system",
            "content": """You are an excellent data scientist, statistician and python programmer. You also know physics and mathematics. You are very critical and will not accept any wrong equations, misleading variable names, incorrect comments, etc.
Given a section of code and some outputs, your job is to review the code carefully and provide constructive feedback to improve the code.
Your feedback should be very detailed and include:
* First tell us what you think the code is doing. Mention all potential issues in the code such as wrong equations, misleading variable names, incorrect comments, etc.
* Second, tell us what the outputs contain / represent and the relation to the given code. Explain images and figures in very detail.
* Third, tell us where code and outputs don't align well, or where the code is misleading. Also point out if the code is not doing what is written in its comments, and explain what is different, missing, or misleading.
* Point out potential pitfalls and code improvements. Mention typos if you see them. If variable names are not descriptive or misleading, suggest better names. If equations are wrong, point this out.
* Say ACTION REQUIRED if there is anything that needs to be done or ALL GOOD if everything is fine. Avoid additional text and formatting
"""}, {
            "role": "user",
            "content": [
                {"type": "text", "text": """Code:
```python
# Print numbers from 1 to 3
for i in range(3):
    print(i)
```                                                                                              

Outputs:
0
1
2
"""}]
        },
        {
            "role": "assistant",
            "content": """* The code prints the numbers from 0 to 2.
* The output consists of the numbers 0, 1, and 2, as instructed in the code.
* The comment in the code does neither fit to the code nor to the output.
* To make the code do what's in the comment, the code should be changed to the range to range(1, 4).
* ACTION REQUIRED
"""
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": """Code:
```python
my_list = ["banana", "apple", "cherry", "date"]

# Sort alphabetically
sorted_list = sorted(my_list)
print(sorted_list)
```

Outputs:
["apple", "banana", "cherry", "date"]
"""}]},
        {
            "role": "assistant",
            "content": """* The code creates a list of fruits as strings, sorts them alphabetically and prints the sorted list out.
* The output is an alphabetically sorted list of fruits as instructed in the code.
* Code and output fit well together.
* The code looks great. I cannot suggest improvements.
* ALL GOOD
"""},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": """Code:
```python
area = speed / distance
print(area)
```

Outputs:
5
"""}]},
        {
            "role": "assistant",
            "content": """* The code computes area from speed and distance and prints out the result. The equation is wrong.
* The output is a single number: 5, presumably the result of the wrong equation.
* While code and output fit together, the equation in the code is misleading. Speed divided by distance is time and not area.
* The variable `area` should be renamed to `time`.
* ACTION REQUIRED
"""},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": """Code:
```python
# load a text file from disk
with open("test.txt", "r") as f:
    text = f.read()
print(text)
```

Outputs:
Hello, world!
"""}]},
        {
            "role": "assistant",
            "content": """* The code loads a text file from disk and prints out the content.
* The output is the content of the text file as instructed in the code.
* Code and output fit well together.
* The code looks great. I cannot suggest improvements.
* ALL GOOD
"""},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""Code:
```python
{code}
```

Outputs: 
{outputs}
"""},
                *image_messages
            ]
        }
    ]

    # Send the chat completion request
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    return response.choices[0].message.content.strip()