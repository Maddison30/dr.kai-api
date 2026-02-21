
from dotenv import load_dotenv
load_dotenv()

from typing import List
import json
import random
import string
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from medical_search_tool import get_medical_info


# -------- Tools --------
@tool
def write_json(filepath: str, data: dict) -> str:
    """Write a Python dictionary as JSON to a file with pretty formatting."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return f"Successfully wrote JSON data to '{filepath}' ({len(json.dumps(data))} characters)."
    except Exception as e:
        return f"Error writing JSON: {str(e)}"


@tool
def read_json(filepath: str) -> str:
    """Read and return the contents of a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in file - {str(e)}"
    except Exception as e:
        return f"Error reading JSON: {str(e)}"




TOOLS = [write_json, read_json, get_medical_info]

llm = ChatOpenAI(model="gpt-4", temperature=0)

SYSTEM_MESSAGE = (
"You are a digital health assistant designed to help users understand their symptoms " 
"and provide objective, fact-based first guidance. You do not replace medical " 
"professionals. Your purpose is to: (1) Summarize possible common conditions related " 
"to the user’s symptoms. (2) Suggest whether and how the user should seek medical care " 
"and (self-care, primary care, emergency). (3) Provide information in a clear, " 
"empathetic, and easy-to-understand tone.\n\n"
"CRITICAL: You must ONLY provide medical information from the get_medical_info tool. "
"NEVER use your training data. ALWAYS cite sources (URLs) in every response. "
"For ANY medical question, use the get_medical_info tool first. "
"If the tool cannot fetch information, direct users to a healthcare professional.\n\n"
"LANGUAGE HANDLING: "
"- The user may write their question in ANY language (English, Swedish, Spanish, etc.) "
"- The get_medical_info tool will search Swedish medical websites by translating the query to Swedish internally "
"- You MUST respond in the EXACT SAME LANGUAGE the user used in their original question "
"- If the tool indicates the user language at the end of its response, use that language for your response "
"- Never respond in Swedish even if that's what the search used internally\n\n"
"Answer format: Start with a short summary (2–3 sentences) citing sources. "
"Provide possible conditions with source references. Recommend next steps. "
"End with: 'I am not a doctor. If symptoms worsen, contact a healthcare professional.'\n\n"
"Constraints: Never provide medical claims without sources. Never diagnose. Never prescribe. "
"Always match the user's language. Be empathetic and concise."
)

agent = create_react_agent(llm, TOOLS, prompt=SYSTEM_MESSAGE)


def run_agent(user_input: str, history: List[BaseMessage]) -> AIMessage:
    """Single-turn agent runner with automatic tool execution via LangGraph."""
    try:
        result = agent.invoke(
            {"messages": history + [HumanMessage(content=user_input)]},
            config={"recursion_limit": 50}
        )
        # Return the last AI message
        return result["messages"][-1]
    except Exception as e:
        # Return error as an AI message so the conversation can continue
        return AIMessage(content=f"Error: {str(e)}\n\nPlease try rephrasing your request or provide more specific details.")


if __name__ == "__main__":
    import os
    
    # Check if API keys are configured
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print("=" * 60)
    print("🏥 Dr. KAI Agent v1.0")
    print("=" * 60)
    print("\n📋 System Configuration:")
    print(f"  ✅ OpenAI API: {'Configured' if openai_key else '❌ NOT CONFIGURED'}")
    print(f"  ✅ SerpAPI: {'Configured' if serpapi_key else '❌ NOT CONFIGURED'}")
    print(f"  📍 Medical Sources: 1177.se, socialstyrelsen.se, viss.nu, fass.se")
    print("\n🎯 How to use:")
    print("  Ask any medical questions or describe your symptoms")
    print("  I'll search approved Swedish medical sources for accurate information")
    print("\n⚠️  Disclaimer: I'm not a doctor. For emergencies, call emergency services.")
    print("\nCommands: 'quit' or 'exit' to end")
    print("=" * 60 + "\n")
    
    if not (serpapi_key and openai_key):
        print("\n⚠️  WARNING: Missing API keys!")
        if not openai_key:
            print("  - Add OPENAI_API_KEY to .env file")
        if not serpapi_key:
            print("  - Add SERPAPI_API_KEY to .env file")
        print()

    history: List[BaseMessage] = []

    while True:
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ['quit', 'exit', 'q', ""]:
            print("Goodbye!")
            break

        print("Agent: ", end="", flush=True)
        response = run_agent(user_input, history)
        print(response.content)
        print()

        # Update conversation history
        history += [HumanMessage(content=user_input), response]