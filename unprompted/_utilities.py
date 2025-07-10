import re

def markdown_to_html(markdown_text):
    """
    Convert simple markdown to HTML.
    Supports: headers, bold, italic, links, code, lists, and paragraphs.
    """
    lines = markdown_text.split('\n')
    html_lines = []
    in_ul = False
    in_ol = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for unordered list items (-, *, +)
        ul_match = re.match(r'^[\s]*[-*+]\s+(.*)', line)
        if ul_match:
            if not in_ul:
                html_lines.append('<ul>')
                in_ul = True
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False
            html_lines.append(f'<li>{ul_match.group(1)}</li>')
            i += 1
            continue
        
        # Check for ordered list items (1., 2., etc.)
        ol_match = re.match(r'^[\s]*\d+\.\s+(.*)', line)
        if ol_match:
            if not in_ol:
                html_lines.append('<ol>')
                in_ol = True
            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            html_lines.append(f'<li>{ol_match.group(1)}</li>')
            i += 1
            continue
        
        # Close list tags if we're no longer in a list
        if in_ul:
            html_lines.append('</ul>')
            in_ul = False
        if in_ol:
            html_lines.append('</ol>')
            in_ol = False
        
        # Add the line as-is for now
        html_lines.append(line)
        i += 1
    
    # Close any remaining open list tags
    if in_ul:
        html_lines.append('</ul>')
    if in_ol:
        html_lines.append('</ol>')
    
    # Join lines back together
    html = '\n'.join(html_lines)
    
    # Headers (# ## ### #### ##### ######)
    html = re.sub(r'^#{6}\s+(.*?)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^#{5}\s+(.*?)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#{4}\s+(.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^#{3}\s+(.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#{2}\s+(.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^#{1}\s+(.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold (**text** or __text__)
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
    
    # Italic (*text* or _text_)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
    
    # Code (`code`)
    html = re.sub(r'```(.*?)```', r'<code>\1</code>', html)
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # Links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
    # Clean up empty paragraphs and extra whitespace
    html = re.sub(r'<p></p>', '', html)
    html = re.sub(r'\n+', '\n', html)
    
    return html.strip()


def create_reusable_variables_block():
    """Creates a block of text that explains which variables, functions and libraries are
    available to be used."""
    variables = []
    functions = []
    modules = []
    import types
    from IPython import get_ipython

    # figure out which variables are not private
    for key, value in get_ipython().user_ns.items():
        if key.startswith("_"):
            continue
        if callable(value):
            if key not in ["quit", "exit", "get_ipython", "open", "bob"]:
                functions.append(key)
            continue
        if isinstance(value, types.ModuleType):
            if key != "bia_bob":
                modules.append(key)
            continue
        if key in ["In", "Out"]:
            continue
        variables.append(key)

    return f"""
    The following variables are defined: {",".join([str(v) + "(" + str(type(v)) + ")" for v in variables])}    
    The following functions are defined: {",".join([str(f) for f in functions])}    
    The following modules or aliases are imported: {",".join([str(m) for m in modules])}
    """
