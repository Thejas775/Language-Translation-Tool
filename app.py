import streamlit as st
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import time
import re
import requests
import base64
import xml.etree.ElementTree as ET
from io import StringIO
import zipfile
from github import Github
from github import Auth

# Load environment variables
load_dotenv()

# Configure the Gemini API
def configure_genai():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = st.session_state.get('api_key', '')
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Failed to configure Gemini API: {str(e)}")
            return False
    return False

# Configure GitHub API
def configure_github():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        github_token = st.session_state.get('github_token', '')
    
    if github_token:
        try:
            auth = Auth.Token(github_token)
            g = Github(auth=auth)
            # Test the connection
            g.get_user().login
            return g
        except Exception as e:
            st.error(f"Failed to configure GitHub API: {str(e)}")
            return None
    return None

def scan_github_repository(repo_url, pattern_search=True):
    """
    Scan a GitHub repository for strings.xml files.
    Uses pattern-based search for faster scanning when pattern_search=True
    Supports specifying a branch in the URL
    
    Args:
        repo_url (str): The GitHub repository URL (can include /tree/branch-name)
        pattern_search (bool): Whether to use pattern-based search
        
    Returns:
        dict: A dictionary of strings.xml files found in the repository
    """
    try:
        # Extract branch if specified in the URL
        branch = None
        if "/tree/" in repo_url:
            # Split the URL at /tree/ to separate branch name
            base_url, branch_part = repo_url.split("/tree/", 1)
            # Get the branch name (it might have additional path components)
            branch = branch_part.split("/")[0]
            # Reconstruct the base repo URL without the branch part
            repo_url = base_url
        
        # Extract owner and repo name from URL
        url_parts = repo_url.strip('/').split('/')
        owner = url_parts[-2]
        repo_name = url_parts[-1]
        
        g = configure_github()
        if not g:
            st.error("GitHub API not configured. Please enter a valid token in the sidebar.")
            return {}
        
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # If branch was specified in the URL, use it
        if branch:
            st.info(f"Scanning branch: {branch}")
            # Verify the branch exists
            try:
                repo.get_branch(branch)
            except Exception as e:
                st.error(f"Branch '{branch}' not found. Error: {str(e)}")
                return {}
        else:
            # Otherwise use the default branch
            branch = repo.default_branch
            st.info(f"Using default branch: {branch}")
        
        # Common patterns where strings.xml files are typically located
        common_patterns = [
            # Mifos KMP specific patterns - prioritize these
            # "feature/*/src/commonMain/composeResources/values/strings.xml",
            # "feature/*/src/*/composeResources/values/strings.xml",
            # "feature/*/src/*/resources/values/strings.xml",
            
            # KMM/Compose Multiplatform patterns
            "*/src/commonMain/composeResources/values/strings.xml",
            "*/*/src/commonMain/composeResources/values/strings.xml",
            # "*/src/commonMain/resources/MR/base/strings.xml",
            # "*/*/src/commonMain/resources/MR/base/strings.xml",
            
            # # Android module patterns
            # "*/src/main/res/values/strings.xml",
            # "*/*/src/main/res/values/strings.xml",
            # "feature/*/src/main/res/values/strings.xml",
            
            # # General fallbacks
            # "**/values/strings.xml",
            # "**/values-*/strings.xml"
        ]
        
        found_files = {}
        
        # If pattern search is enabled, search for common patterns first
        if pattern_search:
            with st.spinner(f"Searching for strings.xml files using common patterns in branch '{branch}'..."):
                progress_bar = st.progress(0)
                
                for i, pattern in enumerate(common_patterns):
                    try:
                        # Update progress
                        progress_bar.progress((i + 1) / len(common_patterns))
                        st.caption(f"Trying pattern: {pattern}")
                        
                        # Search for files matching the pattern
                        contents = repo.get_contents("", ref=branch)
                        path_parts = pattern.split("/")
                        
                        # Try to match the pattern
                        files = search_by_pattern(repo, contents, path_parts, 0, branch)
                        
                        if files:
                            st.caption(f"Found {len(files)} files with pattern: {pattern}")
                            
                        for file_path, content in files.items():
                            found_files[file_path] = content
                            
                    except Exception as e:
                        st.caption(f"Error with pattern {pattern}: {str(e)}")
                        # Continue with next pattern if an error occurs
                        continue
                
                # If we found files, return them without doing a full repository scan
                if found_files:
                    return found_files
        
        # If no files were found with pattern search or pattern search is disabled,
        # fall back to full repository scan (slower but thorough)
        st.info(f"Pattern search didn't find strings.xml files. Performing a full repository scan of branch '{branch}' (this may take longer)...")
        return search_files_in_repo(repo, "strings.xml", branch)
            
    except Exception as e:
        st.error(f"Error scanning repository: {str(e)}")
        return {}

def search_by_pattern(repo, contents, pattern_parts, current_depth, branch):
    """
    Recursively search for files that match a pattern.
    
    Args:
        repo: GitHub repository object
        contents: Current contents to search through
        pattern_parts: List of parts in the pattern path
        current_depth: Current depth in the pattern
        branch: Branch to search in
        
    Returns:
        dict: A dictionary mapping file paths to their content
    """
    found_files = {}
    
    if current_depth >= len(pattern_parts):
        return found_files
        
    current_pattern = pattern_parts[current_depth]
    
    for content_item in contents:
        # Skip non-matching items unless it's a wildcard
        if current_pattern != "*" and current_pattern != "**" and content_item.name != current_pattern:
            continue
            
        if content_item.type == "dir":
            # If it's a directory and matches the pattern (or pattern is a wildcard)
            try:
                next_contents = repo.get_contents(content_item.path, ref=branch)
                
                # If the pattern is "**", we need to search at this level AND deeper
                if current_pattern == "**":
                    # Search at this level with the next pattern part
                    deeper_files = search_by_pattern(repo, next_contents, pattern_parts, current_depth + 1, branch)
                    found_files.update(deeper_files)
                    
                    # Also search at this same level for more directories
                    same_level_files = search_by_pattern(repo, next_contents, pattern_parts, current_depth, branch)
                    found_files.update(same_level_files)
                else:
                    # Regular directory match, go one level deeper in the pattern
                    deeper_files = search_by_pattern(repo, next_contents, pattern_parts, current_depth + 1, branch)
                    found_files.update(deeper_files)
            except Exception as e:
                st.caption(f"Error accessing directory {content_item.path}: {str(e)}")
                # Skip if we can't access the directory content
                continue
                
        elif content_item.type == "file" and current_depth == len(pattern_parts) - 1:
            # If it's a file and the last pattern part matches the filename
            if content_item.name == pattern_parts[-1] or pattern_parts[-1] == "*":
                try:
                    # Get the file content
                    raw_content = base64.b64decode(content_item.content).decode('utf-8')
                    found_files[content_item.path] = raw_content
                    st.caption(f"Found matching file: {content_item.path}")
                except Exception as e:
                    st.caption(f"Error decoding content of {content_item.path}: {str(e)}")
                    # Skip if we can't decode the content
                    continue
    
    return found_files

