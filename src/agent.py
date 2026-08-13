import os
import json
from google import genai
from google.genai import types
from tools import get_order_status, process_refund

# Initialize Gemini Client
client = genai.Client()

def get_active_model_name():
    """Dynamically fetches a working non-deprecated model name from your API key."""
    try:
        available_models = [m.name for m in client.models.list()]
        
        # Priority order for active models on your account
        preferred_models = [
            'models/gemini-3.5-flash',
            'models/gemini-2.5-flash-lite',
            'models/gemini-flash-latest',
            'gemini-3.5-flash',
            'gemini-2.5-flash-lite'
        ]
        
        for pref in preferred_models:
            if pref in available_models:
                return pref
                
        # Filter out old deprecated gemini-2.5-flash if returning dynamically
        valid_models = [m for m in available_models if 'gemini-2.5-flash' not in m and ('flash' in m or 'pro' in m)]
        if valid_models:
            return valid_models[0]
            
        return 'gemini-3.5-flash'
    except Exception:
        return 'gemini-3.5-flash'

def run_triage_agent(user_message: str):
    print("=" * 60)
    print(f"Customer Inquiry: \"{user_message}\"")
    print("=" * 60)

    # 1. Available tools
    tools_list = [get_order_status, process_refund]
    
    system_instruction = """
    You are an Autonomous Customer Support Triage Agent for an e-commerce platform.
    Your job is to SOLVE customer issues using available tools.
    
    Instructions:
    1. Extract order details from user message.
    2. Use `get_order_status` to check order status in database first.
    3. If package is LOST_IN_TRANSIT and customer requests a refund, call `process_refund`.
    4. If a tool returns REQUIRES_HUMAN_APPROVAL, politely inform the user that their request has been escalated to a senior manager.
    """

    model_name = get_active_model_name()
    print(f"[SYSTEM INFO]: Automatically selected active model -> '{model_name}'\n")

    # Step 1: Initial call to model with tools
    response = client.models.generate_content(
        model=model_name,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools_list,
            temperature=0.1,
        )
    )

    # Step 2: Check if model wants to call a tool
    if response.function_calls:
        for call in response.function_calls:
            tool_name = call.name
            tool_args = call.args
            print(f"[AI DECISION]: Executing Tool -> '{tool_name}' with args {tool_args}")
            
            # Execute the tool function
            if tool_name == "get_order_status":
                tool_output = get_order_status(**tool_args)
            elif tool_name == "process_refund":
                tool_output = process_refund(**tool_args)
            else:
                tool_output = "Tool not found."

            print(f"[TOOL OUTPUT]: {tool_output}")

            # Step 3: Send tool result back to Gemini for final answer
            second_response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part.from_text(user_message)]),
                    response.candidates[0].content,
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": tool_output}
                            )
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                )
            )
            
            print("\n[FINAL RESPONSE TO CUSTOMER]:")
            print(second_response.text)
    else:
        print("\n[FINAL RESPONSE TO CUSTOMER]:")
        print(response.text)

if __name__ == "__main__":
    test_1 = "My package for order 1002 never arrived and I want a refund!"
    run_triage_agent(test_1)