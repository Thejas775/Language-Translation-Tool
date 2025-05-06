# backend/app/services/github_service.py
from github import Github, Auth
import base64
import re
from typing import Dict, Optional, List
import xml.etree.ElementTree as ET

async def scan_github_repository(
    repo_url: str, 
    github_token: str, 
    pattern_search: bool = True,
    branch: Optional[str] = None
) -> Dict[str, str]:
    """
    Scan a GitHub repository for strings.xml files.
    
    Args:
        repo_url: The GitHub repository URL (can include /tree/branch-name)
        github_token: GitHub API access token
        pattern_search: Whether to use pattern-based search for faster scanning
        branch: Optional branch name (can be extracted from URL)
        
    Returns:
        Dictionary mapping file paths to their content
    """
    try:
        # Extract branch if specified in the URL
        if not branch and "/tree/" in repo_url:
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
        
        # Configure GitHub client
        auth = Auth.Token(github_token)
        g = Github(auth=auth)
        
        # Get repository object
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # If branch was not specified, use the default branch
        if not branch:
            branch = repo.default_branch
        
        # Common patterns where strings.xml files are typically located
        common_patterns = [
            "*/src/commonMain/composeResources/values/strings.xml",
            "*/*/src/commonMain/composeResources/values/strings.xml",
            "feature/*/src/commonMain/composeResources/values/strings.xml",
            "feature/*/src/*/composeResources/values/strings.xml",
            "feature/*/src/*/resources/values/strings.xml",
        ]
        
        found_files = {}
        
        # If pattern search is enabled, search for common patterns first
        if pattern_search:
            for pattern in common_patterns:
                try:
                    # Search for files matching the pattern
                    contents = repo.get_contents("", ref=branch)
                    path_parts = pattern.split("/")
                    
                    # Try to match the pattern
                    pattern_files = await search_by_pattern(repo, contents, path_parts, 0, branch)
                    
                    # Add found files to the result
                    for file_path, content in pattern_files.items():
                        found_files[file_path] = content
                        
                except Exception as e:
                    # Skip errors in pattern matching and continue with next pattern
                    continue
            
            # If we found files, return them without doing a full repository scan
            if found_files:
                return found_files
        
        # If no files were found with pattern search or pattern search is disabled,
        # fall back to full repository scan
        return await search_files_in_repo(repo, "strings.xml", branch)
            
    except Exception as e:
        # Re-raise the exception with details
        raise Exception(f"Error scanning repository: {str(e)}")

async def search_by_pattern(repo, contents, pattern_parts, current_depth, branch):
    """
    Recursively search for files that match a pattern.
    
    Args:
        repo: GitHub repository object
        contents: Current contents to search through
        pattern_parts: List of parts in the pattern path
        current_depth: Current depth in the pattern
        branch: Branch to search in
        
    Returns:
        Dictionary mapping file paths to their content
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
                    deeper_files = await search_by_pattern(repo, next_contents, pattern_parts, current_depth + 1, branch)
                    found_files.update(deeper_files)
                    
                    # Also search at this same level for more directories
                    same_level_files = await search_by_pattern(repo, next_contents, pattern_parts, current_depth, branch)
                    found_files.update(same_level_files)
                else:
                    # Regular directory match, go one level deeper in the pattern
                    deeper_files = await search_by_pattern(repo, next_contents, pattern_parts, current_depth + 1, branch)
                    found_files.update(deeper_files)
            except Exception:
                # Skip if we can't access the directory content
                continue
                
        elif content_item.type == "file" and current_depth == len(pattern_parts) - 1:
            # If it's a file and the last pattern part matches the filename
            if content_item.name == pattern_parts[-1] or pattern_parts[-1] == "*":
                try:
                    # Get the file content
                    raw_content = base64.b64decode(content_item.content).decode('utf-8')
                    found_files[content_item.path] = raw_content
                except Exception:
                    # Skip if we can't decode the content
                    continue
    
    return found_files

async def search_files_in_repo(repo, filename, branch):
    """
    Search for files in a repository with a specific filename.
    
    Args:
        repo: GitHub repository object
        filename: The filename to search for
        branch: Branch to search in
        
    Returns:
        Dictionary mapping file paths to their content
    """
    found_files = {}
    
    # Get all files in the repository
    contents = repo.get_contents("", ref=branch)
    
    # Use a loop instead of recursion to avoid stack overflow
    while contents:
        file_content = contents.pop(0)
        
        if file_content.type == "dir":
            try:
                # Add directory contents to the queue
                dir_contents = repo.get_contents(file_content.path, ref=branch)
                contents.extend(dir_contents)
            except Exception:
                # Skip if we can't access the directory
                continue
                
        elif file_content.name == filename:
            # Found a matching file
            try:
                raw_content = base64.b64decode(file_content.content).decode('utf-8')
                found_files[file_content.path] = raw_content
            except Exception:
                # Skip if we can't decode the content
                continue
    
    return found_files

async def parse_strings_xml(xml_content):
    """
    Parse a strings.xml file and extract the strings.
    
    Args:
        xml_content: The content of the strings.xml file
        
    Returns:
        Dictionary of string keys and values
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
        raise Exception(f"Error parsing XML: {str(e)}")