def search_files_in_repo(repo, filename, branch):
    """
    Search for files in a repository with a specific filename.
    
    Args:
        repo: GitHub repository object
        filename (str): The filename to search for
        branch (str): Branch to search in
        
    Returns:
        dict: A dictionary mapping file paths to their content
    """
    found_files = {}
    
    # Get all files in the repository
    contents = repo.get_contents("", ref=branch)
    
    with st.spinner(f"Scanning repository for {filename} files in branch '{branch}'..."):
        progress_bar = st.progress(0)
        total_files = len(contents)
        processed = 0
        
        while contents:
            file_content = contents.pop(0)
            processed += 1
            progress_bar.progress(min(1.0, processed / max(1, total_files)))
            
            if file_content.type == "dir":
                try:
                    # Add directory contents to the queue
                    dir_contents = repo.get_contents(file_content.path, ref=branch)
                    contents.extend(dir_contents)
                    total_files += len(dir_contents) - 1  # Adjust total count
                except Exception as e:
                    # Skip if we can't access the directory
                    st.caption(f"Error accessing directory {file_content.path}: {str(e)}")
                    continue
            elif file_content.name == filename:
                # Found a strings.xml file
                try:
                    raw_content = base64.b64decode(file_content.content).decode('utf-8')
                    found_files[file_content.path] = raw_content
                    st.caption(f"Found file: {file_content.path}")
                except Exception as e:
                    # Skip if we can't decode the content
                    st.caption(f"Error decoding content of {file_content.path}: {str(e)}")
                    continue
    
    return found_files
    """
    Search for files in a repository with a specific filename.
    
    Args:
        repo: GitHub repository object
        filename (str): The filename to search for
        
    Returns:
        dict: A dictionary mapping file paths to their content
    """
    found_files = {}
    
    # Get the default branch
    default_branch = repo.default_branch
    
    # Get all files in the repository
    contents = repo.get_contents("")
    
    with st.spinner(f"Scanning repository for {filename} files..."):
        progress_bar = st.progress(0)
        total_files = len(contents)
        processed = 0
        
        while contents:
            file_content = contents.pop(0)
            processed += 1
            progress_bar.progress(min(1.0, processed / max(1, total_files)))
            
            if file_content.type == "dir":
                try:
                    # Add directory contents to the queue
                    dir_contents = repo.get_contents(file_content.path)
                    contents.extend(dir_contents)
                    total_files += len(dir_contents) - 1  # Adjust total count
                except Exception as e:
                    # Skip if we can't access the directory
                    st.caption(f"Error accessing directory {file_content.path}: {str(e)}")
                    continue
            elif file_content.name == filename:
                # Found a strings.xml file
                try:
                    raw_content = base64.b64decode(file_content.content).decode('utf-8')
                    found_files[file_content.path] = raw_content
                    st.caption(f"Found file: {file_content.path}")
                except Exception as e:
                    # Skip if we can't decode the content
                    st.caption(f"Error decoding content of {file_content.path}: {str(e)}")
                    continue
    
    return found_files
    """
    Search for files in a repository with a specific filename.
    
    Args:
        repo: GitHub repository object
        filename (str): The filename to search for
        
    Returns:
        dict: A dictionary mapping file paths to their content
    """
    found_files = {}
    
    # Get the default branch
    default_branch = repo.default_branch
    
    # Get all files in the repository
    contents = repo.get_contents("")
    
    with st.spinner(f"Scanning repository for {filename} files..."):
        progress_bar = st.progress(0)
        total_files = len(contents)
        processed = 0
        
        while contents:
            file_content = contents.pop(0)
            processed += 1
            progress_bar.progress(min(1.0, processed / max(1, total_files)))
            
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            elif file_content.name == filename:
                # Found a strings.xml file
                raw_content = base64.b64decode(file_content.content).decode('utf-8')
                found_files[file_content.path] = raw_content
    
    return found_files

def parse_strings_xml(xml_content):
    """
    Parse a strings.xml file and extract the strings.
    
    Args:
        xml_content (str): The content of the strings.xml file
        
    Returns:
        dict: A dictionary of string keys and values
    """
    try:
        root = ET.fromstring(xml_content)
        result = {}
        
        for string_elem in root.findall('.//string'):
            key = string_elem.get('name')
            if key:
                # Remove any formatting tags but keep the text
                value = ''.join(string_elem.itertext())
                result[key] = value
                
        return result
    except Exception as e:
        st.error(f"Error parsing XML: {str(e)}")
        return {}

def parse_translation_response(response_text):
    """
    Parse the translation response with improved error handling for common issues.
    
    Args:
        response_text (str): The raw text response from the API
        
    Returns:
        dict: A dictionary of key-value pairs with translations, or empty dict if parsing fails
    """
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()

        response_text = re.sub(r'\s*//.*', '', response_text)
        response_text = re.sub(r'/\*.*?\*/', '', response_text, flags=re.DOTALL)
        
        response_text = re.sub(r',\s*}', '}', response_text)
        response_text = re.sub(r',\s*\]', ']', response_text)
        
        response_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', response_text)
        
        response_text = re.sub(r'}\s*{', '},{', response_text)
        
        translations_data = json.loads(response_text)
        
        # Process translations
        all_results = {}
        
        # Handle both array and object formats
        if isinstance(translations_data, list):
            for item in translations_data:
                key = item.get("key")
                translation = item.get("translation")
                if key and translation:
                    all_results[key] = translation
        elif isinstance(translations_data, dict):
            for key, item in translations_data.items():
                if isinstance(item, dict) and "translation" in item:
                    all_results[key] = item["translation"]
                else:
                    all_results[key] = item
        
        return all_results
        
    except json.JSONDecodeError as json_err:
        st.warning(f"JSON error: {str(json_err)}")
        st.code(response_text[:200] + "..." if len(response_text) > 200 else response_text)
        
        # Try extracting individual JSON objects
        pattern = r'{[^{}]*"key"\s*:\s*"([^"]+)"[^{}]*"translation"\s*:\s*"([^"]+)"[^{}]*}'
        matches = re.finditer(pattern, response_text)
        
        translations = {}
        for match in matches:
            try:
                obj_text = match.group(0)
                # Fix potential issues within the object
                obj_text = re.sub(r',\s*}', '}', obj_text)
                obj = json.loads(obj_text)
                if "key" in obj and "translation" in obj:
                    translations[obj["key"]] = obj["translation"]
            except:
                key_match = re.search(r'"key"\s*:\s*"([^"]+)"', match.group(0))
                translation_match = re.search(r'"translation"\s*:\s*"([^"]+)"', match.group(0))
                if key_match and translation_match:
                    translations[key_match.group(1)] = translation_match.group(1)
        
        if translations:
            return translations
            
        pattern = r'"key"\s*:\s*"([^"]+)"[^}]+"translation"\s*:\s*"([^"]+)"'
        matches = re.finditer(pattern, response_text)
        
        translations = {}
        for match in matches:
            key = match.group(1)
            translation = match.group(2)
            translations[key] = translation
            
        return translations

