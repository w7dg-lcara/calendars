#!/usr/bin/env python3
"""Format event list from iCal (ics / vcard) file."""
import argparse
from pathlib import Path
import typing as t

import datetime
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event


DEFAULT_CALENDAR_FILE = Path(__file__).parent.parent / "2023_cowlitz_ham.ics"


def format_time(t: datetime.datetime | datetime.time) -> str:
    return t.strftime("%H:%M")


def format_timespan(start: datetime.datetime, end: datetime.datetime) -> str:
    return f"({format_time(start)} - {format_time(end)})"


def format_date(d: datetime.datetime | datetime.date) -> str:
    return d.strftime("%m/%d")


def format_date_range(
    start: datetime.datetime | datetime.date,
    end: datetime.datetime | datetime.date | None,
) -> str:
    start_date = start.date() if isinstance(start, datetime.datetime) else start
    start_date_fmt = format_date(start_date)
    end_date = end.date() if isinstance(end, datetime.datetime) else end
    if end_date and end_date - start_date > datetime.timedelta(days=1):
        # multi-day "all day" event
        return f"{start_date_fmt} - {format_date(end_date)}"
    return start_date_fmt


def text_event_formatter(event: Event) -> str:
    event_start = event.dtstart
    event_end = event.dtend
    parts = [
        format_date_range(event_start, event_end) + ":",
        event.summary,
    ]
    if isinstance(event_start, datetime.datetime) and isinstance(
        event_end,
        datetime.datetime,
    ):
        # if the start or end are datetime objects, then the event is not all-day
        parts.append(format_timespan(event_start, event_end))
    return " ".join(parts)


def text_event_formatter_w_location(event: Event) -> str:
    event_fmt = text_event_formatter(event)
    if event.location:
        return event_fmt + f"\n    Location: {event.location}"
    return event_fmt


def format_upcoming_events(
    filename: str | Path,
    delta: datetime.timedelta,
    event_formatter: t.Callable[[Event], str] = text_event_formatter,
) -> list[str]:
    event_strings: list[str] = []
    for cal in calendars_from_file(filename):
        event_strings.extend(
            event_formatter(event) for event in events_thru(cal, delta)
        )
    return event_strings


def calendars_from_file(filename: str | Path) -> t.Generator[Calendar, None, None]:
    for calendar in IcsCalendarStream.from_ics((Path(filename).read_text())).calendars:
        yield calendar


def events_thru(
    cal: Calendar,
    delta: datetime.timedelta,
) -> t.Generator[Event, None, None]:
    start_interval = datetime.datetime.now()
    end_interval = start_interval + delta

    yield from cal.timeline.included(start=start_interval, end=end_interval)


def main():
    parser = argparse.ArgumentParser("evlist")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="include additional information for each event",
    )
    parser.add_argument(
        "--days",
        default=45,
        help="enumerate events this many days into the future (default: 45)",
    )
    parser.add_argument(
        "--calendar",
        default=None,
        help="path to .ics file (default: ../2023_cowlitz_ham.ics",
    )
    args = parser.parse_args()
    print(
        "\n".join(
            format_upcoming_events(
                filename=args.calendar or DEFAULT_CALENDAR_FILE,
                delta=datetime.timedelta(days=int(args.days)),
                event_formatter=(
                    text_event_formatter_w_location
                    if args.verbose
                    else text_event_formatter
                ),
            ),
        ),
    )


if __name__ == "__main__":
    main()
