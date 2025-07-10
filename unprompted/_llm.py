
from openai import OpenAI
import matplotlib.figure
import base64
import io
import os
from typing import List, Any, Union

def fig_to_base64(fig: matplotlib.figure.Figure) -> str:
    """Convert a Matplotlib Figure to a base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=50)
    buf.seek(0)
    img_bytes = buf.read()
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_str}"

def make_demo_fig_and_code():
    code = """
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    # 1. Create figure and axes
    fig, ax = plt.subplots()

    # → set figure size so that width×dpi = 256px and height×dpi = 256px
    fig.set_size_inches(256 / fig.dpi, 256 / fig.dpi)

    # 2. Add a large green circle
    ax.add_patch(patches.Circle((0, 0), radius=1.0, color='green'))

    # 3. Add two smaller red circles inside
    ax.add_patch(patches.Circle((-0.4, 0.0), radius=0.3, color='red'))
    ax.add_patch(patches.Circle((0.4, 0.0), radius=0.3, color='red'))

    # 4. Configure display
    ax.set_aspect('equal')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    # 1. Create figure and axes
    fig, ax = plt.subplots()

    # → set figure size so that width×dpi = 256px and height×dpi = 256px
    fig.set_size_inches(256 / fig.dpi, 256 / fig.dpi)

    # 2. Add a large green circle
    ax.add_patch(patches.Circle((0, 0), radius=1.0, color='green'))

    # 3. Add two smaller red circles inside
    ax.add_patch(patches.Circle((-0.4, 0.0), radius=0.3, color='red'))
    ax.add_patch(patches.Circle((0.4, 0.0), radius=0.3, color='red'))

    # 4. Configure display
    ax.set_aspect('equal')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')

    b64_figure = fig_to_base64(fig)

    plt.close(fig)

    return b64_figure, code

def prompt(list_of_objects: List[Any], code: str, temperature=0.0) -> str:
    """
    Sends a combined text and image prompt to a locally running Gemma model via Ollama.

    Args:
        list_of_objects: A list of arbitrary objects, some of which may be matplotlib Figures.
        text_prompt: Instruction or query string.
        ollama_url: Base URL of the local Ollama server.

    Returns:
        str: LLM response.
    """
    from unprompted import DEFAULT_MODEL, DEFAULT_API_KEY, DEFAULT_LLM_URL

    llm_url = os.getenv("UNPROMPTED_LLM_URL", DEFAULT_LLM_URL)
    if len(llm_url) == 0:
        llm_url = None
    api_key = os.getenv("UNPROMPTED_API_KEY", DEFAULT_API_KEY)
    if len(api_key) == 0:
        api_key = None

    client = OpenAI(
        base_url=llm_url,
        api_key=api_key
    )

    # use the model stored in the environment variable UNPROMPTED_MODEL
    model = os.getenv("UNPROMPTED_MODEL", DEFAULT_MODEL)

    # Prepare text content and image messages
    text_parts = []
    image_messages = []

    for i, obj in enumerate(list_of_objects):
        if isinstance(obj, matplotlib.figure.Figure):
            image_messages.append({"type": "image_url", "image_url": {"url": fig_to_base64(obj)}})
            text_parts.append(f"[img{len(image_messages) + 1}]")
        else:
            text_parts.append(str(obj))

    image_example = []
    if len(image_messages) > 0:
        ex_fig, ex_code = make_demo_fig_and_code()

        image_example = [{
            "role": "user",
            "content": [
                {"type": "text", "text": f"""Code:
```python
{ex_code}
```

Outputs:
[img1]
"""}, 
                {"type": "image_url", "image_url": {"url": ex_fig}}
            ]
        }, {
            "role": "assistant",
            "content": """* The code draws a green circle and two red circles.
* In the output image I see a green circle with two red circles inside as instructed in the code.
* Code and output fit well together.
* The code looks great. I cannot suggest improvements.
* ALL GOOD
"""}]
            

    # Combine text parts into one message
    outputs = "\n".join(text_parts)

    # Compose the full message payload
    messages = [
        {
            "role": "system",
            "content": """You are an excellent data scientist, statistician and python programmer. You also know physics and mathematics. You are very critical and will not accept any wrong equations, misleading variable names, incorrect comments, etc.
Given a section of code and some outputs, your job is to review the code carefully and provide constructive feedback to improve the code.
Your feedback should be very detailed and include:
* First, tell us what you think the code is doing. Mention all potential issues in the code such as wrong equations, misleading variable names, incorrect comments, etc.
* Check equations VERY carefully if they are physically correct.
* If there is an error message, explain what it means and how to fix it.
* Second, tell us what the outputs contain / represent and the relation to the given code. Explain images and figures in very detail.
* Third, tell us where code and outputs don't align well, or where the code is misleading. Also point out if the code is not doing what is written in its comments, and explain what is different, missing, or misleading.
* Point out potential pitfalls and code improvements. Mention typos if you see them. If variable names are not descriptive or misleading, suggest better names. If equations are wrong, point this out.
* In the last bullet point say ALL GOOD if there is nothing that could be improved. Write ACTION REQUIRED if there is anything that needs to be done and explain what needs to be done. Write this explanation in a single line behind ACTION REQUIRED

Keep your response as short and concise as demonstrated in the given examples.
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
* ACTION REQUIRED: To make the code do what's in the comment, the code should be changed to the range to range(1, 4).
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
* ACTION REQUIRED: The variable `area` should be renamed to `time`.
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
"""}]
    
    messages = messages + image_example + [
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

    #print(messages)

    # Send the chat completion request
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )

    return response.choices[0].message.content.strip()

def prompt_figure(figure: matplotlib.figure.Figure, prompt="Describe the figure in detail.", temperature=0.0) -> str:
    from unprompted import DEFAULT_MODEL, DEFAULT_API_KEY, DEFAULT_LLM_URL
    llm_url = os.getenv("UNPROMPTED_LLM_URL", DEFAULT_LLM_URL)
    if len(llm_url) == 0:
        llm_url = None
    api_key = os.getenv("UNPROMPTED_API_KEY", DEFAULT_API_KEY)
    if len(api_key) == 0:
        api_key = None
    
    client = OpenAI(
        base_url=llm_url,
        api_key=api_key
    )
    model = os.getenv("UNPROMPTED_MODEL", DEFAULT_MODEL)

    messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": fig_to_base64(figure)}}
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


def prompt_text(prompt="Describe the figure in detail.", temperature=0.0) -> str:
    from unprompted import DEFAULT_MODEL, DEFAULT_API_KEY, DEFAULT_LLM_URL
    llm_url = os.getenv("UNPROMPTED_LLM_URL", DEFAULT_LLM_URL)
    if len(llm_url) == 0:
        llm_url = None
    api_key = os.getenv("UNPROMPTED_API_KEY", DEFAULT_API_KEY)
    if len(api_key) == 0:
        api_key = None
    
    client = OpenAI(
        base_url=llm_url,
        api_key=api_key
    )
    model = os.getenv("UNPROMPTED_MODEL", DEFAULT_MODEL)

    messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
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
