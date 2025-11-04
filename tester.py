import os
import sys
from ollama import chat, web_fetch, web_search
import dotenv
dotenv.load_dotenv()
from ollama import Client
# Ensure an Ollama bearer token is available; the client requires an Authorization header.
# Put OLLAMA_API_KEY=<your_token> in your .env or export it into the environment before running.
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY') or os.getenv('OLLAMA_TOKEN')
if not OLLAMA_API_KEY:
    print("Error: OLLAMA_API_KEY (or OLLAMA_TOKEN) not found in environment; add it to your .env or export it before running.")
    sys.exit(1)

# Normalize to OLLAMA_API_KEY for the Ollama client if the token was provided under OLLAMA_TOKEN.
custom_headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}"
}
client = Client(headers=custom_headers)
available_tools = {
    'web_search': client.web_search, # Use client's method
    'web_fetch': client.web_fetch     # Use client's method
}
messages = [{'role': 'user', 'content': "what is the weather like in Glenside Pennsylvania right now?"}]

while True:
    # 1. Start streaming by setting stream=True
    response_stream = client.chat(
        model='qwen3:30b',
        messages=messages,
        tools=[client.web_search, client.web_fetch],
        think=True,
        stream=True  # <--- Key change for streaming
    )

    # Initialize a final message structure to accumulate the response
    final_response_message = {
        'role': 'assistant',
        'content': '',
        'thinking': None,
        'tool_calls': None 
    }
    
    # 2. Iterate through the generator to print chunks and build the final message
    print('Content: ', end='', flush=True)
    
    # Use response_chunk instead of response
    for response_chunk in response_stream: 
        chunk_message = response_chunk.message

        # Handle Thinking (usually sent in the first chunk, if present)
        if chunk_message.thinking:
            # Thinking content is non-streaming and should be set once
            if not final_response_message['thinking']:
                 final_response_message['thinking'] = chunk_message.thinking
                 print(f'\nThinking: {final_response_message["thinking"]}')
        
        # Stream Content
        if chunk_message.content:
            # Print the streamed chunk and accumulate it
            print(chunk_message.content, end='', flush=True)
            final_response_message['content'] += chunk_message.content

        # Handle Tool Calls (usually sent in the final chunk, if present)
        if chunk_message.tool_calls:
            # Tool calls are non-streaming and should be set once
            final_response_message['tool_calls'] = chunk_message.tool_calls
    
    print() # Add a final newline after streaming is complete

    # 3. Append the *complete* final message to the conversation history
    # The structure must match the `Message` object expected by `chat`.
    messages.append(final_response_message) 

    # 4. Handle tool calls (which initiates the next loop iteration)
    if final_response_message['tool_calls']:
        print('Tool calls: ', final_response_message['tool_calls'])
        
        # Re-map the structure for easy iteration
        tool_calls = final_response_message['tool_calls'] 

        for tool_call in tool_calls:
            function_to_call = available_tools.get(tool_call.function.name)
            if function_to_call:
                # The tool call object might need to be accessed via .function.arguments 
                # depending on the exact structure returned by the Ollama library. 
                # Assuming the structure is similar to the non-streaming version:
                args = tool_call.function.arguments 
                result = function_to_call(**args)
                print('Result: ', str(result)[:200]+'...')
                # Result is truncated for limited context lengths
                messages.append({
                    'role': 'tool', 
                    'content': str(result)[:2000 * 4], 
                    'tool_name': tool_call.function.name
                })
            else:
                messages.append({
                    'role': 'tool', 
                    'content': f'Tool {tool_call.function.name} not found', 
                    'tool_name': tool_call.function.name
                })
    else:
        # Exit if no tool calls were requested
        break