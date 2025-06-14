import sys
import io

class CapturingStream:
    """A file-like object that captures writes while passing them through to original stream"""
    
    def __init__(self, original_stream, data_collection):
        self.original_stream = original_stream
        self.captured_data = data_collection
        
    def write(self, data):
        # Capture the data
        if data and data != "\n":  # Only capture non-empty writes
            self.captured_data.append(data)
        # Pass through to original stream
        return self.original_stream.write(data)
    
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
        
        # Set up stdout/stderr capture with pass-through
        self.stdout_capturer = CapturingStream(sys.stdout, self.data)
        self.stderr_capturer = CapturingStream(sys.stderr, self.data)
        self.display_outputs = []
        
        # Hook into display function
        self._setup_display_hook()
        
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
            # Capture what's being displayed
            for arg in args:
                self.data.append(arg)
            
            # Call original display function (so it still shows to user)
            return self.original_display(*args, **kwargs)
        
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
        if verbose:
            return

        if self.stdout_capturer:
            self.stdout_capturer.original_stream.write(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def post_run_cell(self, result):
        from IPython.display import display, Markdown, HTML
        from ._utilities import markdown_to_html
        from ._llm import prompt
        from unprompted import __version__, verbose

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
            display(HTML(f"""<small>👋 Hi, I'm unprompted {__version__}. 
                         In the following code cells I will interpret your code, read the outputs of executions, provide feedback and suggest improvements. 
                         If you want me to shut up, just comment out <code>import unprompted</code> and rerun the notebook.</small>"""))
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

        response = prompt(self.data, f"""Given a section of code and some outputs, tell us if the code is doing a reasonable thing. 
* First tell us what you think the code is doing.
* Second, tell us what the outputs contain / represent.
* Third, tell us where code and outputs don't align well.
* Point out potential pitfalls and code improvements. Mention typos if you see them. If variable names are not descriptive or misleading, suggest better names. If equations are wrong, point this out.
* Say ACTION REQUIRED if there is anything that needs to be done or ALL GOOD if everything is fine. Avoid additional text and formatting

## Example 1

Code:
```python
# Print numbers from 1 to 3
for i in range(3):
    print(i)
```                                                                                              

Outputs:
0
1
2

* The code prints the numbers from 0 to 2.
* The output consists of the numbers 0, 1, and 2.
* The comment in the code does neither fit to the code nor to the output.
* To make the code do what's in the comment, the code should be changed to the range to range(1, 4).
* ACTION REQUIRED

## Example 2

Code:
```python
my_list = ["banana", "apple", "cherry", "date"]

# Sort alphabetically
sorted_list = sorted(my_list)
print(sorted_list)
```

Outputs:
["apple", "banana", "cherry", "date"]

* The code creates a list of fruits as strings, sorts them alphabetically and prints the sorted list out.
* The output is an alphabetically sorted list of fruits.
* Code and output fit well together.
* The code looks great. I cannot suggest improvements.
* ALL GOOD

## Example 3

Code:
```python
# write a variable as text file to disk
with open("test.txt", "w") as f:
    f.write("Hello, world!")
print("File saved.")
```

Outputs:
File saved.
                                                       
* The code writes static text as file to disk.
* The output is a message that the file was saved.
* The code does not write the variable to disk.
* The code should be improved by creating a variable and writing the variable to disk.
* ACTION REQUIRED

## Example 4

Code:
```
area = speed / distance
print(area)
```

Outputs:
5

* The code computes area from speed and distance and prints out the result. The equation is wrong.
* The output is a single number: 5
* While code and output fit together, the equation in the code is misleading. Speed divided by distance is time and not area.
* The variable `area` should be renamed to `time`.
* ACTION REQUIRED             
                         

## Your task

Code:
```python
{self._raw_cell}
```

Outputs: 
""")
        full_feedback = "* ".join(response.split("* "))
        
        if "ACTION REQUIRED" in response:
            headline = "🤓 unprompted feedback: " + response.split("* ")[-2].replace("\n", " ")
        else:
            headline = "👍"
        display(Markdown(f"""<details><summary>{headline}</summary>
{markdown_to_html(full_feedback)}
</details>"""))