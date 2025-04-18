import streamlit as st
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import time
import re

# Load environment variables
load_dotenv()

# Configure the Gemini API
def configure_genai():
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
            response = model.generate_content(prompt)
            
            # Parse the response using the improved parser
            response_text = response.text.strip()
            translations = parse_translation_response(response_text)
            
            if translations:
                all_results.update(translations)
            else:
                # If parsing still fails, try individual translation as last resort
                st.warning(f"Failed to parse batch {current_batch}. Trying individual translations...")
                for key, text in batch:
                    if key not in all_results:  # Only translate if not already translated
                        context = contexts_dict.get(key, "")
                        translation = translate_text(text, target_language, context)
                        if translation:
                            all_results[key] = translation
                        else:
                            all_results[key] = text  # Fallback to original
            
            # Update progress
            progress_bar.progress(min(1.0, (i + batch_size) / len(texts_list)))
            
            time.sleep(0.5)
        
        return all_results
        
    except Exception as e:
        st.error(f"Batch translation error: {str(e)}")
        return {}

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

# App title and description
st.title("UI String Translator")
st.markdown("""
Upload a JSON file with UI strings, select target language, and generate translations using Gemini API.
This tool helps create localization files for your application with context-aware translations.
""")

# API Key input
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password", key="api_key")
    if st.button("Configure API"):
        if configure_genai():
            st.success("API configured successfully!")
        else:
            st.error("Please provide a valid API key")

# Main workflow
tab1, tab2, tab3 = st.tabs(["Upload & Translate", "Review & Edit", "Export"])

with tab1:
    st.header("Step 1: Upload JSON File")
    uploaded_file = st.file_uploader("Choose a JSON file", type="json")
    
    if uploaded_file is not None:
        try:
            # Load and parse the JSON file
            content = json.loads(uploaded_file.read().decode())
            flattened_content = flatten_json(content)
            
            # Store in session state
            st.session_state.original_content = content
            st.session_state.flattened_content = flattened_content
            
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
            
            # Add file summary
            with st.expander("View File Structure Summary"):
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
            
            # Allow context addition
            st.header("Step 2: Add Context (Optional)")
            st.info("You can add context for specific keys to improve translation quality.")
            
            if 'contexts' not in st.session_state:
                st.session_state.contexts = {}
            
            # Interface for adding context
            selected_key = st.selectbox("Select key to add context", list(flattened_content.keys()))
            current_context = st.session_state.contexts.get(selected_key, "")
            
            context = st.text_area(
                "Enter context for this string (e.g., 'This appears on a login button')",
                value=current_context
            )
            
            if st.button("Save Context"):
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
            target_language = st.text_input("Enter target language (e.g., Hindi, Spanish, French)")
            
            # Single call vs. batching options
            use_smart_batching = st.checkbox("Use smart batching (recommended)", value=True, 
                                            help="Will try to translate everything in a single API call when possible, and only use batching if needed")
            
            if st.button("Start Translation") and target_language and configure_genai():
                if 'translations' not in st.session_state:
                    st.session_state.translations = {}
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Start timer
                start_time = time.time()
                
                if use_smart_batching:
                    status_text.text("Analyzing content and starting translation...")
                    
                    # First try translating everything in one go
                    st.session_state.translations = translate_all_strings(
                        flattened_content, 
                        target_language, 
                        st.session_state.contexts
                    )
                else:
                    # Fall back to batch mode
                    string_contents = {k: v for k, v in flattened_content.items() if isinstance(v, str)}
                    st.session_state.translations = batch_translate_texts(
                        string_contents, 
                        target_language, 
                        st.session_state.contexts
                    )
                
                # Calculate time taken
                total_time = time.time() - start_time
                
                # Update progress and show completion
                progress_bar.progress(1.0)
                status_text.text("Translation completed!")
                
                st.success(f"Translated {len(st.session_state.translations)} strings to {target_language} in {total_time:.1f} seconds")
                
                # Navigate to review tab
                st.session_state.active_tab = "Review & Edit"
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

