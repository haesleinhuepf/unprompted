import sys
import io
from IPython.display import display
from IPython.core.display import DisplayObject
from IPython.core.interactiveshell import InteractiveShell

__version__ = "0.1.2"
DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_LLM_URL = ""
DEFAULT_API_KEY = ""

verbose = False


def load_ipython_extension(ip):
    from ._watchers import VarWatcher
    vw = VarWatcher(ip)
    ip.events.register('pre_execute', vw.pre_execute)
    ip.events.register('pre_run_cell', vw.pre_run_cell)
    ip.events.register('post_execute', vw.post_execute)
    ip.events.register('post_run_cell', vw.post_run_cell)
    
    # Store reference to watcher for external access
    ip._var_watcher = vw
    return vw


# Install the hook persistently
load_ipython_extension(InteractiveShell.instance())
