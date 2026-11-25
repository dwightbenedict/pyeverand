# NiceGUI is only partially typed, so strict pyright cannot check calls into it.
# pyright: basic
# Layout only: what a row says and which settings are valid are decided elsewhere.

from collections.abc import Callable
from pathlib import Path

from nicegui import app, background_tasks, ui
from starlette.middleware.trustedhost import TrustedHostMiddleware

from pyeverand.errors import AppError, CredentialsRequiredError
from pyeverand.interfaces.gui_view import (
    COOKIE_COMMAND,
    COOKIE_STEPS,
    RowView,
    default_output_dir,
    describe_added,
    describe_item,
    describe_request,
)
from pyeverand.logging_config import configure_logging
from pyeverand.wiring import (
    get_app_options,
    get_choose_folder_service,
    get_download_queue,
    get_save_credentials_service,
    get_saved_credentials,
    get_settings,
)


APP_TITLE = "Everand Download"
LOCAL_HOST = "127.0.0.1"
REFRESH_SECONDS = 0.4
THEME = Path(__file__).with_name("gui_theme.css")
FONTS = Path(__file__).with_name("fonts")
PACKAGE = Path(__file__).parents[1]
# Outline icons from Lucide (ISC licence).
SETTINGS_ICON = (
    "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0"
    "-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 "
    "2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20"
    "a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 "
    "0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15"
    "-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0"
    " 1-1-1.73V4a2 2 0 0 0-2-2zM15 12a3 3 0 1 1-6 0 3 3 0 1 1 6 0"
)
REMOVE_ICON = "M18 6 6 18M6 6l12 12"
SHOW_ICON = (
    "M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1"
    "-19.88 0M15 12a3 3 0 1 1-6 0 3 3 0 1 1 6 0"
)
HIDE_ICON = (
    "M10.73 5.08a10.74 10.74 0 0 1 11.21 6.57 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-1.44 2.49"
    "M14.08 14.16a3 3 0 0 1-4.24-4.24M17.48 17.5a10.75 10.75 0 0 1-15.42-5.15 1 1 0 0 1 0-.7"
    " 10.75 10.75 0 0 1 4.45-5.14M2 2l20 20"
)


def _icon(path: str) -> None:
    ui.html(
        f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg>',
        sanitize=False,
        tag="span",
    ).classes("icon")


def _button(label: str, on_click: Callable[[], object], kind: str = "push") -> ui.element:
    with ui.element("button").classes(f"button {kind}").props("type=button") as button:
        ui.label(label)

    button.on("click", on_click)
    return button


def _field(label: str, control: ui.input | ui.textarea) -> None:
    control.props(f'borderless dense aria-label="{label}"').classes("field")


def _caption(text: str) -> None:
    ui.label(text).classes("caption")


def _message() -> ui.label:
    return ui.label().classes("message").props("role=status")


def _show_message(message: ui.label, text: str, *, is_error: bool) -> None:
    message.text = text
    message.classes(add="error" if is_error else "", remove="" if is_error else "error")


def _start_queue() -> None:
    background_tasks.create(get_download_queue().run())


def _circle(kind: str) -> ui.element:
    return ui.element("circle").classes(kind).props("cx=18 cy=18 r=16 pathLength=100")


async def _on_remove(item_id: int, message: ui.label) -> None:
    try:
        await get_download_queue().remove(item_id)

    except AppError as err:
        _show_message(message, str(err), is_error=True)


class _QueueRow:
    def __init__(self, item_id: int, message: ui.label) -> None:
        with ui.element("li").classes("queue-row") as self.root:
            with ui.element("div").classes("queue-row-text"):
                self._title = ui.label().classes("row-title")
                self._detail = ui.label().classes("row-detail")

            self._retry = _button("Try Again", lambda: self._on_retry(item_id))

            # One button for the whole life of the row, so keyboard focus stays on it.
            with ui.element("button").classes("row-action").props("type=button") as self._action:
                ring = ui.element("svg").classes("progress-ring")

                with ring.props('viewBox="0 0 36 36" aria-hidden=true'):
                    _circle("progress-track")
                    self._arc = _circle("progress-value")

                self._percent = ui.label().classes("progress-percent").props("aria-hidden=true")
                _icon(REMOVE_ICON)

            self._action.on("click", lambda: _on_remove(item_id, message))

    def _on_retry(self, item_id: int) -> None:
        get_download_queue().retry(item_id)
        _start_queue()

    def show(self, view: RowView) -> None:
        self._title.text = view.title
        self._detail.text = view.detail
        self.root.props(f"data-status={view.status}")
        self.root.props(f"data-progress={view.progress}")
        self._arc.props(f'stroke-dasharray="{view.percent} 100"')
        self._percent.text = f"{view.percent}%"
        # Set directly: a book title may hold quotes, which the props string syntax would break on.
        self._action.props["aria-label"] = view.action_label
        self._action.props["title"] = view.action_label
        self._action.update()
        self._retry.set_visibility(view.can_retry)


