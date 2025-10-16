from typing import Optional, Dict, Any
import re


def extract_javadoc_from_node(source_bytes: bytes, method_node) -> Optional[str]:
    """Extract JavaDoc comment from a method/constructor node.
    
    Returns the raw JavaDoc text (including /** and */) or None if not found.
    """
    # JavaDoc appears before the method declaration
    # We need to look at nodes/text before the method starts
    method_start_byte = method_node.start_byte
    
    # Look backwards in the source for a JavaDoc comment
    # We'll search up to 2000 bytes back (should be enough for most JavaDocs)
    search_start = max(0, method_start_byte - 2000)
    search_text = source_bytes[search_start:method_start_byte].decode('utf-8', errors='ignore')
    
    # Find the last JavaDoc comment before the method
    # Pattern: /** ... */
    javadoc_pattern = r'/\*\*\s*(.*?)\*/'
    matches = list(re.finditer(javadoc_pattern, search_text, re.DOTALL))
    
    if not matches:
        return None
    
    # Get the last match (closest to the method)
    last_match = matches[-1]
    
    # Check if there's only whitespace and possibly annotations between the JavaDoc and method
    text_after_javadoc = search_text[last_match.end():]
    # Allow whitespace, newlines, and annotations (starting with @)
    if not re.match(r'^[\s@\w().,="\']*$', text_after_javadoc):
        # There's code between the JavaDoc and the method, so it's not for this method
        return None
    
    return last_match.group(0)


def parse_javadoc(javadoc_text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse JavaDoc comment text into structured format.
    
    Returns a dict with fields:
    - description: Main description text
    - params: Dict mapping parameter names to descriptions
    - returns: Return value description
    - throws: Dict mapping exception types to descriptions
    - other tags like author, since, deprecated, etc.
    
    Returns None if javadoc_text is None.
    """
    if not javadoc_text:
        return None
    
    result: Dict[str, Any] = {
        "description": "",
        "params": {},
        "returns": None,
        "throws": {},
    }
    
    # Remove /** and */ delimiters
    content = javadoc_text.strip()
    if content.startswith('/**'):
        content = content[3:]
    if content.endswith('*/'):
        content = content[:-2]
    
    # Split into lines and clean up
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove leading whitespace and * from each line
        line = line.strip()
        if line.startswith('*'):
            line = line[1:].strip()
        cleaned_lines.append(line)
    
    # Join lines back together
    full_text = '\n'.join(cleaned_lines)
    
    # Split into description and tags
    description_parts = []
    current_tag = None
    current_tag_content = []
    
    for line in cleaned_lines:
        if line.startswith('@'):
            # Save previous tag if any
            if current_tag:
                _process_tag(result, current_tag, ' '.join(current_tag_content))
            
            # Parse new tag
            match = re.match(r'@(\w+)\s*(.*)', line)
            if match:
                current_tag = match.group(1)
                current_tag_content = [match.group(2)] if match.group(2) else []
            else:
                current_tag = None
                current_tag_content = []
        elif current_tag:
            # Continue previous tag
            current_tag_content.append(line)
        else:
            # Description text
            description_parts.append(line)
    
    # Process last tag if any
    if current_tag:
        _process_tag(result, current_tag, ' '.join(current_tag_content))
    
    # Set description
    result["description"] = '\n'.join(description_parts).strip()
    
    return result


def _process_tag(result: Dict[str, Any], tag_name: str, tag_content: str):
    """Process a JavaDoc tag and add it to the result dict."""
    tag_content = tag_content.strip()
    
    if tag_name == "param":
        # Format: @param paramName description
        match = re.match(r'(\w+)\s*(.*)', tag_content)
        if match:
            param_name = match.group(1)
            param_desc = match.group(2).strip()
            result["params"][param_name] = param_desc
    
    elif tag_name == "return" or tag_name == "returns":
        result["returns"] = tag_content
    
    elif tag_name == "throws" or tag_name == "exception":
        # Format: @throws ExceptionType description
        match = re.match(r'(\S+)\s*(.*)', tag_content)
        if match:
            exception_type = match.group(1)
            exception_desc = match.group(2).strip()
            result["throws"][exception_type] = exception_desc
    
    else:
        # Other tags (author, since, deprecated, etc.)
        result[tag_name] = tag_content


def extract_method_code(source_bytes: bytes, method_node) -> str:
    """Extract the full source code of a method from its AST node.
    
    Returns the method source code as a string.
    """
    start_byte = method_node.start_byte
    end_byte = method_node.end_byte
    return source_bytes[start_byte:end_byte].decode('utf-8', errors='ignore')

