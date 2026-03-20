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


    Put {ATTORNEY_NAME} {ATTORNEY_ADDRESS} {ATTORNEY_PHONE} {ATTORNEY_EMAIL} at the end of the email:
    """
    st.write("Hi Roman, how can I help you today?")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"]) 

    # Reliable inline row: + popover (left) + chat input (middle) + send button (right)
    with st.form("legal_chat_inline_form", clear_on_submit=True):
        col_add, col_input, col_send = st.columns([1, 8, 1.4])
        with col_add:
            with st.popover("➕"):
                st.markdown("📎 **Add Photo & Files**")
                uploaded = st.file_uploader(
                    "Add Photo & Files",
                    accept_multiple_files=True,
                    type=None,
                    key="legal_searcher_uploads",
                    label_visibility="collapsed",
                )
                if uploaded:
                    st.session_state["legal_searcher_uploaded_files"] = [f.name for f in uploaded]
                    st.caption(f"Selected: {', '.join(st.session_state['legal_searcher_uploaded_files'])}")
        with col_input:
            prompt = st.text_input(
                "Message",
                placeholder="legal research, draft petitions, write emails and more...",
                key="legal_prompt_inline",
                label_visibility="collapsed",
            )
        with col_send:
            submitted = st.form_submit_button("Send")

    if submitted and prompt.strip():
        prompt = prompt.strip()
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