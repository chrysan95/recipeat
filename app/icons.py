"""Inline SVG icon set (stroke icons, inherit currentColor)"""
from markupsafe import Markup, escape

PATHS = {
    "home": '<path d="M3.5 11.2 12 4l8.5 7.2"/><path d="M5.5 9.6V20h4.5v-4.5a2 2 0 0 1 4 0V20h4.5V9.6"/><path d="M16.5 6.6V4h2v4.3"/>',
    "pot": '<path d="M4.9 7.5h14.2a9 9 0 1 1-14.2 0z"/><path d="m7 20.4-1.7 1.9M17 20.4l1.7 1.9M15.5 7.5l4.7-4.8"/><circle cx="11" cy="3.2" r="1.1" fill="currentColor" stroke="none"/><circle cx="14.2" cy="4.8" r="1.3" fill="currentColor" stroke="none"/>',
    "book": '<rect x="5.5" y="3" width="14" height="18" rx="3"/><rect x="9.5" y="7" width="6" height="4" rx="1"/><path d="M3.5 7.5h3M3.5 12h3M3.5 16.5h3"/>',
    "bell": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4z"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "arrowLeft": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "arrowRight": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "chevronRight": '<path d="m9 6 6 6-6 6"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    "basket": '<path d="M3 10h18l-2 10H5z"/><path d="m8 10 4-6 4 6M9 14v3M12 14v3M15 14v3"/>',
    "minus": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12h8"/>',
    "plus": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12h8M12 8v8"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M4 22h16"/>',
    "expand": '<path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/>',
    "logout": '<path d="M14 4h5v16h-5"/><path d="M10 12H3M6 8l-4 4 4 4"/>',
    "grid": '<path d="M12 3 7 11h10z"/><rect x="3" y="14" width="7" height="7" rx="1"/><circle cx="17" cy="17" r="3.5"/><path d="m20 20 2 2"/>',
    "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "eyeOff": '<path d="M3 10c2.4 3 5.4 4.5 9 4.5s6.6-1.5 9-4.5"/><path d="m5.6 12.6-2 2.4M18.4 12.6l2 2.4M9.4 14.2 8.6 17M14.6 14.2l.8 2.8"/>',
    "message": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "chef": '<path d="M7 14a4 4 0 1 1 1-7.9 4 4 0 0 1 8 0A4 4 0 1 1 17 14v5H7z"/><path d="M7 17h10"/>',
    "megaphone": '<path d="M3 10v4h4l8 5V5L7 10z"/><path d="M18 9a4 4 0 0 1 0 6"/>',
    "warning": '<path d="M12 3 2 21h20z"/><path d="M12 10v5M12 18v.5"/>',
    "upload": '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v4h16v-4"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
}

