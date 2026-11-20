"""Debug logging that shows up in the Driver Station console (and on stdout)."""

import hal


def log(message: str) -> None:
    print(message, flush=True)
    hal.send_console_line(message)
