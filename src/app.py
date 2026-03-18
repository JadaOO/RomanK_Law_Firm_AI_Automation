import sys
from pathlib import Path

# Ensure project root and src are on path (so config and agent/legal_searcher load)
_root = Path(__file__).resolve().parent.parent
_src = Path(__file__).resolve().parent
for p in (_root, _src):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
from legal_searcher import legal_searcher
from law_automation import LawAutomation
# from sendgrid import send_email
from homepage_calendar import show_calendar
from billing_payment import billing_payment


law_automation = LawAutomation()

def main():
    css_path = Path(__file__).parent / "styles.css"
    css = css_path.read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.title("Roman Kostenko's Law Office")

    tab_calendar, tab_research,tab_email, tab_billing = st.tabs([
        "Calendar",
        "Legal Research, Email Writing, and Petition Drafting",
        "Send Email",
        "Billing & Payment"
    ])

    with tab_calendar:
        show_calendar()
    with tab_research:
        legal_searcher()
    with tab_email:
        st.header("email")
    with tab_billing:
        billing_payment()

def home_page():
    st.header("Home Page: Event Management")

    with st.form("add_event"):
        event_name = st.text_input("Event Name")
        location = st.text_input("Location")
        time = st.text_input("Time")
        details = st.text_area("Details")
        client = st.text_input("Client")
        submit_event = st.form_submit_button("Add Event")

        if submit_event:
            law_automation.add_event(event_name, location, time, details, client)
            st.success("Event added successfully!")
    
    st.subheader("Events List")
    date = st.date_input("Date")
    events = law_automation.list_events(date.isoformat())

    for event in events:
        with st.expander(f"{event['event_name']} at {event['time']}"):
            st.write(f"Location: {event['location']}")
            st.write(f"Details: {event['details']}")
            st.write(f"Client: {event['client']}")
            if st.button("Remove", key=event['id']):
                law_automation.remove_event(event['id'])
                st.success("Event removed successfully!")

# def legal_research_writing():
#     st.header("Legal Research and Writing")

#     query = st.text_input("Enter query for Arizona Law:")
#     if st.button("Search"):
#         research_results = law_automation.perform_legal_research(query)
#         st.write(research_results)

#     client_id = st.number_input("Client ID", min_value=0, step=1)
#     research_text = st.text_area("Research")
#     writing_text = st.text_area("Writing")
#     if st.button("Save"):
#         law_automation.store_research_and_writing(client_id, research_text, writing_text)
#         st.success("Research and writing saved successfully!")

# def billing_payment():
#     st.header("Billing and Payment System")

#     with st.form("manage_client"):
#         name = st.text_input("Name")
#         email = st.text_input("Email")
#         phone = st.text_input("Phone")
#         address = st.text_input("Address")
#         city = st.text_input("City")
#         state = st.text_input("State")
#         zip_code = st.text_input("ZIP")
#         country = st.text_input("Country")
#         case_number = st.text_input("Case Number")
#         case_type = st.text_input("Case Type")
#         case_status = st.text_input("Case Status")
#         case_description = st.text_area("Case Description")
#         submit_client = st.form_submit_button("Add Client")

#         if submit_client:
#             client_id = law_automation.add_client(name, email, phone, address, city, state, zip_code, country, case_number, case_type, case_status, case_description)
#             st.success(f"Client added with ID {client_id}")

#     client_id = st.number_input("Client ID for Billing", min_value=0, step=1)
#     if client_id:
#         client_data = law_automation.view_client(client_id)
#         if client_data:
#             st.write(client_data)

#             with st.form("billing_services"):
#                 service_name = st.text_input("Service Name")
#                 service_description = st.text_input("Service Description")
#                 service_price = st.number_input("Service Price", min_value=0.0)
#                 service_quantity = st.number_input("Service Quantity", min_value=1)
#                 service_date = st.date_input("Service Date").isoformat()
#                 submit_service = st.form_submit_button("Add Billing Service")
    
#                 if submit_service:
#                     law_automation.add_billing_service(client_id, service_name, service_description, service_price, service_quantity, service_date)
#                     st.success("Billing service added successfully!")

#             if st.button("Generate Invoice PDF"):
#                 invoice_path = law_automation.generate_invoice_pdf(client_id)
#                 if invoice_path:
#                     st.success(f"Invoice generated at {invoice_path}")
#                 else:
#                     st.warning("Total price is below the threshold to generate an invoice.")

#             if st.button("Send Payment Reminder"):
#                 law_automation.send_payment_reminder(client_id)
#                 st.success("Payment reminder sent successfully!")

if __name__ == "__main__":
    main()