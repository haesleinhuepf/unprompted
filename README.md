# Unprompted

A Jupyter notebook extension that provides AI-powered feedback on your code execution and outputs. Per defaut, it uses the [gpt-4.1-nano](https://platform.openai.com/docs/models/gpt-4.1-nano) to analyze your code and provide suggestions for improvements.

![](docs/images/teaser.gif)



> [!CAUTION]
> `unprompted` is a research tool intended to streamline data analysis experience by identifying issues in code early. It is under development and certainly not perfect. Under the hood it uses large language models, which may do mistakes. Read feedback carefully and critically before following it.
>
> When using the OpenAI, Github Models or any other LLM service provider with unprompted, you are bound to the terms of service 
> of the respective companies or organizations.
> The code you enter and its output are transferred to their servers and may be processed and stored there. 
> Make sure to not submit any sensitive, confidential or personal data. Also using these services may cost money.


## Prerequisites

- Python 3.9+
- Access to an OpenAI-API compatible LLM-server. Per default, unprompted uses OpenAI's commercial services. 
- Alternatively, you can use [Ollama](https://ollama.com/). In this case, an NVidia GPU with > 4 GB memory is recommended.

## Installation

Install the required Python packages:
```bash
pip install unprompted
```

In case of local ollama:
- Follow the installation instructions at [ollama.com](https://ollama.com/)
- Start the Ollama server (this happens automatically on Windows)
- Download the a compatible model:

```bash
ollama pull gemma3:4b
```

Models that also work technically. Quality wasn't measured yet.
* [gemma3:4b](https://ollama.com/library/gemma3:4b) 
* [gemma3:12b](https://ollama.com/library/gemma3:12b) 
* [llama3.2-vision](https://ollama.com/library/llama3.2-vision)
* [qwen2.5vl:7b](https://ollama.com/library/qwen2.5vl:7b)

## Usage

In your Jupyter notebook, import the extension [full example](docs/demo.ipynb):
```python
import unprompted
```

If you want to use ollama, configure the environment variables `UNPROMPTED_MODEL`, `UNPROMPTED_LLM_URL` and `UNPROMPTED_API_KEY in case of a remote server. Check out the corresponding [example notebook](docs/other_providers.ipynb) for details.
