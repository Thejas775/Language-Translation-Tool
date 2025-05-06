# backend/app/services/translation_service.py
import json
import re
import google.generativeai as genai
from typing import Dict, Optional, List, Any

async def translate_strings(
    strings: Dict[str, str], 
    target_language: str, 
    contexts: Dict[str, str] = None,
    api_key: str = None
) -> Dict[str, str]:
    """
    Translate a dictionary of strings to the target language.
    
    Args:
        strings: Dictionary of string keys and values to translate
        target_language: Target language for translation
        contexts: Optional dictionary of contexts for each string
        api_key: Gemini API key
        
    Returns:
        Dictionary of translated strings
    """
    try:
        # Configure the Gemini API
        if api_key:
            genai.configure(api_key=api_key)
        
        # Filter only string values
        string_contents = {k: v for k, v in strings.items() if isinstance(v, str)}
        
        # Use contexts if provided
        contexts_dict = contexts or {}
        
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
        
        # Check if input is too large and use batch mode if needed
        if estimated_tokens > 30000:
            return await batch_translate_texts(string_contents, target_language, contexts_dict, api_key)
        
        # Craft a translation prompt
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
        
        # Configure model
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Parse the response
        response_text = response.text.strip()
        translations = parse_translation_response(response_text)
        
        if translations:
            return translations
            
        # If parsing fails, fall back to batch translation
        return await batch_translate_texts(string_contents, target_language, contexts_dict, api_key)
            
    except Exception as e:
        raise Exception(f"Translation error: {str(e)}")

async def batch_translate_texts(
    texts_dict: Dict[str, str], 
    target_language: str, 
    contexts_dict: Dict[str, str] = None,
    api_key: str = None
) -> Dict[str, str]:
    """
    Translate texts in batches to handle large input.
    
    Args:
        texts_dict: Dictionary of strings to translate
        target_language: Target language for translation
        contexts_dict: Optional dictionary of contexts for each string
        api_key: Gemini API key
        
    Returns:
        Dictionary of translated strings
    """
    try:
        # Configure the Gemini API if not already configured
        if api_key:
            genai.configure(api_key=api_key)
            
        string_contents = {k: v for k, v in texts_dict.items() if isinstance(v, str)}
        contexts = contexts_dict or {}
        
        texts_list = list(string_contents.items())
        
        batch_size = 50  # Number of strings per batch
        all_results = {}
        
        # Process each batch
        for i in range(0, len(texts_list), batch_size):
            batch = texts_list[i:i+batch_size]
            
            # Create structured format for translation with JSON
            translation_items = []
            for key, text in batch:
                context = contexts.get(key, "")
                translation_items.append({
                    "id": key,
                    "key": key,
                    "text": text,
                    "context": context
                })
            
            # Craft a batch translation prompt
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
            
            # Configure model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    
                    # Parse the response
                    response_text = response.text.strip()
                    translations = parse_translation_response(response_text)
                    
                    if translations:
                        all_results.update(translations)
                        break  # Success! Exit retry loop
                
                except Exception as batch_error:
                    if retry == max_retries - 1:
                        # If this was the last retry, add batch keys with original values
                        for key, text in batch:
                            if key not in all_results:
                                all_results[key] = text  # Use original as fallback
        
        return all_results
        
    except Exception as e:
        raise Exception(f"Batch translation error: {str(e)}")

def parse_translation_response(response_text: str) -> Dict[str, str]:
    """
    Parse the translation response from Gemini API.
    
    Args:
        response_text: The raw text response from the API
        
    Returns:
        Dictionary of key-value pairs with translations
    """
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()

        # Clean up common formatting issues
        response_text = re.sub(r'\s*//.*', '', response_text)
        response_text = re.sub(r'/\*.*?\*/', '', response_text, flags=re.DOTALL)
        
        response_text = re.sub(r',\s*}', '}', response_text)
        response_text = re.sub(r',\s*\]', ']', response_text)
        
        # Add quotes to keys if missing
        response_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', response_text)
        
        # Fix JSON array format issues
        response_text = re.sub(r'}\s*{', '},{', response_text)
        
        # Parse JSON
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
        
    except json.JSONDecodeError:
        # Try extracting individual JSON objects if full parsing fails
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
                # Last resort fallback using regex
                key_match = re.search(r'"key"\s*:\s*"([^"]+)"', match.group(0))
                translation_match = re.search(r'"translation"\s*:\s*"([^"]+)"', match.group(0))
                if key_match and translation_match:
                    translations[key_match.group(1)] = translation_match.group(1)
        
        if translations:
            return translations
            
        # Try another pattern if still no matches
        pattern = r'"key"\s*:\s*"([^"]+)"[^}]+"translation"\s*:\s*"([^"]+)"'
        matches = re.finditer(pattern, response_text)
        
        translations = {}
        for match in matches:
            key = match.group(1)
            translation = match.group(2)
            translations[key] = translation
            
        return translations

    except Exception as e:
        # Return empty dict if all parsing fails
        return {}