# Solid glyphs (fill only) — used for the active navbar item. (viewBox, inner SVG)
SOLID = {
    "home": ("0 0 24 24", '<path d="M16.2 3.4h2.3a.5.5 0 0 1 .5.5v4.5l2.1 1.8a1 1 0 0 1-1.3 1.5l-.3-.2V20a1.5 1.5 0 0 1-1.5 1.5H14V16a2 2 0 0 0-4 0v5.5H5.9A1.5 1.5 0 0 1 4.4 20v-8.5l-.3.2a1 1 0 0 1-1.3-1.5l8.5-7.3a1 1 0 0 1 1.3 0l3.1 2.7V3.9a.5.5 0 0 1 .5-.5Z"/>'),
    "pot": ("0 0 40 40", '<path fill-rule="evenodd" clip-rule="evenodd" d="M18.3334 6.66659C18.7754 6.66659 19.1993 6.49099 19.5119 6.17843C19.8244 5.86587 20 5.44195 20 4.99992C20 4.55789 19.8244 4.13397 19.5119 3.82141C19.1993 3.50885 18.7754 3.33325 18.3334 3.33325C17.8913 3.33325 17.4674 3.50885 17.1549 3.82141C16.8423 4.13397 16.6667 4.55789 16.6667 4.99992C16.6667 5.44195 16.8423 5.86587 17.1549 6.17843C17.4674 6.49099 17.8913 6.66659 18.3334 6.66659ZM23.75 9.99992C24.3026 9.99992 24.8325 9.78043 25.2232 9.38972C25.6139 8.99902 25.8334 8.46912 25.8334 7.91659C25.8334 7.36405 25.6139 6.83415 25.2232 6.44345C24.8325 6.05275 24.3026 5.83325 23.75 5.83325C23.1975 5.83325 22.6676 6.05275 22.2769 6.44345C21.8862 6.83415 21.6667 7.36405 21.6667 7.91659C21.6667 8.46912 21.8862 8.99902 22.2769 9.38972C22.6676 9.78043 23.1975 9.99992 23.75 9.99992ZM32.25 13.0249C34.0423 15.5498 35.0035 18.5703 35 21.6666L34.9917 21.6749C34.9917 25.9999 33.1417 29.8833 30.2084 32.6249L32.9584 35.3749L31.1917 37.1416L28.2417 34.1916C25.7958 35.8128 22.9261 36.6766 19.9917 36.6749C16.9417 36.6749 14.1084 35.7583 11.7417 34.1916L8.7917 37.1416L7.02503 35.3749L9.77503 32.6249C6.8417 29.8833 4.9917 25.9999 4.9917 21.6749C4.9917 18.5666 5.9417 15.5749 7.7417 13.0333L8.1167 12.5083H10.825C10.825 11.4032 11.264 10.3434 12.0454 9.56197C12.8268 8.78057 13.8866 8.34159 14.9917 8.34159C16.0968 8.34159 17.1566 8.78057 17.938 9.56197C18.7194 10.3434 19.1584 11.4032 19.1584 12.5083H25.7917L33.6917 4.54159L35.4667 6.29992L29.3167 12.4999H31.875L32.25 13.0249ZM16.6667 12.4999C16.6667 11.5833 15.9167 10.8333 15 10.8333C14.0834 10.8333 13.3334 11.5833 13.3334 12.4999H16.6667Z"/>'),
    "book": ("0 0 24 24", '<path fill-rule="evenodd" d="M8.5 2.5h8A3.5 3.5 0 0 1 20 6v12a3.5 3.5 0 0 1-3.5 3.5h-8A3.5 3.5 0 0 1 5 18v-.7h-.8a1 1 0 1 1 0-2H5v-2.3h-.8a1 1 0 1 1 0-2H5V8.7h-.8a1 1 0 1 1 0-2H5V6a3.5 3.5 0 0 1 3.5-3.5Zm2 4a1 1 0 0 0-1 1v3.2a1 1 0 0 0 1 1h4.2a1 1 0 0 0 1-1V7.5a1 1 0 0 0-1-1Z"/>'),
    "bell": ("0 0 24 24", '<path d="M12 2.8a6.6 6.6 0 0 0-6.6 6.6v5.2l-1.7 2.2a1 1 0 0 0 .8 1.7h15a1 1 0 0 0 .8-1.7l-1.7-2.2V9.4A6.6 6.6 0 0 0 12 2.8Z"/><path d="M9.3 19.6h5.4a2.7 2.7 0 0 1-5.4 0Z"/>'),
}


def solid_icon(name, size=24, cls=""):
    view, inner = SOLID[name]
    return Markup(f'<svg class="icon {cls}" aria-hidden="true" width="{size}" height="{size}" viewBox="{view}" fill="currentColor">{inner}</svg>')


def icon(name, size=24, cls="", fill=False, label=None):
    p = PATHS.get(name)
    if not p:
        return Markup("")
    aria = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return Markup(
        f'<svg class="icon {cls}" {aria} width="{size}" height="{size}" viewBox="0 0 24 24" fill="{"currentColor" if fill else "none"}" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{p}</svg>'
    )
