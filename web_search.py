"""
Web Search API integration for searching approved medical websites.
Supports multiple search APIs with domain restrictions.
Includes language detection and translation for Swedish medical searches.
"""

from dotenv import load_dotenv
load_dotenv()

import requests
from typing import List, Dict, Optional
from urllib.parse import quote
import os
import logging
import json

# Set up logging
logger = logging.getLogger(__name__)

# Approved medical domains to search within
APPROVED_MEDICAL_DOMAINS = [
    "1177.se",
    "socialstyrelsen.se",
    "viss.nu",
    "fass.se"
]

def translate_to_swedish(text: str) -> str:
    """Translate text to Swedish using OpenAI API for accurate medical terminology."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        
        prompt = f"""Translate the following medical query to Swedish. Keep medical terminology accurate and natural.
        
Query: {text}

Respond ONLY with the Swedish translation, nothing else."""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        swedish_text = response.content.strip()
        
        # Remove any markdown formatting if present
        if swedish_text.startswith("**"):
            swedish_text = swedish_text.replace("**", "")
        
        logger.debug(f"🔤 Translated: '{text}' → '{swedish_text}'")
        return swedish_text
    except Exception as e:
        logger.error(f"⚠️ Translation error: {str(e)}. Using original text.")
        return text

def detect_language(text: str) -> str:
    """Simple language detection - checks if text is likely English or Swedish."""
    # Common English medical terms
    english_terms = {"pain", "hurt", "symptom", "fever", "headache", "disease", "treatment", "doctor", "hospital", "health"}
    # Common Swedish medical terms
    swedish_terms = {"smärta", "ont", "symptom", "feber", "huvudvärk", "sjukdom", "behandling", "läkare", "sjukhus", "hälsa"}
    
    text_lower = text.lower()
    
    english_count = sum(1 for term in english_terms if term in text_lower)
    swedish_count = sum(1 for term in swedish_terms if term in text_lower)
    
    if english_count > swedish_count:
        return "en"
    elif swedish_count > english_count:
        return "sv"
    else:
        # Default to English if unclear
        return "en"

class WebSearcher:
    """Unified interface for web search APIs focused on approved medical sources."""
    
    def __init__(self, api_type: str = "serpapi"):
        """
        Initialize the web searcher.
        
        Args:
            api_type: Type of API to use ('serpapi', 'bing', 'google')
        """
        self.api_type = api_type
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        if self.api_type == "serpapi":
            return os.getenv("SERPAPI_API_KEY")
        elif self.api_type == "bing":
            return os.getenv("BING_SEARCH_API_KEY")
        elif self.api_type == "google":
            return os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        return None
    
    def search_medical_info(self, query: str, max_results: int = 5) -> Dict[str, any]:
        """
        Search for medical information from approved domains.
        Automatically translates English queries to Swedish for better results.
        
        Args:
            query: Medical query/symptoms (in English or Swedish)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and sources
        """
        # Detect language and translate if needed
        detected_lang = detect_language(query)
        
        if detected_lang == "en":
            logger.debug(f"🌐 English query detected, translating to Swedish...")
            swedish_query = translate_to_swedish(query)
        else:
            swedish_query = query
            logger.debug(f"🌐 Swedish query detected, using as-is")
        
        if not self.api_key:
            return self._fallback_search(query)
        
        if self.api_type == "serpapi":
            return self._search_serpapi(swedish_query, max_results)
        elif self.api_type == "bing":
            return self._search_bing(swedish_query, max_results)
        elif self.api_type == "google":
            return self._search_google(swedish_query, max_results)
        else:
            return self._fallback_search(query)
    
    def _search_serpapi(self, query: str, max_results: int) -> Dict:
        """Search using SerpAPI."""
        try:
            results = []
            sources = []
            
            # Create domain filter for approved sites
            domain_filter = " OR ".join([f"site:{domain}" for domain in APPROVED_MEDICAL_DOMAINS])
            search_query = f"{query} ({domain_filter})"
            
            logger.debug(f"🔍 Searching SerpAPI with query: {search_query}")
            
            url = "https://serpapi.com/search"
            params = {
                "q": search_query,
                "api_key": self.api_key,
                "num": max_results,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=10)
            logger.debug(f"📡 SerpAPI Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract organic results
                for result in data.get("organic_results", [])[:max_results]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    
                    if snippet:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })
                        if link:
                            sources.append(link)
                
                logger.debug(f"✅ Found {len(results)} results from approved medical sources")
                
                return {
                    "success": bool(results),
                    "results": results,
                    "sources": sources,
                    "message": f"Found {len(results)} results from approved medical sources."
                }
            else:
                logger.error(f"❌ SerpAPI returned status {response.status_code}")
                return {
                    "success": False,
                    "results": [],
                    "sources": [],
                    "message": f"Search API returned status {response.status_code}"
                }
        except Exception as e:
            logger.error(f"❌ Error during SerpAPI search: {str(e)}")
            return {
                "success": False,
                "results": [],
                "sources": [],
                "message": f"Error during search: {str(e)}"
            }
    
    def _search_bing(self, query: str, max_results: int) -> Dict:
        """Search using Bing Search API."""
        try:
            results = []
            sources = []
            
            # Create domain filter
            domain_filter = " OR ".join([f"site:{domain}" for domain in APPROVED_MEDICAL_DOMAINS])
            search_query = f"{query} ({domain_filter})"
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": search_query, "count": max_results}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get("webPages", {}).get("value", [])[:max_results]:
                    results.append({
                        "title": result.get("name", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("url", "")
                    })
                    if result.get("url"):
                        sources.append(result.get("url"))
                
                return {
                    "success": bool(results),
                    "results": results,
                    "sources": sources,
                    "message": f"Found {len(results)} results from approved medical sources."
                }
            else:
                return {
                    "success": False,
                    "results": [],
                    "sources": [],
                    "message": f"Search API returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "sources": [],
                "message": f"Error during search: {str(e)}"
            }
    
    def _search_google(self, query: str, max_results: int) -> Dict:
        """Search using Google Custom Search API."""
        try:
            results = []
            sources = []
            
            # Create domain filter
            domain_filter = " OR ".join([f"site:{domain}" for domain in APPROVED_MEDICAL_DOMAINS])
            search_query = f"{query} ({domain_filter})"
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": search_query,
                "key": os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY"),
                "cx": os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID"),
                "num": max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get("items", [])[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", "")
                    })
                    if result.get("link"):
                        sources.append(result.get("link"))
                
                return {
                    "success": bool(results),
                    "results": results,
                    "sources": sources,
                    "message": f"Found {len(results)} results from approved medical sources."
                }
            else:
                return {
                    "success": False,
                    "results": [],
                    "sources": [],
                    "message": f"Search API returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "sources": [],
                "message": f"Error during search: {str(e)}"
            }
    
    def _fallback_search(self, query: str) -> Dict:
        """Fallback when no API key is configured."""
        return {
            "success": False,
            "results": [],
            "sources": [],
            "message": (
                f"No search API configured. Please set up one of the following:\n"
                f"1. SerpAPI: Set SERPAPI_API_KEY environment variable\n"
                f"2. Bing Search: Set BING_SEARCH_API_KEY environment variable\n"
                f"3. Google Custom Search: Set GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID\n\n"
                f"For testing, consider using SerpAPI (free tier available): https://serpapi.com"
            )
        }

# Default searcher instance
_default_searcher = None

def get_searcher(api_type: str = "serpapi") -> WebSearcher:
    """Get or create a searcher instance."""
    global _default_searcher
    if _default_searcher is None:
        _default_searcher = WebSearcher(api_type)
    return _default_searcher

def search_medical_sources(query: str, api_type: str = "serpapi") -> Dict:
    """Convenience function to search medical sources."""
    searcher = WebSearcher(api_type)
    return searcher.search_medical_info(query)