with tab2:
    if st.session_state.get('translations'):
        st.header("Review and Edit Translations")
        
        # Add search functionality
        search_query = st.text_input("Search keys or translations", "")
        
        # Create a dataframe for display and editing
        data = {
            "Key": list(st.session_state.translations.keys()),
            "Original": [st.session_state.flattened_content.get(k, "") for k in st.session_state.translations.keys()],
            "Translation": list(st.session_state.translations.values())
        }
        
        df = pd.DataFrame(data)
        
        # Filter based on search query if provided
        if search_query:
            df = df[
                df["Key"].str.contains(search_query, case=False) | 
                df["Original"].astype(str).str.contains(search_query, case=False) | 
                df["Translation"].astype(str).str.contains(search_query, case=False)
            ]
        
        # Display as editable dataframe
        edited_df = st.data_editor(df, use_container_width=True, 
                                  key="translation_editor",
                                  column_config={
                                      "Key": st.column_config.TextColumn("Key", width="medium"),
                                      "Original": st.column_config.TextColumn("Original", width="medium"),
                                      "Translation": st.column_config.TextColumn("Translation", width="medium")
                                  })
        
        # Save edited translations
        if st.button("Save Edited Translations"):
            # Update only the edited translations
            for i, row in edited_df.iterrows():
                key = row["Key"]
                translation = row["Translation"]
                st.session_state.translations[key] = translation
                
            st.success("Translations updated!")
    else:
        st.info("No translations available yet. Please upload a file and translate first.")

with tab3:
    if st.session_state.get('translations'):
        st.header("Export Translations")
        
        # Get file format preference
        export_format = st.selectbox(
            "Select export format",
            ["JSON", "Android (strings.xml)"]
        )
        
        if export_format == "JSON":
            # Rebuild the original structure with translations
            translated_flattened = {}
            for key, translation in st.session_state.translations.items():
                translated_flattened[key] = translation
            
            translated_nested = unflatten_json(translated_flattened)
            translated_json = json.dumps(translated_nested, indent=2, ensure_ascii=False)
            
            st.code(translated_json, language="json")
            
            # Download button
            st.download_button(
                "Download JSON",
                translated_json,
                "translations.json",
                mime="application/json"
            )
            
        elif export_format == "Android (strings.xml)":
            # Create Android strings.xml format
            xml_content = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            
            for key, translation in st.session_state.translations.items():
                # Replace periods with underscores for Android resource IDs
                android_key = key.replace(".", "_")
                
                # Escape special XML characters
                translation_escaped = (str(translation)
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '\\"'))
                
                xml_content += f'    <string name="{android_key}">{translation_escaped}</string>\n'
            
            xml_content += '</resources>'
            
            st.code(xml_content, language="xml")
            
            # Download button
            st.download_button(
                "Download strings.xml",
                xml_content,
                "strings.xml",
                mime="text/xml"
            )
            
        elif export_format == "iOS (.strings)":
            # Create iOS .strings format
            ios_content = "/* Generated Translations */\n\n"
            
            for key, translation in st.session_state.translations.items():
                # Escape special characters
                translation_escaped = str(translation).replace('"', '\\"')
                ios_content += f'"{key}" = "{translation_escaped}";\n'
            
            st.code(ios_content)
            
            # Download button
            st.download_button(
                "Download Localizable.strings",
                ios_content,
                "Localizable.strings",
                mime="text/plain"
            )
    else:
        st.info("No translations available yet. Please upload a file and translate first.")

# Initialize session state for the first run
if 'original_content' not in st.session_state:
    st.session_state.original_content = {}

if 'flattened_content' not in st.session_state:
    st.session_state.flattened_content = {}

if 'contexts' not in st.session_state:
    st.session_state.contexts = {}

if 'translations' not in st.session_state:
    st.session_state.translations = {}