class _QueueList:
    def __init__(self, message: ui.label) -> None:
        self._message = message
        self._empty = ui.label("No downloads yet.").classes("empty")
        self._list = ui.element("ul").classes("group queue").props('aria-label="Downloads"')
        self._rows: dict[int, _QueueRow] = {}

    def refresh(self) -> None:
        items = get_download_queue().items()

        for item_id in self._rows.keys() - {item.item_id for item in items}:
            self._rows.pop(item_id).root.delete()

        for item in items:
            if item.item_id not in self._rows:
                with self._list:
                    self._rows[item.item_id] = _QueueRow(item.item_id, self._message)

            self._rows[item.item_id].show(describe_item(item))

        self._empty.set_visibility(not items)
        self._list.set_visibility(bool(items))


def _on_add(books: ui.textarea, folder: ui.input, message: ui.label, sheet: ui.dialog) -> None:
    try:
        count = get_download_queue().add(books.value or "", folder.value or "")

    except CredentialsRequiredError:
        sheet.open()

    except AppError as err:
        _show_message(message, str(err), is_error=True)

    else:
        books.value = ""
        _show_message(message, describe_added(count), is_error=False)
        _start_queue()


def _check_input(
    books: ui.textarea, folder: ui.input, button: ui.element, message: ui.label
) -> None:
    view = describe_request(books.value or "", folder.value or "")
    _show_message(message, view.hint, is_error=bool(view.hint))

    if view.can_download:
        button.props(remove="disabled")
    else:
        button.props("disabled")


async def _on_choose_folder(folder: ui.input, message: ui.label) -> None:
    try:
        folder.value = await get_choose_folder_service().choose_folder(folder.value or "")

    except AppError as err:
        _show_message(message, str(err), is_error=True)


def _folder_picker() -> tuple[ui.input, ui.element]:
    with ui.element("div").classes("folder-picker"):
        folder = ui.input(value=default_output_dir()).props("readonly")
        _field("Save to folder", folder)
        choose = _button("Choose…", lambda: None)

    return folder, choose


def _downloads_panel(sheet: ui.dialog) -> None:
    with ui.element("div").classes("form"):
        _caption("Book links or IDs, one per line")
        books = ui.textarea(placeholder="https://www.everand.com/book/…")
        _field("Book links or IDs", books)
        _caption("Save to folder")
        folder, choose = _folder_picker()

        with ui.element("div").classes("actions"):
            message = _message()
            choose.on("click", lambda: _on_choose_folder(folder, message))
            download = _button(
                "Download", lambda: _on_add(books, folder, message, sheet), "push default"
            )

    for field in (books, folder):
        field.on_value_change(lambda: _check_input(books, folder, download, message))

    _check_input(books, folder, download, message)

    queue_list = _QueueList(message)
    queue_list.refresh()
    ui.timer(REFRESH_SECONDS, queue_list.refresh)


async def _on_save(token: ui.input, user_id: ui.input, message: ui.label, sheet: ui.dialog) -> None:
    try:
        await get_save_credentials_service().save_credentials(
            token.value or "", user_id.value or ""
        )
        get_settings()

    except AppError as err:
        _show_message(message, str(err), is_error=True)

    else:
        sheet.close()


class _SecretField:
    """A text field that is masked until its eye button is pressed."""

    def __init__(self, label: str) -> None:
        _caption(label)

        with ui.element("div").classes("secret-field"):
            self.input = ui.input().props("autocomplete=off spellcheck=false")
            _field(label, self.input)

            with ui.element("button").classes("icon-button reveal") as self._toggle:
                _icon(SHOW_ICON)
                _icon(HIDE_ICON)

        self._toggle.props(f'type=button aria-label="Show {label}" title="Show {label}"')
        self._toggle.on("click", self._flip)
        self._mask()

    def fill(self, value: str) -> None:
        self.input.value = value
        self._mask()

    def _flip(self) -> None:
        if self._is_masked:
            self._reveal()
        else:
            self._mask()

    def _mask(self) -> None:
        self._is_masked = True
        self.input.props("type=password")
        self._toggle.props("aria-pressed=false")

    def _reveal(self) -> None:
        self._is_masked = False
        self.input.props("type=text")
        self._toggle.props("aria-pressed=true")


