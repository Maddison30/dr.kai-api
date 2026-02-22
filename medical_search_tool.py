from langchain_core.tools import tool
from web_search import search_medical_sources, APPROVED_MEDICAL_DOMAINS
from translation_utils import translate_query_for_search, get_language_handler

@tool
def get_medical_info(query: str) -> str:
    """Searches ONLY approved medical websites (1177.se, socialstyrelsen.se, viss.nu, fass.se) for health information in Swedish, returns results with citations."""
    
    # Detect user's language and translate query to Swedish for searching
    swedish_query, user_language = translate_query_for_search(query)
    language_handler = get_language_handler()
    user_lang_name = language_handler.get_language_name(user_language)
    
    print(f"\n🌐 User language detected: {user_lang_name}")
    print(f"🔍 Searching approved medical sources for: '{swedish_query}'")
    
    # Search using Swedish query (better results from Swedish medical sites)
    search_result = search_medical_sources(swedish_query, api_type="serpapi")
    
    if not search_result["success"]:
        print(f"❌ Search failed: {search_result['message']}")
        error_msg = f"⚠️ {search_result['message']}\n\nApproved medical sources: {', '.join(APPROVED_MEDICAL_DOMAINS)}"
        return error_msg
    
    # Format results with HTML anchor citations (clickable links)
    response = f"📋 Medical Information Found ({len(search_result['results'])} results):\n\n"
    
    # Build a map of URL -> citation number for LLM to reference
    url_to_citation = {}
    for i, result in enumerate(search_result["results"], 1):
        url_to_citation[result['url']] = i
        response += f"{i}. {result['title']}\n"
        response += f"   📝 {result['snippet']}\n"
        # Include URL in HTML anchor format for easy reference
        response += f"   Source: [<a href='{result['url']}' target='_blank'>{i}</a>]\n\n"
        print(f"   ✅ Result {i}: {result['title'][:50]}...")
    
    # Add a JSON-encoded map at the end so LLM can easily reference which URL corresponds to which number
    import json
    citation_map = {str(num): url for url, num in url_to_citation.items()}
    response += f"\n[CITATION_MAP: {json.dumps(citation_map)}]\n"
    
    # Add disclaimer
    response += "\n⚠️ IMPORTANT DISCLAIMER:\n"
    response += "I am not a doctor. This information is for educational purposes only. "
    response += "If your symptoms are severe or worsen, please contact a healthcare professional immediately.\n\n"
    
    response += f"[All information sourced from approved Swedish medical websites: {', '.join(APPROVED_MEDICAL_DOMAINS)}]\n"
    response += f"[Original query language: {user_lang_name}. Please provide your response in {user_lang_name}. Use HTML anchors [<a href='URL'>N</a>] for all citations.]" 
    
    return response