def translate_all_strings(texts_dict, target_language, contexts_dict={}):
    try:
        # Filter only string values
        string_contents = {k: v for k, v in texts_dict.items() if isinstance(v, str)}
        
        # Prepare translation items
        translation_items = []
        for key, text in string_contents.items():
            context = contexts_dict.get(key, "")
            translation_items.append({
                "id": key,  # Use actual key as ID
                "key": key,
                "text": text,
                "context": context
            })
        
        input_text = json.dumps(translation_items, ensure_ascii=False)
        estimated_tokens = len(input_text) / 4  # Rough estimate: 4 chars per token
        

        if estimated_tokens > 10000000:
            st.info(f"Input is too large for a single API call (est. {int(estimated_tokens)} tokens). Switching to batch mode...")
            return batch_translate_texts(string_contents, target_language, contexts_dict)
        
        # Craft a translation prompt for all strings at once
        prompt = f"""
        Translate the following UI strings to {target_language}. 
        
        Each item includes:
        - id: A unique identifier
        - key: The string identifier
        - text: The text to translate
        - context: (Optional) Where/how this string is used in the UI
        
        Guidelines:
        - Keep translations concise and natural
        - Use everyday language, not formal or complex terms
        - Maintain the same meaning and intent as the original
        - Don't add extra words or explanations
        - Ensure translations would fit well on buttons or UI elements
        - Preserve any placeholders like {{variable}} or %s
        - Preserve formatting and special characters
        - DO NOT include any comments in the JSON output
        - DO NOT use comment lines with // or /* */ in your response
        
        Input:
        {json.dumps(translation_items, ensure_ascii=False, indent=2)}
        
        Return ONLY a valid JSON array with the same structure as input, but add a "translation" field to each item.
        Don't include any explanations, comments, or additional text outside or inside the JSON array.
        """
        
        # Configure model with larger output tokens
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"max_output_tokens": 8192})
        response = model.generate_content(prompt)
        
        # Parse the response using improved parsing
        response_text = response.text.strip()
        translations = parse_translation_response(response_text)
        
        if translations:
            return translations
            
        # If parsing completely fails, fall back to batch translation
        st.warning("Failed to parse response. Switching to batch mode...")
        return batch_translate_texts(string_contents, target_language, contexts_dict)
            
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        # Fall back to batch translation
        st.warning("Error in single API call. Switching to batch mode...")
        return batch_translate_texts(string_contents, target_language, contexts_dict)

def batch_translate_texts(texts_dict, target_language, contexts_dict={}):
    try:
        string_contents = {k: v for k, v in texts_dict.items() if isinstance(v, str)}
        
        texts_list = list(string_contents.items())
        
        batch_size = 50 
        all_results = {}
        
        # Process each batch
        total_batches = (len(texts_list) + batch_size - 1) // batch_size
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(0, len(texts_list), batch_size):
            batch = texts_list[i:i+batch_size]
            current_batch = (i//batch_size) + 1
            
            status_text.text(f"Translating batch {current_batch} of {total_batches} ({len(batch)} strings)")
            
            # Create structured format for translation with JSON
            translation_items = []
            for j, (key, text) in enumerate(batch):
                context = contexts_dict.get(key, "")
                translation_items.append({
                    "id": key,
                    "key": key,
                    "text": text,
                    "context": context
                })
            
            # Craft a batch translation prompt with explicit instruction not to use comments
            prompt = f"""
            Translate the following UI strings to {target_language}. 
            
            Each item includes:
            - id: A unique identifier
            - key: The string identifier
            - text: The text to translate
            - context: (Optional) Where/how this string is used in the UI
            
            Guidelines:
            - Keep translations concise and natural
            - Use everyday language, not formal or complex terms
            - Maintain the same meaning and intent as the original
            - Don't add extra words or explanations
            - Ensure translations would fit well on buttons or UI elements
            - Preserve any placeholders like {{variable}} or %s
            - Preserve formatting and special characters
            - DO NOT include any comments in the JSON output
            - DO NOT use comment lines with // or /* */ in your response
            
            Input:
            {json.dumps(translation_items, ensure_ascii=False, indent=2)}
            
            Return ONLY a valid JSON array with the same structure as input, but add a "translation" field to each item.
            Don't include any explanations, comments, or additional text outside or inside the JSON array.
            """
            
            # Configure model with appropriate tokens
            model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"max_output_tokens": 8192})
            
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    
                    # Parse the response using the improved parser
                    response_text = response.text.strip()
                    translations = parse_translation_response(response_text)
                    
                    if translations:
                        all_results.update(translations)
                        break  # Success! Exit retry loop
                    elif retry < max_retries - 1:
                        st.warning(f"Failed to parse batch {current_batch}. Retrying ({retry + 1}/{max_retries})...")
                        time.sleep(2)  # Wait a bit before retrying
                    else:
                        st.error(f"Failed to translate batch {current_batch} after {max_retries} attempts. Skipping batch.")
                        # Add batch keys with original values to show something rather than nothing
                        for key, text in batch:
                            if key not in all_results:
                                all_results[key] = text  # Use original as fallback
                
                except Exception as batch_error:
                    if retry < max_retries - 1:
                        st.warning(f"Error in batch {current_batch}: {str(batch_error)}. Retrying ({retry + 1}/{max_retries})...")
                        time.sleep(2)  # Wait a bit before retrying
                    else:
                        st.error(f"Failed to process batch {current_batch} after {max_retries} attempts. Skipping batch.")
                        # Add batch keys with original values to show something rather than nothing
                        for key, text in batch:
                            if key not in all_results:
                                all_results[key] = text  # Use original as fallback
            
            # Update progress
            progress_bar.progress(min(1.0, (i + batch_size) / len(texts_list)))
            
            # Small delay between batches to avoid rate limiting
            time.sleep(1)
        
        # Check if any strings were not translated and add them with original text
        for key, text in string_contents.items():
            if key not in all_results:
                all_results[key] = text
                
        return all_results
        
    except Exception as e:
        st.error(f"Batch translation error: {str(e)}")
        # Create a dictionary with original strings as fallback
        return {k: v for k, v in texts_dict.items() if isinstance(v, str)}
        
