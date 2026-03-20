import datetime
import base64
import json
import os
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

DB_DIR = Path(__file__).resolve().parent.parent / "db"
CLIENT_FILE = DB_DIR / "client.json"
BILLING_FILE = DB_DIR / "billing.json"
TO_BE_PAID_BILLING_FILE = DB_DIR / "to_be_paid_billing.json"
STATEMENTS_DIR = DB_DIR / "statements"


def _load_clients():
    if not CLIENT_FILE.exists():
        return []
    try:
        with CLIENT_FILE.open("r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_clients(clients):
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with CLIENT_FILE.open("w") as f:
        json.dump(clients, f, indent=2)
        f.flush()


def _load_billings():
    if not BILLING_FILE.exists():
        return []
    try:
        with BILLING_FILE.open("r") as f:
            billings = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(billings, list):
        return []

    max_id = 0
    for b in billings:
        if isinstance(b.get("id"), (int, float)):
            max_id = max(max_id, int(b["id"]))
    changed = False
    for b in billings:
        if not isinstance(b.get("id"), (int, float)):
            max_id += 1
            b["id"] = max_id
            changed = True
    if changed:
        _save_billings(billings)
    return billings


def _save_billings(billings):
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with BILLING_FILE.open("w") as f:
        json.dump(billings, f, indent=2)
        f.flush()


def _load_to_be_paid_billings():
    if not TO_BE_PAID_BILLING_FILE.exists():
        return []
    try:
        with TO_BE_PAID_BILLING_FILE.open("r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_to_be_paid_billings(entries):
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with TO_BE_PAID_BILLING_FILE.open("w") as f:
        json.dump(entries, f, indent=2)
        f.flush()


def _next_billing_id(billings):
    ids = [int(b.get("id", 0)) for b in billings if isinstance(b.get("id"), (int, float))]
    return (max(ids) + 1) if ids else 1


def _find_billing_by_id(billings, billing_id):
    for i, b in enumerate(billings):
        if b.get("id") == billing_id:
            return i
    return -1


def _generate_invoice_pdf(client, client_billings, client_total):
    try:
        from fpdf import FPDF
    except Exception as e:
        raise RuntimeError("FPDF missing. Install: pip install fpdf2") from e

    STATEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    invoice_number = str(random.randint(10000, 99999))
    created_date = datetime.date.today()
    payment_deadline = created_date + datetime.timedelta(days=14)

    attorney_name = os.getenv("ATTORNEY_NAME", "")
    attorney_address = os.getenv("ATTORNEY_ADDRESS", "")
    attorney_phone = os.getenv("ATTORNEY_PHONE", "")
    attorney_email = os.getenv("ATTORNEY_EMAIL", "")
    attorney_fax = os.getenv("ATTORNEY_FAX", "")
    payment_url = os.getenv("PAYMENT_URL", "")

    safe_client = str(client.get("name", "client")).strip().replace(" ", "_")
    pdf_path = STATEMENTS_DIR / f"Invoice_{created_date.isoformat()}_{safe_client}_{invoice_number}.pdf"

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Header left: attorney details
    pdf.set_xy(10, 10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(105, 5, attorney_name, ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(10)
    pdf.multi_cell(105, 4.5, " ".join(attorney_address.split()))
    pdf.set_x(10)
    pdf.cell(105, 4.5, f"Phone: {attorney_phone}", ln=1)
    pdf.set_x(10)
    pdf.cell(105, 4.5, f"Email: {attorney_email}", ln=1)
    pdf.set_x(10)
    pdf.cell(105, 4.5, f"Fax: {attorney_fax}", ln=1)
    left_bottom_y = pdf.get_y()

    # Header right: payment info
    pdf.set_xy(120, 10)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(80, 6, f"Payment URL: {payment_url}", ln=1, align="R")
    pdf.set_x(120)
    pdf.cell(80, 6, f"Payment Deadline: {payment_deadline.isoformat()}", ln=1, align="R")
    right_bottom_y = pdf.get_y()

    # Main form header
    pdf.set_y(max(left_bottom_y, right_bottom_y) + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Billing Invoice", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Client Name: {client.get('name', '')}", ln=1)
    pdf.cell(0, 6, f"Case Number: {client.get('case_number', '')}", ln=1)
    pdf.cell(0, 6, f"Date: {created_date.isoformat()}", ln=1)
    pdf.ln(2)

    headers = ["Date", "EE", "Activity", "Description", "Rate", "Hours", "Line Total"]
    widths = [20, 18, 28, 50, 18, 18, 28]
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for b in client_billings:
        row = [
            str(b.get("date", ""))[:10],
            str(b.get("ee", ""))[:10],
            str(b.get("activity", ""))[:16],
            str(b.get("description", ""))[:36],
            f"${float(b.get('rate', 0) or 0):,.2f}",
            f"{float(b.get('hours', 0) or 0):,.2f}",
            f"${float(b.get('line_total', 0) or 0):,.2f}",
        ]
        aligns = ["L", "L", "L", "L", "R", "R", "R"]
        for val, w, a in zip(row, widths, aligns):
            pdf.cell(w, 7, val, border=1, align=a)
        pdf.ln()

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(sum(widths[:-1]), 8, "Invoice Total", border=1, align="R")
    pdf.cell(widths[-1], 8, f"${client_total:,.2f}", border=1, align="R")

    pdf.output(str(pdf_path))
    return pdf_path, invoice_number, payment_deadline.isoformat()


def _archive_client_billings_after_invoice(
    client_index, client_name, client_email, invoice_number, invoice_pdf, payment_deadline
):
    all_billings = _load_billings()
    moving = [b for b in all_billings if b.get("client_index") == client_index]
    remaining = [b for b in all_billings if b.get("client_index") != client_index]
    if not moving:
        return 0

    queue = _load_to_be_paid_billings()
    queue.append(
        {
            "invoice_number": str(invoice_number),
            "client_index": client_index,
            "client_name": client_name,
            "client_email": client_email,
            "invoice_pdf": str(invoice_pdf),
            "invoice_date": datetime.date.today().isoformat(),
            "payment_deadline": payment_deadline,
            "status": "unpaid",
            "total_amount": sum(float(b.get("line_total", 0) or 0) for b in moving),
            "billings": moving,
        }
    )
    _save_to_be_paid_billings(queue)
    _save_billings(remaining)
    return len(moving)


def _delete_file_if_exists(file_path):
    raw = str(file_path or "").strip()
    if not raw:
        return
    p = Path(raw)
    if p.exists() and p.is_file():
        p.unlink()


def _revert_invoice_entry_to_billing(entry):
    restored = entry.get("billings", [])
    if not isinstance(restored, list) or not restored:
        return 0
    billings = _load_billings()
    next_id = _next_billing_id(billings)
    for b in restored:
        item = dict(b)
        item["id"] = next_id
        next_id += 1
        billings.append(item)
    _save_billings(billings)
    return len(restored)


def _auto_download_pdf(pdf_path):
    path = Path(pdf_path)
    if not path.exists():
        return
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    filename = path.name.replace("'", "_")
    components.html(
        f"""
        <script>
          (function() {{
            const b64 = "{encoded}";
            const bytes = atob(b64);
            const arr = new Uint8Array(bytes.length);
            for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
            const blob = new Blob([arr], {{ type: "application/pdf" }});
            const url = URL.createObjectURL(blob);
            const dataUrl = "data:application/pdf;base64," + b64;

            // Attempt 1: regular programmatic click
            try {{
              const a = document.createElement("a");
              a.href = url;
              a.download = '{filename}';
              a.style.display = "none";
              document.body.appendChild(a);
              a.click();
              a.remove();
            }} catch (e) {{}}

            // Attempt 2: open in new tab (often bypasses blocked auto-download)
            try {{
              const w = window.open(url, "_blank");
              if (w && typeof w.focus === "function") w.focus();
            }} catch (e) {{}}

            // Attempt 3: force top-level navigation to inline PDF data
            try {{
              if (window.top) {{
                window.top.location.href = dataUrl;
              }}
            }} catch (e) {{}}

            setTimeout(() => URL.revokeObjectURL(url), 3000);
          }})();
        </script>
        """,
        height=1,
    )


def _show_client_billing(client_idx, client_name, client_email, client_obj):
    all_billings = _load_billings()
    client_billings = [b for b in all_billings if b.get("client_index") == client_idx]
    client_total = sum(float(b.get("line_total", 0) or 0) for b in client_billings)

    st.markdown(f"#### Billing for this client — Total: ${client_total:,.2f}")
    if not client_billings:
        st.info("No billing entries for this client.")
        return

    for b in client_billings:
        billing_id = b.get("id")
        with st.expander(
            f"{b.get('date','')} — {b.get('activity','')} — ${float(b.get('line_total', 0) or 0):,.2f}"
        ):
            st.write(f"**Date:** {b.get('date', '')}")
            st.write(f"**EE:** {b.get('ee', '')}")
            st.write(f"**Activity:** {b.get('activity', '')}")
            st.write(f"**Description:** {b.get('description', '')}")
            st.write(f"**Rate:** ${float(b.get('rate', 0) or 0):,.2f}")
            st.write(f"**Hours:** {float(b.get('hours', 0) or 0):,.2f}")
            st.write(f"**Line Total (Rate × Hours):** ${float(b.get('line_total', 0) or 0):,.2f}")

            editing = st.session_state.get("editing_billing_id") == billing_id
            if not editing:
                col_u, col_d = st.columns(2)
                if col_u.button("Update", key=f"update_billing_{billing_id}"):
                    st.session_state["editing_billing_id"] = billing_id
                    st.rerun()
                if col_d.button("Delete", key=f"delete_billing_{billing_id}"):
                    mutable = _load_billings()
                    di = _find_billing_by_id(mutable, billing_id)
                    if di >= 0:
                        mutable.pop(di)
                        _save_billings(mutable)
                    st.success("Billing entry deleted.")
                    st.rerun()
            else:
                with st.form(f"update_billing_form_{billing_id}", clear_on_submit=True):
                    ub_date = st.date_input(
                        "Date",
                        value=datetime.date.fromisoformat(
                            b.get("date", datetime.date.today().isoformat())
                        ),
                    )
                    ub_ee = st.text_input("EE", value=b.get("ee", ""))
                    ub_activity = st.text_input("Activity", value=b.get("activity", ""))
                    ub_description = st.text_area("Description", value=b.get("description", ""))
                    ub_rate = st.number_input("Rate", min_value=0.0, step=0.01, value=float(b.get("rate", 0) or 0))
                    ub_hours = st.number_input("Hours", min_value=0.0, step=0.1, value=float(b.get("hours", 0) or 0))
                    ub_line_total = ub_rate * ub_hours
                    st.write(f"**Line Total (Rate × Hours):** ${ub_line_total:,.2f}")

                    s1, s2 = st.columns(2)
                    save_btn = s1.form_submit_button("Save Billing Changes")
                    cancel_btn = s2.form_submit_button("Cancel")
                    if cancel_btn:
                        st.session_state.pop("editing_billing_id", None)
                        st.rerun()
                    if save_btn:
                        all_bills = _load_billings()
                        ui = _find_billing_by_id(all_bills, billing_id)
                        if ui >= 0:
                            all_bills[ui].update(
                                {
                                    "date": ub_date.isoformat(),
                                    "ee": ub_ee.strip(),
                                    "activity": ub_activity.strip(),
                                    "description": ub_description.strip(),
                                    "rate": ub_rate,
                                    "hours": ub_hours,
                                    "line_total": ub_line_total,
                                }
                            )
                            _save_billings(all_bills)
                        st.session_state.pop("editing_billing_id", None)
                        st.success("Billing entry updated.")
                        st.rerun()

    history_key = f"show_invoice_history_{client_idx}"
    if history_key not in st.session_state:
        st.session_state[history_key] = False

    close_col, history_col, create_col = st.columns(3)
    if close_col.button("Close", key=f"close_show_billing_{client_idx}"):
        st.session_state.pop("show_billing_client_idx", None)
        st.rerun()
    if history_col.button("View Invoice History", key=f"history_invoice_{client_idx}"):
        st.session_state[history_key] = not st.session_state[history_key]
        st.rerun()
    if create_col.button("Create a Billing Invoice", key=f"create_invoice_{client_idx}"):
        pdf_path, invoice_number, deadline = _generate_invoice_pdf(client_obj, client_billings, client_total)
        moved = _archive_client_billings_after_invoice(
            client_idx, client_name, client_email, invoice_number, pdf_path, deadline
        )
        _auto_download_pdf(str(pdf_path))
        st.success(
            f"Invoice created (#{invoice_number}). Moved {moved} billing item(s) "
            "to db/to_be_paid_billing.json."
        )

    if st.session_state.get(history_key):
        components.html(
            """
            <script>
              (function () {
                const labels = new Set(["Download", "Delete", "Revert", "Payment Received"]);
                const styleButtons = () => {
                  const doc = window.parent && window.parent.document ? window.parent.document : document;
                  const buttons = doc.querySelectorAll("button");
                  buttons.forEach((btn) => {
                    const txt = (btn.innerText || "").trim();
                    if (labels.has(txt)) {
                      btn.style.fontSize = "12px";
                      btn.style.padding = "0.25rem 0.5rem";
                      const p = btn.querySelector("p");
                      if (p) p.style.fontSize = "12px";
                    }
                  });
                };
                styleButtons();
                setTimeout(styleButtons, 100);
                setTimeout(styleButtons, 400);
              })();
            </script>
            """,
            height=0,
        )
        st.markdown("##### Invoice History")
        entries = [e for e in _load_to_be_paid_billings() if e.get("client_index") == client_idx]
        entries = list(reversed(entries))
        if not entries:
            st.info("No invoices found for this client.")
        else:
            for e in entries:
                raw_pdf_path = str(e.get("invoice_pdf", "") or "").strip()
                p = Path(raw_pdf_path) if raw_pdf_path else None
                invoice_no = str(e.get("invoice_number", ""))
                status_val = str(e.get("status", "unpaid")).lower()
                is_paid = status_val == "paid"
                if p and p.name and p.name not in {".", ".."}:
                    display_name = p.name
                else:
                    display_name = (
                        f"Invoice_{e.get('invoice_date','')}_{str(client_name).replace(' ', '_')}_{invoice_no}.pdf"
                    )
                status_html = (
                    "<span style='color:#16a34a;font-weight:600;'>paid</span>"
                    if is_paid
                    else "<span style='color:#dc2626;font-weight:600;'>unpaid</span>"
                )
                c_name, c_dl, c_delete, c_revert, c_paid = st.columns([4, 1, 1, 1, 1])
                c_name.markdown(f"{display_name} {status_html}", unsafe_allow_html=True)
                if p and p.exists() and p.is_file():
                    with p.open("rb") as f:
                        c_dl.download_button(
                            "Download",
                            data=f.read(),
                            file_name=display_name,
                            mime="application/pdf",
                            key=f"history_invoice_download_{client_idx}_{invoice_no}",
                        )
                else:
                    c_dl.caption("Missing")

                delete_key = f"delete_invoice_{client_idx}_{invoice_no}_{display_name}"
                if c_delete.button("Delete", key=delete_key, type="primary"):
                    queue = _load_to_be_paid_billings()
                    updated = []
                    removed = False
                    for q in queue:
                        q_invoice = str(q.get("invoice_number", ""))
                        q_pdf = str(q.get("invoice_pdf", "") or "").strip()
                        if (
                            not removed
                            and q.get("client_index") == client_idx
                            and q_invoice == invoice_no
                            and q_pdf == raw_pdf_path
                        ):
                            _delete_file_if_exists(q_pdf)
                            removed = True
                            continue
                        updated.append(q)
                    _save_to_be_paid_billings(updated)
                    st.success(f"Deleted invoice {invoice_no}.")
                    st.rerun()

                revert_key = f"revert_invoice_{client_idx}_{invoice_no}_{display_name}"
                if c_revert.button("Revert", key=revert_key):
                    queue = _load_to_be_paid_billings()
                    updated = []
                    reverted_count = 0
                    removed = False
                    for q in queue:
                        q_invoice = str(q.get("invoice_number", ""))
                        q_pdf = str(q.get("invoice_pdf", "") or "").strip()
                        if (
                            not removed
                            and q.get("client_index") == client_idx
                            and q_invoice == invoice_no
                            and q_pdf == raw_pdf_path
                        ):
                            reverted_count = _revert_invoice_entry_to_billing(q)
                            _delete_file_if_exists(q_pdf)
                            removed = True
                            continue
                        updated.append(q)
                    _save_to_be_paid_billings(updated)
                    st.success(
                        f"Reverted invoice {invoice_no}. Restored {reverted_count} billing item(s) to db/billing.json."
                    )
                    st.rerun()

                if not is_paid:
                    paid_key = f"paid_invoice_{client_idx}_{invoice_no}_{display_name}"
                    if c_paid.button("Payment Received", key=paid_key):
                        queue = _load_to_be_paid_billings()
                        for q in queue:
                            q_invoice = str(q.get("invoice_number", ""))
                            q_pdf = str(q.get("invoice_pdf", "") or "").strip()
                            if (
                                q.get("client_index") == client_idx
                                and q_invoice == invoice_no
                                and q_pdf == raw_pdf_path
                            ):
                                q["status"] = "paid"
                                q["paid_date"] = datetime.date.today().isoformat()
                                break
                        _save_to_be_paid_billings(queue)
                        st.success(f"Invoice {invoice_no} marked as paid.")
                        st.rerun()


def billing_payment():
    st.header("Billing and Payment System")

    if "show_add_client_form" not in st.session_state:
        st.session_state["show_add_client_form"] = False
    if "editing_client_idx" not in st.session_state:
        st.session_state["editing_client_idx"] = None

    clients = _load_clients()
    if clients:
        indexed_clients = list(enumerate(clients))
        active_clients = [
            (i, c)
            for i, c in indexed_clients
            if str(c.get("status", "inactive")).lower() == "active"
        ]
        inactive_clients = [
            (i, c)
            for i, c in indexed_clients
            if str(c.get("status", "inactive")).lower() != "active"
        ]

        for section_title, client_items in [
            ("Active Clients", active_clients),
            ("Inactive Clients", inactive_clients),
        ]:
            st.subheader(section_title)
            if not client_items:
                st.caption(f"No {section_title.lower()}.")
                continue

            for idx, c in client_items:
                name = c.get("name", "Unnamed")
                email = c.get("email", "")
                status_val = c.get("status", "inactive")
                label = f"{name} — {email} ({str(status_val).capitalize()})"

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
                    add_billing_clicked = col_billing.button("Add Billing", key=f"add_billing_{idx}")
                    show_billing_clicked = col_show.button("Show Billing", key=f"show_billing_{idx}")
                    update_clicked = col_u.button("Update Client", key=f"update_client_{idx}", type="secondary")
                    delete_clicked = col_d.button("Delete Client", key=f"delete_client_{idx}", type="primary")

                    if add_billing_clicked:
                        st.session_state["add_billing_client_idx"] = idx
                        st.session_state.pop("show_billing_client_idx", None)
                        st.rerun()
                    if show_billing_clicked:
                        st.session_state["show_billing_client_idx"] = idx
                        st.session_state.pop("add_billing_client_idx", None)
                        st.rerun()
                    if update_clicked:
                        st.session_state["editing_client_idx"] = idx
                        st.session_state.pop("add_billing_client_idx", None)
                        st.session_state.pop("show_billing_client_idx", None)
                        st.rerun()

                    if st.session_state.get("add_billing_client_idx") == idx:
                        st.markdown("#### Add Billing")
                        with st.form(f"add_billing_form_{idx}", clear_on_submit=True):
                            b_date = st.date_input("Date", value=datetime.date.today())
                            b_ee = st.text_input("EE")
                            b_activity = st.text_input("Activity")
                            b_description = st.text_area("Description")
                            b_rate = st.number_input("Rate", min_value=0.0, step=0.01)
                            b_hours = st.number_input("Hours", min_value=0.0, step=0.1)
                            line_total = b_rate * b_hours
                            st.write(f"**Line Total (Rate × Hours):** ${line_total:,.2f}")
                            c1, c2 = st.columns(2)
                            save_billing = c1.form_submit_button("Add Billing")
                            cancel_billing = c2.form_submit_button("Cancel")
                            if cancel_billing:
                                st.session_state.pop("add_billing_client_idx", None)
                                st.rerun()
                            if save_billing:
                                billings = _load_billings()
                                billings.append(
                                    {
                                        "id": _next_billing_id(billings),
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
                                st.session_state.pop("add_billing_client_idx", None)
                                st.success("Billing entry added.")
                                st.rerun()

                    if st.session_state.get("show_billing_client_idx") == idx:
                        _show_client_billing(idx, name, email, c)

                    if delete_clicked:
                        current = _load_clients()
                        if 0 <= idx < len(current):
                            current.pop(idx)
                            _save_clients(current)
                        st.success("Client deleted.")
                        st.rerun()

                    # Critical fix: persistent edit form state across reruns.
                    if st.session_state.get("editing_client_idx") == idx:
                        with st.form(f"update_client_form_{idx}", clear_on_submit=True):
                            new_name = st.text_input("Name", value=name)
                            new_email = st.text_input("Email", value=email)
                            new_phone = st.text_input("Phone", value=c.get("phone", ""))
                            new_address = st.text_area("Address", value=c.get("address", ""))
                            new_case_number = st.text_input("Case Number", value=c.get("case_number", ""))
                            new_case_link = st.text_input("Case Link", value=c.get("case_link", ""))
                            new_case_description = st.text_area(
                                "Case Description", value=c.get("case_description", "")
                            )
                            new_status = st.radio(
                                "Active status",
                                options=["active", "inactive"],
                                index=0 if str(status_val).lower() == "active" else 1,
                                horizontal=True,
                                key=f"update_status_{idx}",
                            )
                            s1, s2 = st.columns(2)
                            save_update = s1.form_submit_button("Save Changes")
                            cancel_update = s2.form_submit_button("Cancel")
                            if cancel_update:
                                st.session_state.pop("editing_client_idx", None)
                                st.rerun()
                            if save_update:
                                current = _load_clients()
                                if 0 <= idx < len(current):
                                    current[idx] = {
                                        "name": new_name.strip(),
                                        "email": new_email.strip(),
                                        "phone": new_phone.strip(),
                                        "address": new_address.strip(),
                                        "case_number": new_case_number.strip(),
                                        "case_link": new_case_link.strip(),
                                        "case_description": new_case_description.strip(),
                                        "status": new_status,
                                    }
                                    _save_clients(current)
                                st.session_state.pop("editing_client_idx", None)
                                st.success("Client updated.")
                                st.rerun()
    else:
        st.info("No clients yet. Click 'Add Client' to create one.")

    if st.button("Add Client"):
        st.session_state["show_add_client_form"] = True

    if st.session_state.get("show_add_client_form"):
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
                status = st.radio("Active status", options=["active", "inactive"], horizontal=True)
                c1, c2 = st.columns(2)
                submit = c1.form_submit_button("Add Client")
                cancel = c2.form_submit_button("Cancel")
                if cancel:
                    st.session_state["show_add_client_form"] = False
                if submit and name.strip():
                    clients = _load_clients()
                    clients.append(
                        {
                            "name": name.strip(),
                            "email": email.strip(),
                            "phone": phone.strip(),
                            "address": address.strip(),
                            "case_number": case_number.strip(),
                            "case_link": case_link.strip(),
                            "case_description": case_description.strip(),
                            "status": status,
                        }
                    )
                    _save_clients(clients)
                    st.session_state["show_add_client_form"] = False
                    st.success("Client added.")
                    st.rerun()
