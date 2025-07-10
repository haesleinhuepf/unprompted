import sys
import io

class CapturingStream:
    """A file-like object that captures writes while passing them through to original stream"""
    
    def __init__(self, original_stream, data_collection, original_display):
        self.original_stream = original_stream
        self.captured_data = data_collection
        self.original_display = original_display
        
    def write(self, data):
        from unprompted import INSTANT_FEEDBACK
        # Capture the data
        if data and data != "\n":  # Only capture non-empty writes
            self.captured_data.append(data)

        result = self.original_stream.write(data)
        if INSTANT_FEEDBACK:
            instant_feedback(data, self.original_display)

        # Pass through to original stream
        return result
    
    def flush(self):
        return self.original_stream.flush()

    # Delegate other attributes to original stream
    def __getattr__(self, name):
        return getattr(self.original_stream, name)

class VarWatcher(object):
    def __init__(self, ip):
        self.shell = ip
        self.last_x = None
        self.data = []
        self.stdout_capturer = None
        self.stderr_capturer = None
        self.original_display = None
        self.display_outputs = []
        self._raw_cell = None
        
    def pre_execute(self):
        self.debug_print("PRE")
        self.last_x = self.shell.user_ns.get('x', None)
        self.data = []

        # Hook into display function
        self._setup_display_hook()


        # Set up stdout/stderr capture with pass-through
        self.stdout_capturer = CapturingStream(sys.stdout, self.data, self.original_display)
        self.stderr_capturer = CapturingStream(sys.stderr, self.data, self.original_display)
        self.display_outputs = []
        
        # Replace stdout/stderr with capturing versions
        sys.stdout = self.stdout_capturer
        sys.stderr = self.stderr_capturer

    def _setup_display_hook(self):
        """Set up hook to capture display() calls while still displaying them"""
        if self.original_display is None:
            # Get the display function from IPython
            from IPython.display import display as original_display
            self.original_display = original_display
            
        def display_hook(*args, **kwargs):
            from unprompted import INSTANT_FEEDBACK
            
            # Capture what's being displayed
            for arg in args:
                self.data.append(arg)

            # Call original display function (so it still shows to user)
            result =  self.original_display(*args, **kwargs)
            if INSTANT_FEEDBACK:
                for arg in args:
                    instant_feedback(arg, self.original_display)

            return result
        
        # Replace display function in the user namespace and IPython.display
        self.shell.user_ns['display'] = display_hook
        import IPython.display
        IPython.display.display = display_hook

    def pre_run_cell(self, info):
        self.debug_print("PRC")
        self._raw_cell = info.raw_cell
        #print('info.raw_cell =', info.raw_cell)
        #print('info.store_history =', info.store_history)
        #print('info.silent =', info.silent)
        #print('info.shell_futures =', info.shell_futures)
        #print('info.cell_id =', info.cell_id)

    def post_execute(self):
        self.debug_print("POE")
        
        # Restore original stdout/stderr
        if self.stdout_capturer:
            sys.stdout = self.stdout_capturer.original_stream
        if self.stderr_capturer:
            sys.stderr = self.stderr_capturer.original_stream
        
        # Restore original display function
        if self.original_display is not None:
            self.shell.user_ns['display'] = self.original_display
            import IPython.display
            IPython.display.display = self.original_display

    def debug_print(self, *args, **kwargs):
        from unprompted import verbose
        if not verbose:
            return

        if self.stdout_capturer:
            self.stdout_capturer.original_stream.write(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def post_run_cell(self, result):
        from IPython.display import display, Markdown, HTML
        from ._utilities import markdown_to_html
        from ._llm import prompt
        from unprompted import __version__, verbose, DEFAULT_MODEL
        import os

        self.debug_print("POC")
        #print('result.execution_count = ', result.execution_count)
        #print('result.error_before_exec = ', result.error_before_exec)
        #print('result.error_in_exec = ', result.error_in_exec)
        #print('result.info = ', result.info)
        #print('result.result = ', result.result)
        
        # Add result to data if it exists
        if result.result is not None:
            self.data.append(result.result)

        # Add error information if there were errors
        if result.error_before_exec is not None:
            self.data.append(result.error_before_exec)
        if result.error_in_exec:
            self.data.append(result.error_in_exec)
        
        if self._raw_cell is None:
            # first execution
            model = os.getenv("UNPROMPTED_MODEL", DEFAULT_MODEL)
            display(HTML(f"""<small>👋 Hi, this is <a href="https://github.com/haesleinhuepf/unprompted" target="_blank"><i>umprompted</i></a> {__version__} using {model} under the hood. 
                         Following code cells and related output will be interpreted by AI to provide feedback and suggest improvements. 
                         If you want to keep code and/or its output private, do not use this tool or configure it to use a local LLM. Check the documentation for details.
                         Also <i>umprompted</i> does mistakes. Treat its suggestions carefully.</small>"""))
            return
        
        if self._raw_cell.startswith("%bob") or self._raw_cell.startswith("%%bob"):
            # we trust bob and don't question prompts to it.
            # we can check its code suggestions when they are executed.
            return

        if verbose:
            print("----")
            print(f"Collected {len(self.data)} items:")
            for i, item in enumerate(self.data):
                print(f"  {i}: {type(item)}: {item}")

        temperature = 0.1
        for _ in range(3): # attempts
            response = prompt(self.data, self._raw_cell, temperature=temperature)

            try:
                full_feedback = "* ".join(response.split("* "))
                
                if "ACTION REQUIRED" in response:
                    headline = "🤓 unprompted feedback: " + response.split("ACTION REQUIRED")[1].strip(":").strip()
                else:
                    headline = "👍"
                break
            except:
                full_feedback = response
                headline = "🤔"

                #print(response)

                temperature += 0.2
                print("Retrying...")

        text = markdown_to_html(headline).replace("\n", " ").strip()
        display(Markdown(f"""<details><summary>{text}</summary>
{markdown_to_html(full_feedback)}
</details>"""))
        
def instant_feedback(arg, display_func):
    from IPython.display import display, HTML, Markdown
    import matplotlib
    from ._utilities import markdown_to_html
    from ._llm import prompt_text, prompt_figure
    import html

    
    if isinstance(arg, str):
        if len(str(arg)) < 100:
            return
        feedback = markdown_to_html(prompt_text(f"Summarize the following text to a short sentence and respond with a single line: {arg}"))
        headline = "🤓"
    elif isinstance(arg, matplotlib.figure.Figure):
        feedback = markdown_to_html(prompt_figure(arg))
        headline = "🤩"
    else:
        feedback = html.escape(str(type(arg)))
        headline = "🤔"

    display_func(Markdown(f"""<div align="right" width="100%"><details><summary>{headline}</summary>
{feedback}
</details></div>"""))