def translate_text(text, target_language, context=""):
    try:
        # Craft a careful prompt for translation
        prompt = f"""
        Translate the following UI string to {target_language}:
        
        Original text: "{text}"
        
        Context: {context}
        
        Guidelines:
        - Keep the translation concise and natural
        - Use everyday language, not formal or complex terms
        - Maintain the same meaning and intent as the original
        - Don't add extra words or explanations
        - Ensure the translation would fit well on a button or UI element
        - Preserve any placeholders like {{variable}} or %s
        
        Return ONLY the translated text without any explanations or additional comments.
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        translation = response.text.strip()
        if ":" in translation:
            translation = translation.split(":", 1)[1].strip()
        
        translation = translation.strip('"\'')
        
        return translation
    except Exception as e:
        st.error(f"Single translation error: {str(e)}")
        return None

def flatten_json(nested_json, prefix=""):
    flattened = {}
    for key, value in nested_json.items():
        if isinstance(value, dict):
            flattened.update(flatten_json(value, prefix + key + "."))
        else:
            flattened[prefix + key] = value
    return flattened

def unflatten_json(flattened_json):
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

def xml_to_strings_dict(xml_content):
    """Convert XML content to a dictionary of strings"""
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
        st.error(f"Error parsing XML: {str(e)}")
        return {}

def dict_to_strings_xml(strings_dict, language_code=None):
    """Convert a dictionary of strings to XML content"""
    root = ET.Element("resources")
    
    for key, value in strings_dict.items():
        string_elem = ET.SubElement(root, "string")
        string_elem.set("name", key)
        string_elem.text = value
    
    # Convert to string
    xml_str = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + xml_str

def create_kotlin_multiplatform_structure(translations_dict, languages):
    """Create a Kotlin Multiplatform file structure for translations"""
    files = {}
    
    # Create base/default strings.xml (assuming English)
    files["commonMain/resources/MR/base/strings.xml"] = dict_to_strings_xml(translations_dict["en"])
    
    # Create language-specific files
    for lang_code in languages:
        if lang_code != "en" and lang_code in translations_dict:
            files[f"commonMain/resources/MR/{lang_code}/strings.xml"] = dict_to_strings_xml(translations_dict[lang_code])
    
    return files

# Create list of available languages
SUPPORTED_LANGUAGES = [
    "Arabic", "Bengali", "Chinese (Simplified)", "Chinese (Traditional)", 
    "Dutch", "English", "French", "German", "Hindi", "Indonesian", 
    "Italian", "Japanese", "Korean", "Portuguese", "Russian", 
    "Spanish", "Swedish", "Thai", "Turkish", "Vietnamese"
]

LANGUAGE_CODES = {
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Thai": "th",
    "Turkish": "tr",
    "Vietnamese": "vi"
}

# App title and description
st.title("UI String Translator & GitHub Integrator")
st.markdown("""
Create localization files for your application with context-aware translations.
Upload JSON or XML files, or connect to GitHub to automatically scan repositories for translatable strings.
""")

# Initialize session states for projects
if 'projects' not in st.session_state:
    st.session_state.projects = {}

# API Key input
with st.sidebar:
    st.header("Configuration")
    
    # Gemini API Key
    api_key = st.text_input("Enter Gemini API Key", type="password", key="api_key")
    if st.button("Configure Gemini API"):
        if configure_genai():
            st.success("Gemini API configured successfully!")
        else:
            st.error("Please provide a valid Gemini API key")
    
    # GitHub API Token
    github_token = st.text_input("Enter GitHub Token", type="password", key="github_token")
    if st.button("Configure GitHub API"):
        if github_token:
            if configure_github():
                st.success("GitHub API configured successfully!")
            else:
                st.error("Failed to configure GitHub API. Check your token.")
        else:
            st.error("Please provide a GitHub token")

# Main workflow
tabs = st.tabs(["Dashboard", "Upload & Translate", "Review & Edit", "Export"])

# Dashboard tab

# Dashboard tab
with tabs[0]:
    st.header("Translation Projects Dashboard")
    
    # Create new project section
    with st.expander("Create New Project", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name", key="create_project_name")
        with col2:
            project_type = st.selectbox("Project Type", ["Manual Upload", "GitHub Repository"], key="create_project_type")
        
        if project_type == "GitHub Repository":
            # GitHub Repository section
            st.caption("**Enter GitHub Repository URL (include /tree/branch-name for non-default branches)**")
            repo_url = st.text_input("Repository URL", key="create_repo_url", 
                                    placeholder="https://github.com/openMF/mifos-mobile/tree/kmp-impl")
            
            # Add option to use pattern-based search
            use_pattern_search = st.checkbox("Use pattern-based scanning (faster)", value=True, 
                                           help="Scans for strings.xml files in common locations first")
            
            # Display common patterns - updated for Mifos KMP project
            st.caption("**Common string resource patterns for Mifos KMP:**")
            st.code("""

