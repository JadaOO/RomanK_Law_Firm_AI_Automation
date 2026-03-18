import calendar
import json
from pathlib import Path
import datetime

import streamlit as st

# Persist to project_root/db/calendar (as .json)
DB_DIR = Path(__file__).resolve().parent.parent / "db"
CALENDAR_FILE = DB_DIR / "calendar.json"


def _load_events():
    """Load events from db/calendar.json. Returns dict date_str -> list of events."""
    if not CALENDAR_FILE.exists():
        return {}
    try:
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_events(events):
    """Save events dict to db/calendar.json."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)


def show_calendar():
    """Calendar with date picker; add event_name, event_time, event_location per date; save to db/calendar."""
    today = datetime.date.today()

    st.subheader(f"Today is {today}, {today.strftime('%A')}")
    selected_date = st.date_input(
        "Check your events for this date",
        value=today,
        key="beautiful_day_calendar",
    )
    date_str = selected_date.isoformat()

    events_by_date = _load_events()
    day_events = events_by_date.get(date_str, [])

    st.subheader(f"Events on {selected_date}")

    if not day_events:
        st.info("No events for this date.")
    else:
        for i, ev in enumerate(day_events):
            with st.expander(f"{ev.get('event_name', 'Event')} — {ev.get('event_time', '')}"):
                st.write(f"**Location:** {ev.get('event_location', '')}")
                if st.button("Remove", key=f"del_{date_str}_{i}"):
                    events_by_date[date_str].pop(i)
                    if not events_by_date[date_str]:
                        del events_by_date[date_str]
                    _save_events(events_by_date)
                    st.rerun()

    # Add Event button; form only visible after click
    if "homepage_calendar_show_form" not in st.session_state:
        st.session_state["homepage_calendar_show_form"] = False

    if st.button("Add Event", key="add_event_btn"):
        st.session_state["homepage_calendar_show_form"] = True
        st.rerun()

    if st.session_state["homepage_calendar_show_form"]:
        with st.form("add_calendar_event", clear_on_submit=True):
            event_name = st.text_input("Event name")
            event_time = st.text_input("Event time")
            event_location = st.text_input("Event location")
            col1, col2, _ = st.columns(3)
            with col1:
                submitted = st.form_submit_button("Save")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if cancel:
                st.session_state["homepage_calendar_show_form"] = False
                st.rerun()
            if submitted and event_name.strip():
                new_event = {
                    "event_name": event_name.strip(),
                    "event_time": event_time.strip(),
                    "event_location": event_location.strip(),
                }
                events_by_date = _load_events()
                if date_str not in events_by_date:
                    events_by_date[date_str] = []
                events_by_date[date_str].append(new_event)
                _save_events(events_by_date)
                st.session_state["homepage_calendar_show_form"] = False
                st.success("Event added.")
                st.rerun()
