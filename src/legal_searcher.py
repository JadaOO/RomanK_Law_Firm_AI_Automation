import streamlit as st


def _legal_chat_backend(question):
    """Run search + scrape + GPT. Imports here so app loads even if deps fail."""
    from serper_search import search_az_family_law
    from azlaw_scraper import fetch_law_context
    from chatbot_law_check import ask_gpt

    links = search_az_family_law(question)
    context = fetch_law_context(links)
    answer = ask_gpt(question, context)
    return answer, links


def legal_searcher():
    """My name is Roman Kostenko, I am a family law attorney in Arizona. 
    You will be my legal assistant that elp me with my legal research, petition drafting, and email writing. 
    You will be able to search the internet for the relevant laws and cases based on Arizona Law.
    Return all related laws and cases in the answer.
    You will draft the legal documents based on the research and the attorney's instructions.
    You will draft email messages based on the research and the attorney's instructions.
    Always use the Arizona Law to answer the questions.
    Put the relevant laws and cases in the answer.
    If the question is not clear, ask for more details.
    You will read court ruling and draft a summary of the court ruling for my client, 
    Always put the favorable ruling first then emphasize the avorable ruling.
    Tones and style of the email messages should be professional and respectful.


    Alway put my details at the end of the email:
    My Name: Roman Kostenko
    My Address:Law Office of Roman A. Kostenko, P.L.C.
    202 E. Earll Drive, Suite 490
    Phoenix, Arizona 85012
    Phone: (602) 265-1987
    Fax: (480) 550-8733
    """
    st.write("Hi Roman, how can I help you today?")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"]) 

    prompt = st.chat_input("legal research, draft petitions, write emails and more...")

    if prompt:
        st.chat_message("user").write(prompt)

        with st.spinner("Researching Arizona law..."):
            try:
                answer, sources = _legal_chat_backend(prompt)
            except Exception as e:
                st.error(f"Backend error: {e}")
                return

        # Show each source on its own, separated by a blank line
        if sources:
            response = answer + "\n\nSources:\n\n" + "\n\n".join(sources)
        else:
            response = answer

        # Show assistant response with copy icon (via styled code block)
        with st.chat_message("assistant"):
            st.code(response, language="text")

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": response})