def _fill_cookies(token: _SecretField, user_id: _SecretField) -> None:
    saved = get_saved_credentials()
    token.fill(saved.session_token)
    user_id.fill(saved.user_id)


def _clear(message: ui.label, *fields: _SecretField) -> None:
    _show_message(message, "", is_error=False)

    for field in fields:
        field.fill("")


def _on_copy_command(message: ui.label) -> None:
    ui.clipboard.write(COOKIE_COMMAND)
    _show_message(message, "Command copied.", is_error=False)


def _cookie_help(placement: str = "") -> None:
    """Add the steps as a popover of the enclosing button, which then opens and closes it."""
    menu = ui.menu().classes("popover").props('role=dialog aria-label="How to find your cookies"')

    with menu.props(placement), ui.element("div").classes("popover-body form"):
        with ui.element("ol").classes("steps"):
            for step in COOKIE_STEPS:
                with ui.element("li"):
                    ui.label(step)

        with ui.element("div").classes("actions"):
            message = _message()
            _button("Copy Command", lambda: _on_copy_command(message))


def _help_button() -> None:
    with ui.element("button").classes("help-button") as button:
        ui.label("?").props("aria-hidden=true")
        # The button is at the sheet's right edge, so the popover grows leftwards from it.
        _cookie_help('anchor="bottom right" self="top right"')

    button.props('type=button aria-label="How to find your cookies"')


def _settings_sheet() -> ui.dialog:
    with (
        ui.dialog().props('aria-label="Settings"') as sheet,
        ui.element("div").classes("sheet form"),
    ):
        with ui.element("div").classes("sheet-header"):
            ui.label("Settings").classes("sheet-title").props("role=heading aria-level=2")
            _help_button()

        ui.label("Cookies from your signed-in Everand account.").classes("help")
        token = _SecretField("_scribd_session cookie")
        user_id = _SecretField("_scribd_user_id cookie")

        # Touch layouts show this link, macOS the "?" button: see the stylesheet.
        with _button("How to Find Your Cookies", lambda: None, "help-link"):
            _cookie_help()

        with ui.element("div").classes("actions"):
            message = _message()
            _button("Cancel", sheet.close)
            _button(
                "Save Cookies",
                lambda: _on_save(token.input, user_id.input, message, sheet),
                "push default",
            )

    sheet.on("before-show", lambda: _fill_cookies(token, user_id))
    # The cookies must not stay in the page, however the sheet is dismissed.
    # Not "hide": Quasar skips it when the sheet is reopened before its closing animation ends.
    sheet.on("before-hide", lambda: _clear(message, token, user_id))
    return sheet


@ui.page("/")
def index() -> None:
    sheet = _settings_sheet()

    with ui.element("div").classes("window"):
        with ui.element("header").classes("toolbar"):
            ui.label(APP_TITLE).classes("toolbar-title").props("role=heading aria-level=1")

            with ui.element("button").classes("icon-button") as settings:
                _icon(SETTINGS_ICON)

            settings.props('type=button aria-label="Settings" title="Settings"')
            settings.on("click", sheet.open)

        with ui.element("main").classes("content"):
            _downloads_panel(sheet)


def run() -> None:
    options = get_app_options()
    configure_logging(options)
    ui.add_css(THEME, shared=True)
    app.add_static_files("/fonts", FONTS)
    # The server is only for this computer. Checking the Host header also stops other web sites
    # from reaching it by pointing their own domain at 127.0.0.1 (DNS rebinding).
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[LOCAL_HOST, "localhost"])
    ui.run(
        title=APP_TITLE,
        host=LOCAL_HOST,
        port=options.gui_port,
        dark=None,
        reload=options.gui_reload,
        # The whole package, not only this folder: the services behind the page change too.
        uvicorn_reload_dirs=str(PACKAGE),
        uvicorn_reload_includes="*.py,*.css",
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    run()
