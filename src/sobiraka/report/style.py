from rich.style import Style
from rich.text import Text

from sobiraka.models import Status

ICONS_AND_STYLES: dict[Status, tuple[str, Style]] = {
    Status.DISCOVER: (' ', Style(color='grey39')),
    Status.LOAD: ('>', Style(color='grey39')),
    Status.PARSE: ('▏', Style(color='grey66')),
    Status.PROCESS: ('P', Style(color='deep_sky_blue2')),
    Status.REFERENCE: ('R', Style(color='sky_blue1')),
    Status.NUMERATE: ('N', Style(color='chartreuse4')),
    Status.FINALIZE: ('V', Style(color='sea_green3', bold=True)),

    Status.SOURCE_FAILURE: ('X', Style(color='red1', bold=True)),
    Status.PAGE_FAILURE: ('X', Style(color='red1', bold=True)),
    Status.DEP_FAILURE: ('X', Style(color='orange4')),
    Status.VOL_FAILURE: ('X', Style(color='orange4')),
}


def make_report_icon(status: Status) -> Text:
    icon, style = ICONS_AND_STYLES[status]
    return Text(icon, style, end=' ')


def make_report_text(status: Status, text: str, end: str = '\n') -> Text:
    _, style = ICONS_AND_STYLES[status]
    return Text(text, style, end=end)
