# Auto-generated LangChain tool for: extract_main_content_from_url
# Module: Finbyzweb


from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

@tool("extract_main_content_from_url", return_direct=False)
def extract_main_content_from_url_tool(url: str) -> str:
    """
    Extracts all text inside the <main> tag from the given website URL.

    Args:
        url (str): The URL of the website.

    Returns:
        str: Text content inside the <main> tag, or an error message if not found.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching URL: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    main_tag = soup.find("main")
    if main_tag:
        text = main_tag.get_text(separator="\n", strip=True)
        return text
    else:
        body_tag = soup.find("body")
        text = body_tag.get_text(separator="\n", strip=True) if body_tag else "No <main> or <body> tag found on this page."
        return text

