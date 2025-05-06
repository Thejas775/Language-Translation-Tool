# backend/app/services/xml_service.py
import xml.etree.ElementTree as ET
from typing import Dict, Optional

async def xml_to_strings_dict(xml_content: str) -> Dict[str, str]:
    """
    Convert XML content to a dictionary of strings
    
    Args:
        xml_content: Content of the XML file
        
    Returns:
        Dictionary mapping string IDs to values
    """
    try:
        root = ET.fromstring(xml_content)
        strings_dict = {}
        
        for string_elem in root.findall(".//string"):
            name = string_elem.get("name")
            if name:
                # Extract the text content, preserving any nested tags
                value = "".join(string_elem.itertext())
                strings_dict[name] = value
                
        return strings_dict
    except Exception as e:
        raise Exception(f"Error parsing XML: {str(e)}")

async def dict_to_strings_xml(strings_dict: Dict[str, str], language_code: Optional[str] = None) -> str:
    """
    Convert a dictionary of strings to XML content
    
    Args:
        strings_dict: Dictionary of string IDs and values
        language_code: Optional language code for the strings
        
    Returns:
        XML content as a string
    """
    try:
        root = ET.Element("resources")
        
        for key, value in strings_dict.items():
            string_elem = ET.SubElement(root, "string")
            string_elem.set("name", key)
            string_elem.text = value
        
        # Convert to string
        xml_str = ET.tostring(root, encoding="unicode")
        return '<?xml version="1.0" encoding="utf-8"?>\n' + xml_str
    except Exception as e:
        raise Exception(f"Error generating XML: {str(e)}")

async def flatten_json(nested_json: Dict, prefix: str = "") -> Dict[str, str]:
    """
    Flatten a nested JSON object into a dictionary with dot notation keys
    
    Args:
        nested_json: Nested JSON object
        prefix: Prefix for keys (used in recursion)
        
    Returns:
        Flattened dictionary
    """
    flattened = {}
    for key, value in nested_json.items():
        if isinstance(value, dict):
            flattened.update(await flatten_json(value, prefix + key + "."))
        else:
            flattened[prefix + key] = value
    return flattened

async def unflatten_json(flattened_json: Dict[str, str]) -> Dict:
    """
    Convert a flattened dictionary back to a nested JSON object
    
    Args:
        flattened_json: Dictionary with dot notation keys
        
    Returns:
        Nested JSON object
    """
    result = {}
    for key, value in flattened_json.items():
        parts = key.split(".")
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result