feature/*/src/commonMain/composeResources/values/strings.xml


# Other Compose Multiplatform patterns
*/src/commonMain/composeResources/values/strings.xml

                """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Create & Scan GitHub Project", key="create_github_project_button"):
                    if project_name and repo_url:
                        with st.spinner("Creating project and scanning repository..."):
                            # Create project entry
                            st.session_state.projects[project_name] = {
                                "type": project_type,
                                "repo_url": repo_url,
                                "files": {},
                                "translations": {}
                            }
                            
                            # Extract branch name if present
                            branch_display = "default branch"
                            if "/tree/" in repo_url:
                                branch_display = repo_url.split("/tree/", 1)[1].split("/")[0]
                            
                            # Scan repository for strings.xml files using the improved function
                            string_files = scan_github_repository(repo_url, pattern_search=use_pattern_search)
                            
                            if string_files:
                                st.session_state.projects[project_name]["files"] = string_files
                                st.success(f"Project created! Found {len(string_files)} strings.xml files in {branch_display}.")
                                
                                # Immediately show the found files
                                st.subheader("Found Resource Files")
                                file_data = []
                                for file_path, content in string_files.items():
                                    # Parse file content to get string count
                                    if file_path.endswith(".xml"):
                                        strings_dict = xml_to_strings_dict(content)
                                        string_count = len(strings_dict)
                                    else:
                                        # Assume JSON
                                        try:
                                            strings_dict = json.loads(content)
                                            string_count = len(flatten_json(strings_dict))
                                        except:
                                            string_count = 0
                                    
                                    file_data.append({
                                        "File Path": file_path,
                                        "String Count": string_count
                                    })
                                
                                # Display as dataframe
                                file_df = pd.DataFrame(file_data)
                                st.dataframe(file_df, use_container_width=True)
                                
                                # Add a summary of the feature modules found
                                features_found = set()
                                for file_path in string_files.keys():
                                    if "/feature/" in file_path:
                                        parts = file_path.split("/")
                                        feature_index = parts.index("feature")
                                        if feature_index + 1 < len(parts):
                                            features_found.add(parts[feature_index + 1])
                                
                                if features_found:
                                    st.success(f"Found strings in {len(features_found)} feature modules: {', '.join(features_found)}")
                                
                                # File preview section
                                if file_data:
                                    st.subheader("File Preview")
                                    selected_file = st.selectbox("Select file to preview", list(string_files.keys()), key="dashboard_file_preview_select")
                                    
                                    if selected_file:
                                        file_content = string_files[selected_file]
                                        
                                        if selected_file.endswith(".xml"):
                                            # Parse XML and show as table
                                            strings_dict = xml_to_strings_dict(file_content)
                                            
                                            preview_df = pd.DataFrame({
                                                "Key": list(strings_dict.keys()),
                                                "Value": list(strings_dict.values())
                                            })
                                            
                                            st.dataframe(preview_df, use_container_width=True)
                                            
                                            # Show raw XML with a toggle
                                            if st.checkbox("Show Raw XML", key=f"show_raw_xml_{selected_file.replace('/', '_').replace('.', '_')}", value=False):
                                                st.code(file_content, language="xml")
                                            
                                            # Add translation button for this specific file
                                            col1, col2 = st.columns([1, 2])
                                            with col1:
                                                if st.button("Translate This File", key=f"translate_file_{selected_file.replace('/', '_').replace('.', '_')}"):
                                                    # Store the selected file and strings in session state
                                                    st.session_state.selected_file_for_translation = selected_file
                                                    st.session_state.selected_file_strings = strings_dict
                                                    st.session_state.show_language_dialog_for_file = True
                                                    st.rerun()
                                        else:
                                            # Show JSON
                                            try:
                                                json_content = json.loads(file_content)
                                                flattened = flatten_json(json_content)
                                                
                                                preview_df = pd.DataFrame({
                                                    "Key": list(flattened.keys()),
                                                    "Value": list(flattened.values())
                                                })
                                                
                                                st.dataframe(preview_df, use_container_width=True)
                                                
                                                # Show raw JSON with a toggle
                                                if st.checkbox("Show Raw JSON", key=f"show_raw_json_{selected_file.replace('/', '_').replace('.', '_')}", value=False):
                                                    st.json(json_content)
                                            except:
                                                st.code(file_content)
                            else:
                                st.warning("No strings.xml files found in repository. Try these troubleshooting steps:")
                                st.markdown("""
                                1. Make sure you're specifying the correct branch in the URL (e.g., /tree/kmp-impl)
                                2. Try disabling pattern-based scanning for a full repository scan
                                3. Verify the repository URL is correct
                                4. Make sure your GitHub token has proper access permissions
                                5. Check if the repository has a different structure for string resources
                                """)
                    else:
                        st.error("Please provide both project name and repository URL.")
        else:
            if st.button("Create Upload Project", key="create_upload_project_button"):
                if project_name:
                    st.session_state.projects[project_name] = {
                        "type": project_type,
                        "files": {},
                        "translations": {}
                    }
                    st.success(f"Project '{project_name}' created! Go to Upload & Translate tab to add files.")
                else:
                    st.error("Please provide a project name.")
    
    
    # List existing projects
    st.subheader("Existing Projects")
    
    if not st.session_state.projects:
        st.info("No projects created yet. Use the form above to create a new project.")
    else:
        for project_name, project_data in st.session_state.projects.items():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{project_name}**")
                    st.caption(f"Type: {project_data['type']}")
                    
                    if project_data["type"] == "GitHub Repository":
                        st.caption(f"Repository: {project_data['repo_url']}")
                    
                    # Show file count
                    file_count = len(project_data.get("files", {}))
                    st.caption(f"Files: {file_count}")
                    
                    # Show languages
                    languages = list(project_data.get("translations", {}).keys())
                    if languages:
                        st.caption(f"Languages: {', '.join(languages)}")
                    else:
                        st.caption("No translations yet")
                
                with col2:
                    if st.button("View Files", key=f"view_{project_name}"):
                        # Instead of switching to GitHub tab, expand a section below with file info
                        st.session_state.selected_project = project_name
                        st.session_state.show_project_files = True
                
                with col3:
                    if st.button("Generate Translations", key=f"translate_{project_name}"):
                        st.session_state.selected_project = project_name
                        
                        # Show language selection dialog
                        st.session_state.show_language_dialog = True
                        st.rerun()
                
                st.divider()
    
    # Display project files if requested (instead of switching to GitHub tab)
    if st.session_state.get("show_project_files", False) and st.session_state.get("selected_project"):
        project = st.session_state.projects[st.session_state.selected_project]
        
        st.subheader(f"Files in {st.session_state.selected_project}")
        
        if project["files"]:
            # Add option to rescan the repository
            if project["type"] == "GitHub Repository":
                if st.button("Rescan Repository", key="rescan_repository"):
                    with st.spinner("Rescanning repository..."):
                        repo_url = project["repo_url"]
                        string_files = scan_github_repository(repo_url, pattern_search=True)
                        
                        if string_files:
                            project["files"] = string_files
                            st.success(f"Found {len(string_files)} strings.xml files!")
                            st.rerun()
                        else:
                            st.warning("No strings.xml files found in repository.")
            
            # Create a table of files
            file_data = []
            for file_path, content in project["files"].items():
                # Parse file content to get string count
                if file_path.endswith(".xml"):
                    strings_dict = xml_to_strings_dict(content)
                    string_count = len(strings_dict)
                else:
                    # Assume JSON
                    try:
                        strings_dict = json.loads(content)
                        string_count = len(flatten_json(strings_dict))
                    except:
                        string_count = 0
                
                file_data.append({
                    "File Path": file_path,
                    "String Count": string_count
                })
            
            # Display as dataframe
            file_df = pd.DataFrame(file_data)
            st.dataframe(file_df, use_container_width=True)
            
            # File preview section
            if file_data:
                st.subheader("File Preview")
                
                # Group files by feature module
                grouped_files = {}
                for file_path in project["files"].keys():
                    if "/feature/" in file_path:
                        parts = file_path.split("/")
                        feature_index = parts.index("feature")
                        if feature_index + 1 < len(parts):
                            feature = parts[feature_index + 1]
                            if feature not in grouped_files:
                                grouped_files[feature] = []
                            grouped_files[feature].append(file_path)
                    else:
                        if "Other" not in grouped_files:
                            grouped_files["Other"] = []
                        grouped_files["Other"].append(file_path)
                
                # If we have feature modules, allow selecting by feature first
                if len(grouped_files) > 1:
                    selected_feature = st.selectbox(
                        "Select feature module", 
                        sorted(grouped_files.keys()),
                        key="feature_selector"
                    )
                    
                    file_options = grouped_files[selected_feature]
                else:
                    file_options = list(project["files"].keys())
                
                selected_file = st.selectbox(
                    "Select file to preview", 
                    file_options,
                    key="files_section_preview_select"
                )
                
                if selected_file:
                    file_content = project["files"][selected_file]
                    
                    if selected_file.endswith(".xml"):
                        # Parse XML and show as table
                        strings_dict = xml_to_strings_dict(file_content)
                        
                        preview_df = pd.DataFrame({
                            "Key": list(strings_dict.keys()),
                            "Value": list(strings_dict.values())
                        })
                        
                        st.dataframe(preview_df, use_container_width=True)
                        
                        # Show raw XML with a toggle
                        if st.checkbox("Show Raw XML", key=f"proj_show_raw_xml_{selected_file.replace('/', '_').replace('.', '_')}", value=False):
                            st.code(file_content, language="xml")
                        
                        # Add translation button for this specific file
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            if st.button("Translate This File", key=f"proj_files_translate_{selected_file.replace('/', '_').replace('.', '_')}"):
                                # Store the selected file and strings in session state
                                st.session_state.selected_file_for_translation = selected_file
                                st.session_state.selected_file_strings = strings_dict
                                st.session_state.show_language_dialog_for_file = True
                                st.rerun()
                    else:
                        # Show JSON
                        try:
                            json_content = json.loads(file_content)
                            flattened = flatten_json(json_content)
                            
                            preview_df = pd.DataFrame({
                                "Key": list(flattened.keys()),
                                "Value": list(flattened.values())
                            })
                            
                            st.dataframe(preview_df, use_container_width=True)
                            
                            # Show raw JSON with a toggle
                            if st.checkbox("Show Raw JSON", key=f"proj_show_raw_json_{selected_file.replace('/', '_').replace('.', '_')}", value=False):
                                st.json(json_content)
                        except:
                            st.code(file_content)
            
            # Hide files button
            if st.button("Hide Files", key="hide_project_files"):
                st.session_state.show_project_files = False
                st.rerun()
        else:
            st.info("No string resource files found in this project.")
            
            # If GitHub project, add scan button
            if project["type"] == "GitHub Repository":
                if st.button("Scan Repository Now", key="scan_empty_project"):
                    with st.spinner("Scanning repository..."):
                        repo_url = project["repo_url"]
                        string_files = scan_github_repository(repo_url, pattern_search=True)
                        
                        if string_files:
                            project["files"] = string_files
                            st.success(f"Found {len(string_files)} strings.xml files!")
                            st.rerun()
                        else:
                            st.warning("No strings.xml files found in repository. Try disabling pattern-based scanning.")
                            
                            # Provide option for full scan
                            if st.button("Try Full Repository Scan (Slower)", key="full_scan_button"):
                                with st.spinner("Performing full repository scan..."):
                                    repo_url = project["repo_url"]
                                    string_files = scan_github_repository(repo_url, pattern_search=False)
                                    
                                    if string_files:
                                        project["files"] = string_files
                                        st.success(f"Found {len(string_files)} strings.xml files!")
                                        st.rerun()
                                    else:
                                        st.error("No strings.xml files found in repository. Please check the repository structure.")
    
    # Language selection dialog for specific file
    if st.session_state.get("show_language_dialog_for_file", False):
        with st.form("file_language_selection_form"):
            st.subheader(f"Generate Translations for {st.session_state.selected_file_for_translation}")
            
            selected_languages = st.multiselect(
                "Select target languages",
                SUPPORTED_LANGUAGES,
                default=["Spanish", "French", "German"],
                key="file_languages_dialog_select"
            )
            
            submitted = st.form_submit_button("Generate Translations")
            
            if submitted:
                if selected_languages:
                    # Start translation process for the specific file
                    project = st.session_state.projects[st.session_state.selected_project]
                    
                    with st.spinner("Generating translations..."):
                        # Get the strings to translate
                        strings_dict = st.session_state.selected_file_strings
                        file_path = st.session_state.selected_file_for_translation
                        
                        # Initialize translations dictionary if needed
                        if "file_translations" not in project:
                            project["file_translations"] = {}
                        
                        if file_path not in project["file_translations"]:
                            project["file_translations"][file_path] = {}
                        
                        # Store original strings as English
                        project["file_translations"][file_path]["en"] = strings_dict
                        
                        # Translate to each selected language
                        for language in selected_languages:
                            lang_code = LANGUAGE_CODES.get(language)
                            if lang_code and lang_code != "en":
                                st.text(f"Translating to {language}...")
                                
                                translations = translate_all_strings(
                                    strings_dict, 
                                    language
                                )
                                
                                # Store translations
                                project["file_translations"][file_path][lang_code] = translations
                    
                    st.success(f"Generated translations for file in {len(selected_languages)} languages!")
                    st.session_state.show_language_dialog_for_file = False
                    
                    # Navigate to review tab for this specific file
                    st.session_state.active_tab = "Review & Edit"
                    st.session_state.review_file_path = file_path
                    st.rerun()
                else:
                    st.error("Please select at least one language.")
with tabs[1]:
    st.header("Step 1: Upload JSON or XML File")
    
    # Project selection
    upload_project = st.selectbox(
        "Select project for upload",
        [p for p, data in st.session_state.projects.items() if data["type"] == "Manual Upload"],
        key="upload_project_selector"
    )
    
    uploaded_file = st.file_uploader("Choose a file", type=["json", "xml"])
    
    if uploaded_file is not None and upload_project:
        try:
            # Load and parse the file
            file_content = uploaded_file.read().decode()
            
            if uploaded_file.name.endswith(".json"):
                # Parse JSON file
                content = json.loads(file_content)
                flattened_content = flatten_json(content)
                
                # Store in session state and project
                st.session_state.original_content = content
                st.session_state.flattened_content = flattened_content
                
                # Add to project files
                st.session_state.projects[upload_project]["files"][uploaded_file.name] = file_content
                
                # Display preview
                st.success(f"File loaded successfully! Found {len(flattened_content)} strings.")
                
                # Count string values (non-nested objects)
                string_count = sum(1 for v in flattened_content.values() if isinstance(v, str))
                st.info(f"Found {string_count} translatable text strings and {len(flattened_content) - string_count} nested objects.")
                
                preview_df = pd.DataFrame(
                    {"Key": list(flattened_content.keys())[:5], 
                     "Value": list(flattened_content.values())[:5]}
                )
                st.dataframe(preview_df, use_container_width=True)
                
            elif uploaded_file.name.endswith(".xml"):
                # Parse XML file
                strings_dict = xml_to_strings_dict(file_content)
                
                # Store in session state and project
                st.session_state.original_content = strings_dict
                st.session_state.flattened_content = strings_dict
                
                # Add to project files
                st.session_state.projects[upload_project]["files"][uploaded_file.name] = file_content
                
                # Display preview
                st.success(f"File loaded successfully! Found {len(strings_dict)} strings.")
                
                preview_df = pd.DataFrame(
                    {"Key": list(strings_dict.keys())[:5],
                     "Value": list(strings_dict.values())[:5]}
                )
                st.dataframe(preview_df, use_container_width=True)
            
            # Add file summary
            with st.expander("View File Structure Summary"):
                # For JSON files
                if uploaded_file.name.endswith(".json"):
                    # Get top-level keys and count of nested elements
                    top_levels = {}
                    for key in flattened_content.keys():
                        top_level = key.split('.')[0]
                        if top_level in top_levels:
                            top_levels[top_level] += 1
                        else:
                            top_levels[top_level] = 1
                    
                    # Display as a summary
                    st.write("File structure:")
                    for section, count in top_levels.items():
                        st.write(f"- {section}: {count} elements")
                # For XML files
                else:
                    st.write(f"XML structure: {len(strings_dict)} string elements")
            
            # Context addition section
            st.header("Step 2: Add Context (Optional)")
            st.info("You can add context for specific keys to improve translation quality.")
            
            if 'contexts' not in st.session_state:
                st.session_state.contexts = {}
            
            # Interface for adding context
            selected_key = st.selectbox("Select key to add context", list(st.session_state.flattened_content.keys()), key="context_key_selector")
            current_context = st.session_state.contexts.get(selected_key, "")
            
            context = st.text_area(
                "Enter context for this string (e.g., 'This appears on a login button')",
                value=current_context,
                key="context_text_area"
            )
            
            if st.button("Save Context", key="save_context_button"):
                st.session_state.contexts[selected_key] = context
                st.success(f"Context saved for '{selected_key}'")
            
            # Display saved contexts
            if st.session_state.contexts:
                st.subheader("Saved Contexts")
                contexts_df = pd.DataFrame(
                    {"Key": list(st.session_state.contexts.keys()),
                     "Context": list(st.session_state.contexts.values())}
                )
                st.dataframe(contexts_df, use_container_width=True)
            
            # Translation step
            st.header("Step 3: Translate")
            
            # Show language selection multiselect
            selected_languages = st.multiselect(
                "Select target languages",
                SUPPORTED_LANGUAGES,
                default=["Spanish", "French", "German"],
                key="upload_target_languages_select"
            )
            
            if st.button("Start Translation") and selected_languages and configure_genai():
                if 'translations' not in st.session_state:
                    st.session_state.translations = {}
                
                project = st.session_state.projects[upload_project]
                if "translations" not in project:
                    project["translations"] = {}
                
                # Store original strings as English
                project["translations"]["en"] = st.session_state.flattened_content
                
                # Translate to each selected language
                for language in selected_languages:
                    lang_code = LANGUAGE_CODES.get(language)
                    if lang_code and lang_code != "en":
                        with st.spinner(f"Translating to {language}..."):
                            translations = translate_all_strings(
                                st.session_state.flattened_content, 
                                language, 
                                st.session_state.contexts
                            )
                            
                            # Store translations
                            project["translations"][lang_code] = translations
                            st.session_state.translations[lang_code] = translations
                
                st.success(f"Translated to {len(selected_languages)} languages!")
                
                # Navigate to review tab
                st.session_state.active_tab = "Review & Edit"
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        if not upload_project and st.session_state.projects:
            st.warning("Please select a project first or create a new one in the Dashboard tab.")

# GitHub Integration tab
with tabs[2]:
    st.header("GitHub Repository Integration")
    
    # Check if a project is selected from the dashboard
    selected_project = st.session_state.get("selected_project")
    
    if selected_project and st.session_state.projects[selected_project]["type"] == "GitHub Repository":
        project = st.session_state.projects[selected_project]
        
        st.subheader(f"Project: {selected_project}")
        st.write(f"Repository: {project['repo_url']}")
        
        # Display found strings.xml files
        st.subheader("Found Resource Files")
        
        if project["files"]:
            # Create a table of files
            file_data = []
            for file_path, content in project["files"].items():
                # Parse file content to get string count
                if file_path.endswith(".xml"):
                    strings_dict = xml_to_strings_dict(content)
                    string_count = len(strings_dict)
                else:
                    # Assume JSON
                    strings_dict = json.loads(content)
                    string_count = len(flatten_json(strings_dict))
                
                file_data.append({
                    "File Path": file_path,
                    "String Count": string_count
                })
            
            # Display as dataframe
            file_df = pd.DataFrame(file_data)
            st.dataframe(file_df, width=1000, use_container_width=True)
            
            # File preview section
            st.subheader("File Preview")
            
            selected_file = st.selectbox("Select file to preview", list(project["files"].keys()), key="github_file_preview_select")
            
            if selected_file:
                file_content = project["files"][selected_file]
                
                if selected_file.endswith(".xml"):
                    # Parse XML and show as table
                    strings_dict = xml_to_strings_dict(file_content)
                    
                    preview_df = pd.DataFrame({
                        "Key": list(strings_dict.keys()),
                        "Value": list(strings_dict.values())
                    })
                    
                    st.dataframe(file_df, width=1000, use_container_width=True)

                    # Also show raw XML in expander
                    with st.expander("Raw XML"):
                        st.code(file_content, language="xml")
                    
                    # Add translation button for this specific file
                    if st.button("Translate This File", key=f"translate_file_{selected_file.replace('/', '_')}"):
                        # Store the selected file and strings in session state
                        st.session_state.selected_file_for_translation = selected_file
                        st.session_state.selected_file_strings = strings_dict
                        st.session_state.show_language_dialog_for_file = True
                        st.rerun()
                else:
                    # Show JSON
                    try:
                        json_content = json.loads(file_content)
                        flattened = flatten_json(json_content)
                        
                        preview_df = pd.DataFrame({
                            "Key": list(flattened.keys()),
                            "Value": list(flattened.values())
                        })
                        
                        st.dataframe(preview_df, use_container_width=True)
                        
                        # Also show raw JSON in expander
                        with st.expander("Raw JSON"):
                            st.json(json_content)
                        
                        # Add translation button for this specific file
                        if st.button("Translate This File", key=f"translate_file_{selected_file.replace('/', '_')}"):
                            # Store the selected file and strings in session state
                            st.session_state.selected_file_for_translation = selected_file
                            st.session_state.selected_file_strings = flattened
                            st.session_state.show_language_dialog_for_file = True
                            st.rerun()
                    except:
                        st.code(file_content)
            
            # Replace the "Translate All Files" button with a note about individual file translation
            st.info("Select a file above and click 'Translate This File' to generate translations for specific files.")
        else:
            st.info("No string resource files found in this repository.")
            
            # Manual scan button
            if st.button("Scan Repository Again"):
                with st.spinner("Scanning repository..."):
                    string_files = scan_github_repository(project["repo_url"])
                    
                    if string_files:
                        project["files"] = string_files
                        st.success(f"Found {len(string_files)} strings.xml files!")
                        st.experimental_rerun()
                    else:
                        st.warning("No strings.xml files found in repository.")
    else:
        # Show repository scan form if no project selected
        st.subheader("Scan GitHub Repository")
        
        repo_url = st.text_input("GitHub Repository URL (e.g., https://github.com/username/repo)", key="github_scan_repo_url")
        
        if st.button("Scan Repository", key="github_scan_button"):
            if repo_url and configure_github():
                with st.spinner("Scanning repository..."):
                    string_files = scan_github_repository(repo_url)
                    
                    if string_files:
                        # Create a new project for this repository
                        project_name = repo_url.split("/")[-1]
                        st.session_state.projects[project_name] = {
                            "type": "GitHub Repository",
                            "repo_url": repo_url,
                            "files": string_files,
                            "translations": {}
                        }
                        
                        st.session_state.selected_project = project_name
                        st.success(f"Found {len(string_files)} strings.xml files! Project '{project_name}' created.")
                        st.rerun()
                    else:
                        st.warning("No strings.xml files found in repository.")
            else:
                st.error("Please provide a valid GitHub repository URL and configure GitHub API.")

# Review & Edit tab
# Review & Edit tab
with tabs[3]:
    st.header("Review and Edit Translations")
    
    # Select project
    projects_with_translations = [p for p, data in st.session_state.projects.items() 
                                if data.get("translations") or data.get("file_translations")]
    
    if projects_with_translations:
        selected_review_project = st.selectbox(
            "Select project to review", 
            projects_with_translations,
            key="review_project_selector"
        )
        
        if selected_review_project:
            project = st.session_state.projects[selected_review_project]
            
            # Check if we have file-specific translations
            has_file_translations = "file_translations" in project and project["file_translations"]
            has_project_translations = "translations" in project and project["translations"]
            
            if has_file_translations:
                # File selection for projects with file-specific translations
                st.subheader("Select File")
                
                # Default to the file that was just translated if set
                default_file_index = 0
                file_paths = list(project["file_translations"].keys())
                
                if st.session_state.get("review_file_path") in file_paths:
                    default_file_index = file_paths.index(st.session_state.get("review_file_path"))
                
                selected_file = st.selectbox(
                    "Select file to review",
                    file_paths,
                    index=default_file_index,
                    key="review_file_selector"
                )
                
                file_translations = project["file_translations"][selected_file]
                available_languages = list(file_translations.keys())
                
                # Language selection
                selected_language = st.selectbox(
                    "Select language to review",
                    available_languages,
                    format_func=lambda x: next((lang for lang, code in LANGUAGE_CODES.items() if code == x), x),
                    key="review_file_language_selector"
                )
                
                if selected_language:
                    translations = file_translations[selected_language]
                    
                    # Add search functionality
                    search_query = st.text_input("Search keys or translations", "", key=f"search_file_query_{selected_language}")
                    
                    # Create a dataframe for display and editing
                    if selected_language == "en":
                        # For English (source language), show only key and value
                        data = {
                            "Key": list(translations.keys()),
                            "Value": list(translations.values())
                        }
                    else:
                        # For other languages, show key, original (English) and translation
                        data = {
                            "Key": list(translations.keys()),
                            "Original": [file_translations["en"].get(k, "") for k in translations.keys()],
                            "Translation": list(translations.values())
                        }
                    
                    df = pd.DataFrame(data)
                    
                    # Filter based on search query if provided
                    if search_query:
                        if "Original" in df.columns:
                            df = df[
                                df["Key"].str.contains(search_query, case=False) | 
                                df["Original"].astype(str).str.contains(search_query, case=False) | 
                                df["Translation"].astype(str).str.contains(search_query, case=False)
                            ]
                        else:
                            df = df[
                                df["Key"].str.contains(search_query, case=False) | 
                                df["Value"].astype(str).str.contains(search_query, case=False)
                            ]
                    
                    # Display as editable dataframe
                    edited_df = st.data_editor(df, use_container_width=True, 
                                              key=f"file_translation_editor_{selected_file}_{selected_language}")
                    
                    # Save edited translations
                    if st.button("Save Edited Translations", key=f"save_file_translations_{selected_file}"):
                        # Update file translations
                        if selected_language == "en":
                            for i, row in edited_df.iterrows():
                                key = row["Key"]
                                value = row["Value"]
                                file_translations[selected_language][key] = value
                        else:
                            for i, row in edited_df.iterrows():
                                key = row["Key"]
                                translation = row["Translation"]
                                file_translations[selected_language][key] = translation
                                
                        st.success("Translations updated!")
                
            elif has_project_translations:
                # Traditional project-wide translations
                available_languages = list(project["translations"].keys())
                
                # Language selection
                selected_language = st.selectbox(
                    "Select language to review",
                    available_languages,
                    format_func=lambda x: next((lang for lang, code in LANGUAGE_CODES.items() if code == x), x),
                    key="review_language_selector"
                )
                
                if selected_language:
                    translations = project["translations"][selected_language]
                    
                    # Add search functionality
                    search_query = st.text_input("Search keys or translations", "", key=f"search_query_{selected_language}")
                    
                    # Create a dataframe for display and editing
                    if selected_language == "en":
                        # For English (source language), show only key and value
                        data = {
                            "Key": list(translations.keys()),
                            "Value": list(translations.values())
                        }
                    else:
                        # For other languages, show key, original (English) and translation
                        data = {
                            "Key": list(translations.keys()),
                            "Original": [project["translations"]["en"].get(k, "") for k in translations.keys()],
                            "Translation": list(translations.values())
                        }
                    
                    df = pd.DataFrame(data)
                    
                    # Filter based on search query if provided
                    if search_query:
                        if "Original" in df.columns:
                            df = df[
                                df["Key"].str.contains(search_query, case=False) | 
                                df["Original"].astype(str).str.contains(search_query, case=False) | 
                                df["Translation"].astype(str).str.contains(search_query, case=False)
                            ]
                        else:
                            df = df[
                                df["Key"].str.contains(search_query, case=False) | 
                                df["Value"].astype(str).str.contains(search_query, case=False)
                            ]
                    
                    # Display as editable dataframe
                    edited_df = st.data_editor(df, use_container_width=True, 
                                              key=f"translation_editor_{selected_review_project}_{selected_language}")
                    
                    # Save edited translations
                    if st.button("Save Edited Translations", key="save_project_translations"):
                        # Update project translations
                        if selected_language == "en":
                            for i, row in edited_df.iterrows():
                                key = row["Key"]
                                value = row["Value"]
                                project["translations"][selected_language][key] = value
                        else:
                            for i, row in edited_df.iterrows():
                                key = row["Key"]
                                translation = row["Translation"]
                                project["translations"][selected_language][key] = translation
                                
                        st.success("Translations updated!")
            else:
                st.info("No translations available for this project yet.")
        else:
            st.info("Please select a project to review.")
    else:
        st.info("No projects with translations available yet. Please translate a project first.")

# Initialize session state for the first run
if 'original_content' not in st.session_state:
    st.session_state.original_content = {}

if 'flattened_content' not in st.session_state:
    st.session_state.flattened_content = {}

if 'contexts' not in st.session_state:
    st.session_state.contexts = {}

if 'translations' not in st.session_state:
    st.session_state.translations = {}

if 'string_files' not in st.session_state:
    st.session_state.string_files = {}

if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

if 'show_language_dialog' not in st.session_state:
    st.session_state.show_language_dialog = False

if 'selected_file_for_translation' not in st.session_state:
    st.session_state.selected_file_for_translation = None

if 'selected_file_strings' not in st.session_state:
    st.session_state.selected_file_strings = {}

if 'show_language_dialog_for_file' not in st.session_state:
    st.session_state.show_language_dialog_for_file = False

if 'review_file_path' not in st.session_state:
    st.session_state.review_file_path = None

# Add new session state variables for the integrated GitHub functionality
if 'show_project_files' not in st.session_state:
    st.session_state.show_project_files = False