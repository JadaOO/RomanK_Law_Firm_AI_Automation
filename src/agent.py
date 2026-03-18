from serper_search import search_az_family_law
from azlaw_scraper import fetch_law_context
from chatbot_law_check import ask_gpt


def legal_chat(question):

    # 1 Search statutes
    links = search_az_family_law(question)

    # 2 Retrieve legal text
    context = fetch_law_context(links)

    # 3 Ask GPT
    answer = ask_gpt(question, context)

    return answer, links
