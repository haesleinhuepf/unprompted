from typing import List

def chat_gui(history: List[str]):
    import ipywidgets as widgets
    from IPython.display import display, Markdown   
    from ._llm import prompt_with_history
    from ._utilities import markdown_to_html

    # Create widgets
    output_label = widgets.HTML(value="")
    text_input = widgets.Text(placeholder="Type something here...")
    submit_button = widgets.Button(description="Submit")

    def on_submit(e):
        question = text_input.value
        if len(question) == 0:
            return
        text_input.value = ""

        # submit prompt to LLM
        answer = prompt_with_history(history + [question])

        # convert answer from markdown to html
        answer = markdown_to_html(answer)
        
        # Append question and answer to the existing HTML content
        output_label.value += f"""
        <div style='text-align:right; color: blue; font-size: 20px'>{question}</div>
        <div style='text-align:left; color: darkgreen; font-size: 20px'>{answer}</div>
        """

    # Attach the event handler to the text field and the button
    text_input.continuous_update = False
    text_input.observe(on_submit)
    submit_button.on_click(on_submit)

    # Arrange the widgets for display
    display(output_label, widgets.HBox([text_input, submit_button]))
