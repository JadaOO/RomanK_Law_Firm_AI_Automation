import json
from pathlib import Path
import datetime

import streamlit as st

# Data files: project_root/db/client.json and project_root/db/billing.json
DB_DIR = Path(__file__).resolve().parent.parent / "db"
CLIENT_FILE = DB_DIR / "client.json"
BILLING_FILE = DB_DIR / "billing.json"


def _load_clients():
    """Load all clients from client.json. Returns list of client dicts."""
    if not CLIENT_FILE.exists():
        return []
    try:
        with CLIENT_FILE.open("r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_clients(clients):
    """Persist clients list to client.json."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with CLIENT_FILE.open("w") as f:
        json.dump(clients, f, indent=2)


def _load_billings():
    """Load all billing entries from billing.json. Returns list of dicts. Ensures each has an id."""
    if not BILLING_FILE.exists():
        return []
    try:
        with BILLING_FILE.open("r") as f:
            billings = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(billings, list):
        return []
    # Ensure every entry has a unique id (migrate legacy data)
    max_id = 0
    for b in billings:
        if isinstance(b.get("id"), (int, float)):
            max_id = max(max_id, int(b["id"]))
    changed = False
    for b in billings:
        if b.get("id") is None or not isinstance(b.get("id"), (int, float)):
            max_id += 1
            b["id"] = max_id
            changed = True
    if changed:
        _save_billings(billings)
    return billings


def _save_billings(billings):
    """Persist billing entries list to billing.json. Flush so file is updated immediately."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with BILLING_FILE.open("w") as f:
        json.dump(billings, f, indent=2)
        f.flush()


def _next_billing_id(billings):
    """Return next unique id for a new billing entry."""
    if not billings:
        return 1
    ids = [b.get("id", 0) for b in billings if isinstance(b.get("id"), (int, float))]
    return max(ids, default=0) + 1


def _find_billing_by_id(billings, billing_id):
    """Return index of billing with given id, or -1."""
    for i, b in enumerate(billings):
        if b.get("id") == billing_id:
            return i
    return -1


def billing_payment():
    """Billing & Payment UI: Add Client via pop-up-like form and save to db/client.json."""
    st.header("Billing and Payment System")

    clients = _load_clients()

    # Show existing clients; click row (expander) to view details and actions
    if clients:
        st.subheader("Clients")
        for idx, c in enumerate(clients):
            name = c.get("name", "Unnamed")
            email = c.get("email", "")
            status_val = c.get("status", "inactive")
            status = status_val.capitalize()
            label = f"{name} — {email} ({status})"

            with st.expander(label, expanded=False):
                st.write(f"**Name:** {name}")
                st.write(f"**Email:** {email}")
                st.write(f"**Phone:** {c.get('phone', '')}")
                st.write(f"**Address:** {c.get('address', '')}")
                st.write(f"**Case Number:** {c.get('case_number', '')}")
                st.write(f"**Case Link:** {c.get('case_link', '')}")
                st.write(f"**Case Description:** {c.get('case_description', '')}")
                st.write(f"**Status:** {status_val}")

                col_billing, col_show, col_u, col_d = st.columns(4)
                with col_billing:
                    add_billing_clicked = st.button(
                        "Add Billing",
                        key=f"add_billing_{idx}",
                    )
                with col_show:
                    show_billing_clicked = st.button(
                        "Show Billing",
                        key=f"show_billing_{idx}",
                    )
                with col_u:
                    update_clicked = st.button(
                        "Update Client",
                        key=f"update_client_{idx}",
                        type="secondary",
                    )
                with col_d:
                    delete_clicked = st.button(
                        "Delete Client",
                        key=f"delete_client_{idx}",
                        type="primary",
                    )

                if add_billing_clicked:
                    st.session_state["add_billing_client_idx"] = idx
                    st.session_state.pop("show_billing_client_idx", None)
                    st.rerun()
                if show_billing_clicked:
                    st.session_state["show_billing_client_idx"] = idx
                    st.session_state.pop("add_billing_client_idx", None)
                    st.rerun()

                # Inline Add Billing form when this client is selected
                if st.session_state.get("add_billing_client_idx") == idx:
                    st.markdown("#### Add Billing")
                    with st.form(f"add_billing_form_{idx}", clear_on_submit=True):
                        # auto-populated from client
                        b_name = st.text_input("Name", value=name, disabled=True)
                        b_email = st.text_input("Email", value=email, disabled=True)
                        b_date = st.date_input("Date", value=datetime.date.today())
                        b_ee = st.text_input("EE")
                        b_activity = st.text_input("Activity")
                        b_description = st.text_area("Description")
                        b_rate = st.number_input("Rate", min_value=0.0, step=0.01)
                        b_hours = st.number_input("Hours", min_value=0.0, step=0.1)
                        # Line Total = Rate × Hours (calculated, not entered)
                        line_total = b_rate * b_hours
                        st.write(f"**Line Total (Rate × Hours):** ${line_total:,.2f}")

                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            save_billing = st.form_submit_button("Add Billing")
                        with col_b2:
                            cancel_billing = st.form_submit_button("Cancel")

                        if cancel_billing:
                            st.session_state.pop("add_billing_client_idx", None)
                            st.rerun()

                        if save_billing:
                            billings = _load_billings()
                            new_id = _next_billing_id(billings)
                            billings.append(
                                {
                                    "id": new_id,
                                    "client_index": idx,
                                    "client_name": name,
                                    "client_email": email,
                                    "date": b_date.isoformat(),
                                    "ee": b_ee.strip(),
                                    "activity": b_activity.strip(),
                                    "description": b_description.strip(),
                                    "rate": b_rate,
                                    "hours": b_hours,
                                    "line_total": line_total,
                                }
                            )
                            _save_billings(billings)
                            st.success("Billing entry added.")
                            st.session_state.pop("add_billing_client_idx", None)
                            st.rerun()

                # Show all billings for this client when "Show Billing" was clicked
                if st.session_state.get("show_billing_client_idx") == idx:
                    st.markdown("#### Billing for this client")
                    # Always load fresh from file so updates/deletes are reflected
                    all_billings = _load_billings()
                    client_billings = [b for b in all_billings if b.get("client_index") == idx]
                    if not client_billings:
                        st.info("No billing entries for this client.")
                    else:
                        for b in client_billings:
                            billing_id = b.get("id")
                            if billing_id is None:
                                continue
                            # Use current values from loaded data for display
                            b_date_str = b.get("date", "")
                            b_activity = b.get("activity", "")
                            b_line_total = b.get("line_total", 0)
                            if isinstance(b_line_total, (int, float)):
                                line_fmt = f"${float(b_line_total):,.2f}"
                            else:
                                line_fmt = str(b_line_total)
                            with st.expander(f"{b_date_str} — {b_activity} — {line_fmt}"):
                                st.write(f"**Date:** {b.get('date', '')}")
                                st.write(f"**EE:** {b.get('ee', '')}")
                                st.write(f"**Activity:** {b.get('activity', '')}")
                                st.write(f"**Description:** {b.get('description', '')}")
                                st.write(f"**Rate:** ${float(b.get('rate', 0)):,.2f}")
                                st.write(f"**Hours:** {b.get('hours', 0)}")
                                st.write(f"**Line Total (Rate × Hours):** ${float(b.get('line_total', 0)):,.2f}")

                                # Show update form if this billing is being edited (so submit is processed on rerun)
                                editing_id = st.session_state.get("editing_billing_id")
                                show_update_form = editing_id == billing_id

                                if not show_update_form:
                                    col_bu, col_bd = st.columns(2)
                                    with col_bu:
                                        update_billing = st.button(
                                            "Update",
                                            key=f"update_billing_{billing_id}",
                                        )
                                    with col_bd:
                                        delete_billing = st.button(
                                            "Delete",
                                            key=f"delete_billing_{billing_id}",
                                        )

                                    if delete_billing:
                                        mutable_billings = _load_billings()
                                        di = _find_billing_by_id(mutable_billings, billing_id)
                                        if di >= 0:
                                            mutable_billings.pop(di)
                                            _save_billings(mutable_billings)
                                        st.success("Billing entry deleted.")
                                        st.session_state["show_billing_client_idx"] = idx
                                        st.rerun()

                                    if update_billing:
                                        st.session_state["editing_billing_id"] = billing_id
                                        st.session_state["show_billing_client_idx"] = idx
                                        st.rerun()

                                if show_update_form:
                                    # Inline update form: shown when editing_billing_id is set so submit runs on next rerun
                                    with st.form(f"update_billing_form_{billing_id}", clear_on_submit=True):
                                        ub_date = st.date_input(
                                            "Date",
                                            value=datetime.date.fromisoformat(
                                                b.get("date", datetime.date.today().isoformat())
                                            ),
                                            key=f"ub_date_{billing_id}",
                                        )
                                        ub_ee = st.text_input("EE", value=b.get("ee", ""), key=f"ub_ee_{billing_id}")
                                        ub_activity = st.text_input("Activity", value=b.get("activity", ""), key=f"ub_activity_{billing_id}")
                                        ub_description = st.text_area("Description", value=b.get("description", ""), key=f"ub_desc_{billing_id}")
                                        ub_rate = st.number_input("Rate", min_value=0.0, step=0.01, value=float(b.get("rate", 0.0)), key=f"ub_rate_{billing_id}")
                                        ub_hours = st.number_input("Hours", min_value=0.0, step=0.1, value=float(b.get("hours", 0.0)), key=f"ub_hours_{billing_id}")
                                        ub_line_total = ub_rate * ub_hours
                                        st.write(f"**Line Total (Rate × Hours):** ${ub_line_total:,.2f}")
                                        save_btn = st.form_submit_button("Save Billing Changes")
                                        cancel_btn = st.form_submit_button("Cancel")

                                        if cancel_btn:
                                            st.session_state.pop("editing_billing_id", None)
                                            st.session_state["show_billing_client_idx"] = idx
                                            st.rerun()

                                        if save_btn:
                                            all_bills = _load_billings()
                                            ui = _find_billing_by_id(all_bills, billing_id)
                                            if ui >= 0:
                                                all_bills[ui].update({
                                                    "date": ub_date.isoformat(),
                                                    "ee": ub_ee.strip(),
                                                    "activity": ub_activity.strip(),
                                                    "description": ub_description.strip(),
                                                    "rate": ub_rate,
                                                    "hours": ub_hours,
                                                    "line_total": ub_line_total,
                                                })
                                                _save_billings(all_bills)
                                            st.session_state.pop("editing_billing_id", None)
                                            st.session_state["show_billing_client_idx"] = idx
                                            st.success("Billing entry updated.")
                                            st.rerun()
                    if st.button("Close", key=f"close_show_billing_{idx}"):
                        st.session_state.pop("show_billing_client_idx", None)
                        st.rerun()

                if delete_clicked:
                    remaining = _load_clients()
                    if 0 <= idx < len(remaining):
                        remaining.pop(idx)
                        _save_clients(remaining)
                    st.success("Client deleted.")
                    st.rerun()

                if update_clicked:
                    # Simple inline update form prefilled with current values
                    with st.form(f"update_client_form_{idx}", clear_on_submit=False):
                        new_name = st.text_input("Name", value=name)
                        new_email = st.text_input("Email", value=email)
                        new_phone = st.text_input("Phone", value=c.get("phone", ""))
                        new_address = st.text_area("Address", value=c.get("address", ""))
                        new_case_number = st.text_input(
                            "Case Number", value=c.get("case_number", "")
                        )
                        new_case_link = st.text_input(
                            "Case Link", value=c.get("case_link", "")
                        )
                        new_case_description = st.text_area(
                            "Case Description", value=c.get("case_description", "")
                        )
                        new_status = st.radio(
                            "Active status",
                            options=["active", "inactive"],
                            index=0 if status_val == "active" else 1,
                            horizontal=True,
                            key=f"update_status_{idx}",
                        )

                        save_update = st.form_submit_button("Save Changes")

                        if save_update:
                            all_clients = _load_clients()
                            if 0 <= idx < len(all_clients):
                                all_clients[idx] = {
                                    "name": new_name.strip(),
                                    "email": new_email.strip(),
                                    "phone": new_phone.strip(),
                                    "address": new_address.strip(),
                                    "case_number": new_case_number.strip(),
                                    "case_link": new_case_link.strip(),
                                    "case_description": new_case_description.strip(),
                                    "status": new_status,
                                }
                                _save_clients(all_clients)
                                st.success("Client updated.")
                                st.rerun()
    else:
        st.info("No clients yet. Click 'Add Client' to create one.")

    # Modal-like behavior: toggle visibility of the form
    if "show_add_client_form" not in st.session_state:
        st.session_state["show_add_client_form"] = False

    if st.button("Add Client"):
        st.session_state["show_add_client_form"] = True

    if st.session_state["show_add_client_form"]:
        with st.container():
            st.markdown("### New Client")
            with st.form("add_client_form", clear_on_submit=True):
                name = st.text_input("Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                address = st.text_area("Address")
                case_number = st.text_input("Case Number")
                case_link = st.text_input("Case Link")
                case_description = st.text_area("Case Description")
                status = st.radio(
                    "Active status",
                    options=["active", "inactive"],
                    horizontal=True,
                )

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Add Client")
                with col2:
                    cancel = st.form_submit_button("Cancel")

                if cancel:
                    st.session_state["show_add_client_form"] = False

                if submit and name.strip():
                    new_client = {
                        "name": name.strip(),
                        "email": email.strip(),
                        "phone": phone.strip(),
                        "address": address.strip(),
                        "case_number": case_number.strip(),
                        "case_link": case_link.strip(),
                        "case_description": case_description.strip(),
                        "status": status,
                    }
                    clients = _load_clients()
                    clients.append(new_client)
                    _save_clients(clients)
                    st.success("Client added.")
                    st.session_state["show_add_client_form"] = False
                    st.rerun()

