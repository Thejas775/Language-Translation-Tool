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

# Initialize session state variables early
if 'page' not in st.session_state:
    st.session_state.page = "📚 Home"
if 'sidebar_expanded' not in st.session_state:
    st.session_state.sidebar_expanded = False
if 'projects' not in st.session_state:
    st.session_state.projects = {}
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
if 'show_project_files' not in st.session_state:
    st.session_state.show_project_files = False

# Set page configuration
st.set_page_config(
    page_title="UI String Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed" if not st.session_state.sidebar_expanded else "expanded"
)

# Add custom CSS for modern UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Card-like containers */
    .stApp div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Headings */
    h1 {
        color: #1E3A8A;
        font-weight: 700 !important;
        margin-bottom: 24px !important;
    }
    
    h2 {
        color: #2563EB;
        font-weight: 600 !important;
        margin: 20px 0 !important;
    }
    
    h3 {
        color: #3B82F6;
        font-weight: 500 !important;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    /* Primary button */
    .stButton > button[data-baseweb="button"] {
        background-color: #2563EB;
        border: none;
    }
    
    .stButton > button[data-baseweb="button"]:hover {
        background-color: #1E40AF;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Progress bar */
    div[data-testid="stProgressBar"] {
        background-color: #E5E7EB;
    }
    
    div[data-testid="stProgressBar"] > div {
        background-color: #3B82F6 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        color: white;
    }
    
    section[data-testid="stSidebar"] button {
        background-color: #3B82F6;
        color: white;
        border: none;
    }
    
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 {
        color: white;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #4B5563;
    }
    
    /* Success messages */
    div[data-baseweb="notification"] {
        border-radius: 6px;
    }
    
    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    /* File uploader */
    .stFileUploader > div {
        border-radius: 6px;
    }
    
    /* Status text */
    .status-info {
        background-color: #EFF6FF;
        padding: 10px 15px;
        border-radius: 6px;
        border-left: 4px solid #3B82F6;
        margin: 10px 0;
    }
    
    .status-success {
        background-color: #ECFDF5;
        padding: 10px 15px;
        border-radius: 6px;
        border-left: 4px solid #10B981;
        margin: 10px 0;
    }
    
    .status-warning {
        background-color: #FFFBEB;
        padding: 10px 15px;
        border-radius: 6px;
        border-left: 4px solid #F59E0B;
        margin: 10px 0;
    }
    
    .status-error {
        background-color: #FEF2F2;
        padding: 10px 15px;
        border-radius: 6px;
        border-left: 4px solid #EF4444;
        margin: 10px 0;
    }
    
    /* Icons */
    .icon-text {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Hero section */
    .hero-section {
        padding: 40px 0;
        text-align: center;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .hero-section h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800 !important;
        margin-bottom: 16px !important;
    }
    
    .hero-section p {
        font-size: 1.2rem;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto 30px auto;
    }
    
    /* Cards for features */
    .feature-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    .feature-card h3 {
        color: #1E3A8A;
        margin-bottom: 15px;
    }
    
    /* Nav section */
    .nav-section {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 30px 0;
    }
    
    .nav-button {
        background-color: white;
        color: #2563EB;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 500;
        border: 1px solid #E5E7EB;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background-color: #2563EB;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Configure the Gemini API
def configure_genai():
    # First try to get the API key from Streamlit secrets
    api_key = None
    
    # Try getting from Streamlit secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        # If not in secrets, try environment variables
        api_key = os.getenv('GEMINI_API_KEY')
        
    # If still not found, check session state (from sidebar input)
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
    # First try to get the token from Streamlit secrets
    github_token = None
    
    # Try getting from Streamlit secrets
    try:
        github_token = st.secrets["GITHUB_TOKEN"]
    except:
        # If not in secrets, try environment variables
        github_token = os.getenv('GITHUB_TOKEN')
    
    # If still not found, check session state (from sidebar input)
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
            st.markdown(f"<div class='status-info'>Scanning branch: {branch}</div>", unsafe_allow_html=True)
            # Verify the branch exists
            try:
                repo.get_branch(branch)
            except Exception as e:
                st.markdown(f"<div class='status-error'>Branch '{branch}' not found. Error: {str(e)}</div>", unsafe_allow_html=True)
                return {}
        else:
            # Otherwise use the default branch
            branch = repo.default_branch
            st.markdown(f"<div class='status-info'>Using default branch: {branch}</div>", unsafe_allow_html=True)
        
        # Common patterns where strings.xml files are typically located
        common_patterns = [
            # Mifos KMP specific patterns - prioritize these
            "feature/*/src/commonMain/composeResources/values/strings.xml",
            "feature/*/src/*/composeResources/values/strings.xml",
            "feature/*/src/*/resources/values/strings.xml",
            
            # KMM/Compose Multiplatform patterns
            "*/src/commonMain/composeResources/values/strings.xml",
            "*/*/src/commonMain/composeResources/values/strings.xml",
            "*/src/commonMain/resources/MR/base/strings.xml",
            "*/*/src/commonMain/resources/MR/base/strings.xml",
            
            # Android module patterns
            "*/src/main/res/values/strings.xml",
            "*/*/src/main/res/values/strings.xml",
            "feature/*/src/main/res/values/strings.xml",
            
            # General fallbacks
            "**/values/strings.xml",
            "**/values-*/strings.xml"
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
        st.markdown("<div class='status-info'>Pattern search didn't find strings.xml files. Performing a full repository scan (this may take longer)...</div>", unsafe_allow_html=True)
        return search_files_in_repo(repo, "strings.xml", branch)
            
    except Exception as e:
        st.markdown(f"<div class='status-error'>Error scanning repository: {str(e)}</div>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='status-error'>Error parsing XML: {str(e)}</div>", unsafe_allow_html=True)
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
            st.markdown("<div class='status-info'>Input is too large for a single API call. Switching to batch mode...</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='status-warning'>Failed to parse response. Switching to batch mode...</div>", unsafe_allow_html=True)
        return batch_translate_texts(string_contents, target_language, contexts_dict)
            
    except Exception as e:
        st.markdown(f"<div class='status-error'>Translation error: {str(e)}</div>", unsafe_allow_html=True)
        # Fall back to batch translation
        st.markdown("<div class='status-warning'>Error in single API call. Switching to batch mode...</div>", unsafe_allow_html=True)
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
            
            status_text.markdown(f"<div class='status-info'>Translating batch {current_batch} of {total_batches} ({len(batch)} strings)</div>", unsafe_allow_html=True)
            
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
                        st.markdown(f"<div class='status-warning'>Failed to parse batch {current_batch}. Retrying ({retry + 1}/{max_retries})...</div>", unsafe_allow_html=True)
                        time.sleep(2)  # Wait a bit before retrying
                    else:
                        st.markdown(f"<div class='status-error'>Failed to translate batch {current_batch} after {max_retries} attempts. Skipping batch.</div>", unsafe_allow_html=True)
                        # Add batch keys with original values to show something rather than nothing
                        for key, text in batch:
                            if key not in all_results:
                                all_results[key] = text  # Use original as fallback
                
                except Exception as batch_error:
                    if retry < max_retries - 1:
                        st.markdown(f"<div class='status-warning'>Error in batch {current_batch}: {str(batch_error)}. Retrying ({retry + 1}/{max_retries})...</div>", unsafe_allow_html=True)
                        time.sleep(2)  # Wait a bit before retrying
                    else:
                        st.markdown(f"<div class='status-error'>Failed to process batch {current_batch} after {max_retries} attempts. Skipping batch.</div>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='status-error'>Batch translation error: {str(e)}</div>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='status-error'>Single translation error: {str(e)}</div>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='status-error'>Error parsing XML: {str(e)}</div>", unsafe_allow_html=True)
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

# Initialize session states for projects
if 'projects' not in st.session_state:
    st.session_state.projects = {}

# Configuration sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/7/76/Translate_icon.png", width=50)
    st.markdown("<h2 style='color:white;'>App Configuration</h2>", unsafe_allow_html=True)
    
    # Only display configuration when show_configuration is True
    with st.expander("🔑 API Configuration", expanded=False):        
        # Gemini API Key
        api_key = st.text_input("Gemini API Key", type="password", key="api_key")
        if st.button("Configure Gemini API"):
            if api_key:
                if configure_genai():
                    st.markdown("<div class='status-success'>Gemini API configured successfully!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='status-error'>Please provide a valid Gemini API key</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-error'>Please provide a Gemini API key</div>", unsafe_allow_html=True)
        
        # GitHub API Token
        github_token = st.text_input("GitHub Token", type="password", key="github_token")
        if st.button("Configure GitHub API"):
            if github_token:
                if configure_github():
                    st.markdown("<div class='status-success'>GitHub API configured successfully!</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='status-error'>Failed to configure GitHub API. Check your token.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-error'>Please provide a GitHub token</div>", unsafe_allow_html=True)

    # Navigation
    st.markdown("<h3 style='color:white;'>Navigation</h3>", unsafe_allow_html=True)
    
    # Use on_change to update session state
    def change_page():
        st.session_state.page = st.session_state.page_selection
    
    page = st.radio(
        "Select Page",
        ["📚 Home", "📋 Projects", "🔄 Translation Review", "📤 Export"],
        key="page_selection",
        index=["📚 Home", "📋 Projects", "🔄 Translation Review", "📤 Export"].index(st.session_state.page),
        on_change=change_page
    )

    # Quick how-to guide in the sidebar
    with st.expander("❓ How to use", expanded=False):
        st.markdown("""
        1. Configure API keys in the sidebar
        2. Create a new project
        3. Select source files (upload or GitHub)
        4. Choose languages to translate to
        5. Review and edit translations
        6. Export translations in desired format
        """)

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

# Add new session state variables for navigation
if 'page' not in st.session_state:
    st.session_state.page = "📚 Home"

# Landing Page
if st.session_state.page == "📚 Home":
    # Hero section
    st.markdown("""
    <div class="hero-section">
        <h1>Welcome to UI String Translator</h1>
        <p>The most efficient way to localize your applications with high-quality, context-aware translations across multiple languages.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Features Section
    st.markdown("## Main Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 Automatic Repository Scanning</h3>
            <p>Connect your GitHub repository and we'll automatically find all your localizable string resources with intelligent pattern matching.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 Context-Aware AI Translation</h3>
            <p>Our Gemini-powered translation engine understands UI context to deliver natural, accurate translations that fit perfectly in your interface.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🌐 20+ Languages Supported</h3>
            <p>Localize your application into all major world languages with just a few clicks, reaching a global audience instantly.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("## How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3>1. Connect</h3>
            <p>Link your GitHub repository or upload your string resources directly.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3>2. Select</h3>
            <p>Choose the languages you want to translate your content into.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3>3. Review</h3>
            <p>Verify and refine the AI-generated translations as needed.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <h3>4. Export</h3>
            <p>Download your translations in the format that fits your project.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Center the button and make it more prominent
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        # Get Started Button - using proper Streamlit functionality
        def go_to_projects():
            st.session_state.page = "📋 Projects"
            # Force sidebar to open
            st.session_state.sidebar_expanded = True
        
        st.button("🚀 Get Started Now", 
                on_click=go_to_projects,
                use_container_width=True,
                type="primary",
                key="get_started_btn")
    
    # Testimonials or Stats
    st.markdown("## Why Choose UI String Translator?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 50% Time Savings</h3>
            <p>Reduce localization time by half compared to traditional methods with our AI-powered workflow.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 95% Translation Accuracy</h3>
            <p>Our context-aware AI delivers translations that require minimal human editing.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>💼 Enterprise Ready</h3>
            <p>Secure, scalable, and ready for integration with your existing development workflow.</p>
        </div>
        """, unsafe_allow_html=True)

# Projects Dashboard
elif st.session_state.page == "📋 Projects":
    st.markdown("<h1>Projects Dashboard</h1>", unsafe_allow_html=True)
    
    # Create new project section
    with st.expander("➕ Create New Project", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name", key="create_project_name")
        with col2:
            project_type = st.selectbox("Project Type", ["Manual Upload", "GitHub Repository"], key="create_project_type")
        
        if project_type == "GitHub Repository":
            # GitHub Repository section
            st.markdown("**Enter GitHub Repository URL (include /tree/branch-name for non-default branches)**")
            repo_url = st.text_input("Repository URL", key="create_repo_url", 
                                    placeholder="https://github.com/openMF/mifos-mobile/tree/kmp-impl")
            
            # Add option to use pattern-based search
            use_pattern_search = st.checkbox("Use pattern-based scanning (faster)", value=True, 
                                           help="Scans for strings.xml files in common locations first")
            
            # Display common patterns - updated for Mifos KMP project
            st.markdown("**Common string resource patterns:**")
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
                                st.markdown(f"<div class='status-success'>Project created! Found {len(string_files)} strings.xml files in {branch_display}.</div>", unsafe_allow_html=True)
                                
                                # Immediately show the found files
                                st.markdown("### Found Resource Files")
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
                                    st.markdown(f"<div class='status-success'>Found strings in {len(features_found)} feature modules: {', '.join(features_found)}</div>", unsafe_allow_html=True)
                                
                                # File preview section
                                if file_data:
                                    st.markdown("### File Preview")
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
                                st.markdown("""
                                <div class='status-warning'>No strings.xml files found in repository. Try these troubleshooting steps:</div>
                                
                                1. Make sure you're specifying the correct branch in the URL (e.g., /tree/kmp-impl)
                                2. Try disabling pattern-based scanning for a full repository scan
                                3. Verify the repository URL is correct
                                4. Make sure your GitHub token has proper access permissions
                                5. Check if the repository has a different structure for string resources
                                """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='status-error'>Please provide both project name and repository URL.</div>", unsafe_allow_html=True)
        else:
            # File upload option
            uploaded_file = st.file_uploader("Choose a strings file", type=["json", "xml"])
            
            if uploaded_file is not None:
                try:
                    # Load and parse the file
                    file_content = uploaded_file.read().decode()
                    
                    # Preview the file
                    if uploaded_file.name.endswith(".json"):
                        # Parse JSON file
                        content = json.loads(file_content)
                        flattened_content = flatten_json(content)
                        
                        # Display preview
                        st.markdown("<div class='status-success'>File loaded successfully!</div>", unsafe_allow_html=True)
                        st.markdown(f"Found {len(flattened_content)} strings.")
                        
                        preview_df = pd.DataFrame(
                            {"Key": list(flattened_content.keys())[:5], 
                            "Value": list(flattened_content.values())[:5]}
                        )
                        st.dataframe(preview_df, use_container_width=True)
                        
                    elif uploaded_file.name.endswith(".xml"):
                        # Parse XML file
                        strings_dict = xml_to_strings_dict(file_content)
                        
                        # Display preview
                        st.markdown("<div class='status-success'>File loaded successfully!</div>", unsafe_allow_html=True)
                        st.markdown(f"Found {len(strings_dict)} strings.")
                        
                        preview_df = pd.DataFrame(
                            {"Key": list(strings_dict.keys())[:5],
                            "Value": list(strings_dict.values())[:5]}
                        )
                        st.dataframe(preview_df, use_container_width=True)
                        
                    # Create project button
                    if st.button("Create Upload Project", key="create_upload_project_button"):
                        if project_name:
                            st.session_state.projects[project_name] = {
                                "type": "Manual Upload",
                                "files": {uploaded_file.name: file_content},
                                "translations": {}
                            }
                            
                            # Store the file content in the appropriate format
                            if uploaded_file.name.endswith(".json"):
                                # Add to project translations
                                st.session_state.projects[project_name]["translations"]["en"] = flattened_content
                            elif uploaded_file.name.endswith(".xml"):
                                # Add to project translations
                                st.session_state.projects[project_name]["translations"]["en"] = strings_dict
                                
                            st.markdown(f"<div class='status-success'>Project '{project_name}' created successfully!</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='status-error'>Please provide a project name.</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"<div class='status-error'>Error processing file: {str(e)}</div>", unsafe_allow_html=True)
            else:
                if st.button("Create Upload Project", key="create_empty_project_button"):
                    if project_name:
                        st.session_state.projects[project_name] = {
                            "type": "Manual Upload",
                            "files": {},
                            "translations": {}
                        }
                        st.markdown(f"<div class='status-success'>Project '{project_name}' created! Please upload files to translate.</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='status-error'>Please provide a project name.</div>", unsafe_allow_html=True)

    # List existing projects
    st.markdown("## Your Projects")
    
    if not st.session_state.projects:
        st.markdown("""
        <div class="feature-card" style="text-align:center; padding: 40px;">
            <h3>No projects yet</h3>
            <p>Create your first project above to get started with translations.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display projects in a grid
        projects_list = list(st.session_state.projects.items())
        for i in range(0, len(projects_list), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(projects_list):
                    project_name, project_data = projects_list[i + j]
                    with cols[j]:
                        st.markdown(f"""
                        <div class="feature-card">
                            <h3>{project_name}</h3>
                            <p>Type: {project_data["type"]}</p>
                            <p>Files: {len(project_data.get("files", {}))}</p>
                            <p>Languages: {', '.join(project_data.get("translations", {}).keys()) or "None yet"}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("View Files", key=f"view_{project_name}"):
                                st.session_state.selected_project = project_name
                                st.session_state.show_project_files = True
                                st.rerun()
                        with col2:
                            if st.button("Translate", key=f"translate_{project_name}"):
                                st.session_state.selected_project = project_name
                                st.session_state.show_language_dialog = True
                                st.rerun()
    
    # Display project files if requested
    if st.session_state.get("show_project_files", False) and st.session_state.get("selected_project"):
        project = st.session_state.projects[st.session_state.selected_project]
        
        st.markdown(f"## Files in {st.session_state.selected_project}")
        
        # Add horizontal line for visual separation
        st.markdown("<hr>", unsafe_allow_html=True)
        
        if project["files"]:
            # Add option to rescan the repository
            if project["type"] == "GitHub Repository":
                if st.button("🔄 Rescan Repository", key="rescan_repository"):
                    with st.spinner("Rescanning repository..."):
                        repo_url = project["repo_url"]
                        string_files = scan_github_repository(repo_url, pattern_search=True)
                        
                        if string_files:
                            project["files"] = string_files
                            st.markdown(f"<div class='status-success'>Found {len(string_files)} strings.xml files!</div>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown("<div class='status-warning'>No strings.xml files found in repository.</div>", unsafe_allow_html=True)
            
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
                st.markdown("### File Preview")
                
                # Group files by feature module for better organization
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
                
                # Create columns for file selection and translate button
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    selected_file = st.selectbox(
                        "Select file to preview", 
                        file_options,
                        key="files_section_preview_select"
                    )
                
                with col2:
                    if selected_file and st.button("🌐 Translate This File", key=f"proj_files_translate_btn"):
                        # Get strings from the file
                        file_content = project["files"][selected_file]
                        
                        if selected_file.endswith(".xml"):
                            strings_dict = xml_to_strings_dict(file_content)
                        else:
                            try:
                                json_content = json.loads(file_content)
                                strings_dict = flatten_json(json_content)
                            except:
                                strings_dict = {}
                                
                        # Store the selected file and strings in session state
                        st.session_state.selected_file_for_translation = selected_file
                        st.session_state.selected_file_strings = strings_dict
                        st.session_state.show_language_dialog_for_file = True
                        st.rerun()
                
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
                        with st.expander("View Raw XML", expanded=False):
                            st.code(file_content, language="xml")
                        
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
                            with st.expander("View Raw JSON", expanded=False):
                                st.json(json_content)
                        except:
                            st.code(file_content)
            
            # Hide files button
            if st.button("Hide Files", key="hide_project_files"):
                st.session_state.show_project_files = False
                st.rerun()
        else:
            st.markdown("<div class='status-info'>No string resource files found in this project.</div>", unsafe_allow_html=True)
            
            # If GitHub project, add scan button
            if project["type"] == "GitHub Repository":
                if st.button("Scan Repository Now", key="scan_empty_project"):
                    with st.spinner("Scanning repository..."):
                        repo_url = project["repo_url"]
                        string_files = scan_github_repository(repo_url, pattern_search=True)
                        
                        if string_files:
                            project["files"] = string_files
                            st.markdown(f"<div class='status-success'>Found {len(string_files)} strings.xml files!</div>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown("<div class='status-warning'>No strings.xml files found in repository. Try disabling pattern-based scanning.</div>", unsafe_allow_html=True)
                            
                            # Provide option for full scan
                            if st.button("Try Full Repository Scan (Slower)", key="full_scan_button"):
                                with st.spinner("Performing full repository scan..."):
                                    repo_url = project["repo_url"]
                                    string_files = scan_github_repository(repo_url, pattern_search=False)
                                    
                                    if string_files:
                                        project["files"] = string_files
                                        st.markdown(f"<div class='status-success'>Found {len(string_files)} strings.xml files!</div>", unsafe_allow_html=True)
                                        st.rerun()
                                    else:
                                        st.markdown("<div class='status-error'>No strings.xml files found in repository. Please check the repository structure.</div>", unsafe_allow_html=True)
    
    # Language selection dialog for project
    if st.session_state.get("show_language_dialog", False):
        st.markdown(f"## Generate Translations for {st.session_state.selected_project}")
        
        # Add horizontal line for visual separation
        st.markdown("<hr>", unsafe_allow_html=True)
        
        with st.form("project_language_selection_form"):
            st.markdown("### Select Target Languages")
            
            selected_languages = st.multiselect(
                "Choose languages for translation",
                SUPPORTED_LANGUAGES,
                default=["Spanish", "French", "German"],
                key="project_languages_dialog_select"
            )
            
            submitted = st.form_submit_button("Generate Translations")
            
            if submitted:
                if selected_languages and configure_genai():
                    # Start translation process for the project
                    project = st.session_state.projects[st.session_state.selected_project]
                    
                    with st.spinner("Generating translations..."):
                        # If project has translations, use them
                        if "translations" in project and "en" in project["translations"]:
                            source_strings = project["translations"]["en"]
                            
                            # Translate to each selected language
                            for language in selected_languages:
                                lang_code = LANGUAGE_CODES.get(language)
                                if lang_code and lang_code != "en":
                                    st.markdown(f"<div class='status-info'>Translating to {language}...</div>", unsafe_allow_html=True)
                                    
                                    translations = translate_all_strings(
                                        source_strings, 
                                        language
                                    )
                                    
                                    # Store translations
                                    project["translations"][lang_code] = translations
                        # Otherwise, use the first file
                        elif project["files"]:
                            # Get the first file
                            file_path = next(iter(project["files"]))
                            file_content = project["files"][file_path]
                            
                            # Parse the file
                            if file_path.endswith(".xml"):
                                source_strings = xml_to_strings_dict(file_content)
                            else:
                                try:
                                    json_content = json.loads(file_content)
                                    source_strings = flatten_json(json_content)
                                except:
                                    source_strings = {}
                            
                            # Initialize translations dictionary if needed
                            if "translations" not in project:
                                project["translations"] = {}
                            
                            # Store original strings as English
                            project["translations"]["en"] = source_strings
                            
                            # Translate to each selected language
                            for language in selected_languages:
                                lang_code = LANGUAGE_CODES.get(language)
                                if lang_code and lang_code != "en":
                                    st.markdown(f"<div class='status-info'>Translating to {language}...</div>", unsafe_allow_html=True)
                                    
                                    translations = translate_all_strings(
                                        source_strings, 
                                        language
                                    )
                                    
                                    # Store translations
                                    project["translations"][lang_code] = translations
                    
                    st.markdown(f"<div class='status-success'>Generated translations in {len(selected_languages)} languages!</div>", unsafe_allow_html=True)
                    st.session_state.show_language_dialog = False
                    
                    # Automatically switch to review page
                    st.session_state.page_selection = "🔄 Translation Review"
                    st.rerun()
                else:
                    st.markdown("<div class='status-error'>Please select at least one language and configure Gemini API.</div>", unsafe_allow_html=True)
    
    # Language selection dialog for specific file
    if st.session_state.get("show_language_dialog_for_file", False):
        st.markdown(f"## Generate Translations for {st.session_state.selected_file_for_translation}")
        
        # Add horizontal line for visual separation
        st.markdown("<hr>", unsafe_allow_html=True)
        
        with st.form("file_language_selection_form"):
            st.markdown("### Select Target Languages")
            
            selected_languages = st.multiselect(
                "Choose languages for translation",
                SUPPORTED_LANGUAGES,
                default=["Spanish", "French", "German"],
                key="file_languages_dialog_select"
            )
            
            submitted = st.form_submit_button("Generate Translations")
            
            if submitted:
                if selected_languages and configure_genai():
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
                                st.markdown(f"<div class='status-info'>Translating to {language}...</div>", unsafe_allow_html=True)
                                
                                translations = translate_all_strings(
                                    strings_dict, 
                                    language
                                )
                                
                                # Store translations
                                project["file_translations"][file_path][lang_code] = translations
                    
                    st.markdown(f"<div class='status-success'>Generated translations for file in {len(selected_languages)} languages!</div>", unsafe_allow_html=True)
                    st.session_state.show_language_dialog_for_file = False
                    
                    # Navigate to review page
                    st.session_state.page = "🔄 Translation Review"
                    st.session_state.review_file_path = file_path
                    st.rerun()
                else:
                    st.markdown("<div class='status-error'>Please select at least one language and configure Gemini API.</div>", unsafe_allow_html=True)

# Translation Review page
elif st.session_state.page == "🔄 Translation Review":
    st.markdown("<h1>Review and Edit Translations</h1>", unsafe_allow_html=True)
    
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
                st.markdown("### Select File")
                
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
                    search_query = st.text_input("🔍 Search keys or translations", "", key=f"search_file_query_{selected_language}")
                    
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
                    st.markdown("### Edit Translations")
                    st.markdown("<div class='status-info'>Make changes directly in the table below and click Save when done.</div>", unsafe_allow_html=True)
                    
                    edited_df = st.data_editor(df, use_container_width=True, 
                                              key=f"file_translation_editor_{selected_file}_{selected_language}")
                    
                    # Save edited translations
                    if st.button("💾 Save Edited Translations", key=f"save_file_translations_{selected_file}"):
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
                                
                        st.markdown("<div class='status-success'>Translations updated successfully!</div>", unsafe_allow_html=True)
                
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
                    search_query = st.text_input("🔍 Search keys or translations", "", key=f"search_query_{selected_language}")
                    
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
                    st.markdown("### Edit Translations")
                    st.markdown("<div class='status-info'>Make changes directly in the table below and click Save when done.</div>", unsafe_allow_html=True)
                    
                    edited_df = st.data_editor(df, use_container_width=True, 
                                              key=f"translation_editor_{selected_review_project}_{selected_language}")
                    
                    # Save edited translations
                    if st.button("💾 Save Edited Translations", key="save_project_translations"):
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
                                
                        st.markdown("<div class='status-success'>Translations updated successfully!</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-info'>No translations available for this project yet.</div>", unsafe_allow_html=True)
                
                # Add a button to translate
                if st.button("Generate Translations Now"):
                    st.session_state.selected_project = selected_review_project
                    st.session_state.show_language_dialog = True
                    st.rerun()
        else:
            st.markdown("<div class='status-info'>Please select a project to review.</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="feature-card" style="text-align:center; padding: 40px;">
            <h3>No translations available</h3>
            <p>No projects with translations available yet. Please translate a project first.</p>
            # Add a function to go to projects
            def go_to_projects():
                st.session_state.page = "📋 Projects"
                
            st.button("Go to Projects", on_click=go_to_projects)
        </div>
        """, unsafe_allow_html=True)

# Export page
elif st.session_state.page == "📤 Export":
    st.markdown("<h1>Export Translations</h1>", unsafe_allow_html=True)
    
    # Select project to export
    projects_with_translations = [p for p, data in st.session_state.projects.items() 
                                if data.get("translations") or data.get("file_translations")]
    
    if projects_with_translations:
        selected_export_project = st.selectbox(
            "Select project to export", 
            projects_with_translations,
            key="export_project_selector"
        )
        
        if selected_export_project:
            project = st.session_state.projects[selected_export_project]
            
            # Check if we have file-specific translations or project-wide translations
            has_file_translations = "file_translations" in project and project["file_translations"]
            has_project_translations = "translations" in project and project["translations"]
            
            # Create export options
            st.markdown("## Export Format")
            
            export_format = st.radio(
                "Select export format",
                ["Android XML", "iOS Strings", "JSON", "Kotlin Multiplatform"],
                key="export_format"
            )
            
            # Show available languages
            available_languages = []
            
            if has_file_translations:
                # Get all languages from all files
                for file_path, file_translations in project["file_translations"].items():
                    available_languages.extend(file_translations.keys())
            elif has_project_translations:
                available_languages = list(project["translations"].keys())
                
            available_languages = list(set(available_languages))
            
            # Convert language codes to names for display
            language_names = []
            for code in available_languages:
                language_name = next((name for name, lang_code in LANGUAGE_CODES.items() if lang_code == code), code)
                language_names.append(language_name)
                
            st.markdown("## Available Languages")
            st.markdown(", ".join(language_names))
            
            # Export options
            st.markdown("## Export Options")
            
            if has_file_translations:
                # Allow selecting specific files
                file_paths = list(project["file_translations"].keys())
                
                selected_files = st.multiselect(
                    "Select files to export (leave empty to export all)",
                    file_paths,
                    key="export_file_selector"
                )
                
                if not selected_files:
                    selected_files = file_paths
            
            # Export button
            if st.button("Generate Export", key="generate_export_button"):
                # Create a ZIP file with translations
                with st.spinner("Generating export files..."):
                    export_files = {}
                    
                    if has_file_translations:
                        # Export file-specific translations
                        for file_path in selected_files:
                            file_translations = project["file_translations"][file_path]
                            
                            # Get filename without path
                            filename = file_path.split("/")[-1]
                            file_base = filename.split(".")[0]
                            
                            # Export each language
                            for lang_code, translations in file_translations.items():
                                if export_format == "Android XML":
                                    # Create Android XML format
                                    if lang_code == "en":
                                        export_path = f"values/{file_base}.xml"
                                    else:
                                        export_path = f"values-{lang_code}/{file_base}.xml"
                                        
                                    export_files[export_path] = dict_to_strings_xml(translations)
                                
                                elif export_format == "iOS Strings":
                                    # Create iOS Strings format
                                    ios_content = ""
                                    for key, value in translations.items():
                                        ios_content += f'"{key}" = "{value}";\n'
                                        
                                    if lang_code == "en":
                                        export_path = f"en.lproj/{file_base}.strings"
                                    else:
                                        export_path = f"{lang_code}.lproj/{file_base}.strings"
                                        
                                    export_files[export_path] = ios_content
                                
                                elif export_format == "JSON":
                                    # Create JSON format
                                    if lang_code == "en":
                                        export_path = f"{file_base}.json"
                                    else:
                                        export_path = f"{file_base}_{lang_code}.json"
                                        
                                    export_files[export_path] = json.dumps(translations, ensure_ascii=False, indent=2)
                                
                                elif export_format == "Kotlin Multiplatform":
                                    # Create KMP format
                                    if lang_code == "en":
                                        export_path = f"commonMain/resources/MR/base/{file_base}.xml"
                                    else:
                                        export_path = f"commonMain/resources/MR/{lang_code}/{file_base}.xml"
                                        
                                    export_files[export_path] = dict_to_strings_xml(translations)
                    
                    elif has_project_translations:
                        # Export project-wide translations
                        for lang_code, translations in project["translations"].items():
                            if export_format == "Android XML":
                                # Create Android XML format
                                if lang_code == "en":
                                    export_path = "values/strings.xml"
                                else:
                                    export_path = f"values-{lang_code}/strings.xml"
                                    
                                export_files[export_path] = dict_to_strings_xml(translations)
                            
                            elif export_format == "iOS Strings":
                                # Create iOS Strings format
                                ios_content = ""
                                for key, value in translations.items():
                                    ios_content += f'"{key}" = "{value}";\n'
                                    
                                if lang_code == "en":
                                    export_path = "en.lproj/Localizable.strings"
                                else:
                                    export_path = f"{lang_code}.lproj/Localizable.strings"
                                    
                                export_files[export_path] = ios_content
                            
                            elif export_format == "JSON":
                                # Create JSON format
                                if lang_code == "en":
                                    export_path = "strings.json"
                                else:
                                    export_path = f"strings_{lang_code}.json"
                                    
                                export_files[export_path] = json.dumps(translations, ensure_ascii=False, indent=2)
                            
                            elif export_format == "Kotlin Multiplatform":
                                # Create KMP format
                                if lang_code == "en":
                                    export_path = "commonMain/resources/MR/base/strings.xml"
                                else:
                                    export_path = f"commonMain/resources/MR/{lang_code}/strings.xml"
                                    
                                export_files[export_path] = dict_to_strings_xml(translations)
                    
                    # Create a ZIP file
                    zip_buffer = StringIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for file_path, content in export_files.items():
                            zf.writestr(file_path, content)
                    
                    # Display download button
                    st.download_button(
                        label="📥 Download Translations ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"{selected_export_project}_translations.zip",
                        mime="application/zip"
                    )
                    
                # Show files included in export
                st.markdown("## Files Included in Export")
                for file_path in export_files.keys():
                    st.markdown(f"- {file_path}")
        else:
            st.markdown("<div class='status-info'>Please select a project to export.</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="feature-card" style="text-align:center; padding: 40px;">
            <h3>No translations available</h3>
            <p>No projects with translations available yet. Please translate a project first.</p>
            # Add a function to go to projects
            def go_to_projects():
                st.session_state.page = "📋 Projects"
                
            st.button("Go to Projects", on_click=go_to_projects)
        </div>
        """, unsafe_allow_html=True)