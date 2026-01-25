import ollama
import json
import subprocess

def get_available_models():
    """
    Get list of available Ollama models on the system.
    Enhanced detection for WSL conda environments.
    Returns tuple: (models_list, status_message)
    """
    # First, check if ollama command is available
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return [], 'not_installed'
    except:
        pass  # Continue with other checks

    # Try to get models using subprocess (more reliable in WSL conda)
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # First line is header
                model_list = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_name = parts[0]
                            model_list.append(model_name)
                if model_list:
                    return model_list, 'ok'
    except:
        pass  # Continue with Python library approach

    # Fallback to Python ollama library
    try:
        models = ollama.list()
        model_list = [model['name'] for model in models['models']]
        if model_list:
            return model_list, 'ok'
        else:
            return [], 'no_models'
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['connection', 'connect', 'refused', 'timeout', 'unreachable', 'no such file', 'not found']):
            return [], 'not_running'
        else:
            return [], 'error'

def get_file_classification(file_info, model_name='gemma3:4b'):
    """
    Uses Ollama to classify a file and provide reasoning.
    model_name: The Ollama model to use (default: gemma3:4b)
    """
    prompt = f"""
    You are a smart file organizer. Analyze the following file details and suggest a category name (e.g., Projects, Docs, Media, Others).
    Provide a short reasoning for your choice.
    
    File Detail:
    - Name: {file_info['name']}
    - Extension: {file_info['extension']}
    
    Return the response ONLY as a JSON object with 'category' and 'reasoning' keys.
    """
    
    try:
        response = ollama.chat(model=model_name, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        
        # Clean the response to ensure it's valid JSON
        content = response['message']['content'].strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
            
        return json.loads(content)
    except Exception as e:
        return {
            "category": "Unknown",
            "reasoning": f"Error: {str(e)}"
        }
