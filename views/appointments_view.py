import flet as ft
import logging
from models.appointment import Appointment

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
logger = logging.getLogger("appointments_view")


async def _launch_url(url):
    await ft.UrlLauncher().launch_url(url)


def _build_appointment_card(apt: Appointment, page: ft.Page, on_archive=None, on_edit=None, on_toggle_status=None, url_launcher=None):
    async def _open_url(_):
        url = apt.url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        logger.info("_open_url clicked, url=%s", url)
        try:
            await url_launcher.launch_url(
                url,
                mode=ft.LaunchMode.EXTERNAL_APPLICATION,
                web_only_window_name="_blank",
            )
            logger.info("_open_url launch_url OK")
        except Exception as e:
            logger.error("_open_url error: %s", e)

    url_chip = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.LINK, size=16), ft.Text("Open house listing", size=13)],
            spacing=4,
        ),
        padding=ft.Padding(left=10, right=10, top=6, bottom=6),
        border_radius=20,
        bgcolor=ft.Colors.BLUE_GREY_50,
        on_click=_open_url,
        ink=True,
    )

    is_done = apt.status == "done"
    status_chip = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.CHECK_CIRCLE if is_done else ft.Icons.PENDING, size=14),
             ft.Text("Done" if is_done else "Pending", size=12)],
            spacing=4,
        ),
        padding=ft.Padding(left=8, right=8, top=4, bottom=4),
        border_radius=12,
        bgcolor=ft.Colors.GREEN_50 if is_done else ft.Colors.ORANGE_50,
    )

    action_buttons = []
    if on_toggle_status:
        if is_done:
            action_buttons.append(
                ft.TextButton("Mark Pending", icon=ft.Icons.UNDO_OUTLINED,
                              on_click=lambda _: on_toggle_status(apt.id, "pending"))
            )
        else:
            action_buttons.append(
                ft.TextButton("Mark Done", icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                              on_click=lambda _: on_toggle_status(apt.id, "done"))
            )
    if on_edit:
        action_buttons.append(
            ft.TextButton("Edit", icon=ft.Icons.EDIT_OUTLINED, on_click=lambda _: on_edit(apt))
        )
    if on_archive:
        action_buttons.append(
            ft.TextButton("Archive", icon=ft.Icons.ARCHIVE_OUTLINED, on_click=lambda _: on_archive(apt.id))
        )

    return ft.Card(
        elevation=2,
        content=ft.Container(
            padding=16,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        [ft.Icon(ft.Icons.HOME, color=ft.Colors.BLUE_400),
                         ft.Text(f"{apt.day} · {apt.time} · {apt.city}",
                                 size=16, weight=ft.FontWeight.BOLD),
                         status_chip],
                        spacing=8,
                    ),
                    ft.Text(apt.description, size=14, selectable=True) if apt.description else ft.Container(),
                    ft.Row([url_chip]),
                    ft.Row(action_buttons, alignment=ft.MainAxisAlignment.END) if action_buttons else ft.Container(),
                ],
            ),
        ),
    )


def _build_form_fields():
    day_dropdown = ft.Dropdown(
        label="Day of week",
        options=[ft.dropdown.Option(d) for d in DAYS],
        width=200,
    )
    time_field = ft.TextField(label="Time (e.g. 14:30)", width=200)
    city_field = ft.TextField(label="City", width=200)
    url_field = ft.TextField(label="House URL", width=400)
    description_field = ft.TextField(label="Description", multiline=True, min_lines=2, max_lines=4, width=400)
    return day_dropdown, time_field, city_field, url_field, description_field


def _build_add_dialog(vm, page: ft.Page):
    day_dropdown, time_field, city_field, url_field, description_field = _build_form_fields()

    def _save(e):
        if not day_dropdown.value or not time_field.value or not city_field.value or not url_field.value:
            snack = ft.SnackBar(ft.Text("Please fill all fields except description"))
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        vm.add(
            day=day_dropdown.value,
            time=time_field.value.strip(),
            city=city_field.value.strip(),
            url=url_field.value.strip(),
            description=description_field.value.strip() if description_field.value else "",
        )
        add_dialog.open = False
        page.update()

    def _cancel(e):
        add_dialog.open = False
        page.update()

    add_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add Appointment"),
        content=ft.Column(
            [
                ft.Row([day_dropdown, time_field]),
                city_field,
                url_field,
                description_field,
            ],
            tight=True,
            spacing=12,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=_cancel),
            ft.Button("Save", on_click=_save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return add_dialog


def _build_edit_dialog(vm, page: ft.Page):
    day_dropdown, time_field, city_field, url_field, description_field = _build_form_fields()
    status_dropdown = ft.Dropdown(
        label="Status",
        options=[ft.dropdown.Option("pending"), ft.dropdown.Option("done")],
        width=200,
    )
    editing_id = [None]

    def _open(apt: Appointment):
        editing_id[0] = apt.id
        day_dropdown.value = apt.day
        time_field.value = apt.time
        city_field.value = apt.city
        url_field.value = apt.url
        description_field.value = apt.description
        status_dropdown.value = apt.status
        edit_dialog.open = True
        page.update()

    def _save(e):
        if not day_dropdown.value or not time_field.value or not city_field.value or not url_field.value:
            snack = ft.SnackBar(ft.Text("Please fill all fields except description"))
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        vm.update(
            appointment_id=editing_id[0],
            day=day_dropdown.value,
            time=time_field.value.strip(),
            city=city_field.value.strip(),
            url=url_field.value.strip(),
            description=description_field.value.strip() if description_field.value else "",
        )
        if status_dropdown.value:
            vm.set_status(editing_id[0], status_dropdown.value)
        edit_dialog.open = False
        page.update()

    def _cancel(e):
        edit_dialog.open = False
        page.update()

    edit_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit Appointment"),
        content=ft.Column(
            [
                ft.Row([day_dropdown, time_field]),
                city_field,
                url_field,
                description_field,
                status_dropdown,
            ],
            tight=True,
            spacing=12,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=_cancel),
            ft.Button("Update", on_click=_save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return edit_dialog, _open


def create_appointments_view(vm, page: ft.Page, url_launcher=None):
    add_dialog = _build_add_dialog(vm, page)
    edit_dialog, open_edit = _build_edit_dialog(vm, page)

    day_filter = ft.Dropdown(
        label="Filter by day",
        options=[ft.dropdown.Option(d) for d in DAYS],
        value=None,
        width=180,
        on_select=lambda e: vm.set_filter_day(e.control.value if e.control.value else None),
    )

    city_filter = ft.Dropdown(
        label="Filter by city",
        options=[],
        value=None,
        width=180,
        on_select=lambda e: vm.set_filter_city(e.control.value if e.control.value else ""),
    )

    clear_btn = ft.TextButton(
        "Clear filters",
        on_click=lambda _: (
            setattr(day_filter, "value", None),
            setattr(city_filter, "value", None),
            vm.clear_filters(),
        ),
    )

    filter_row = ft.Row([day_filter, city_filter, clear_btn], spacing=10)

    list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    empty_text = ft.Text("No appointments yet. Tap + to add one.", size=14, color=ft.Colors.GREY_500)

    def _render():
        appointments = vm.appointments
        logger.info("_render() -> %d appointments, list_column has %d controls before clear",
                    len(appointments), len(list_column.controls))

        city_filter.options = [ft.dropdown.Option(c) for c in vm.cities]

        list_column.controls.clear()
        if not appointments:
            list_column.controls.append(empty_text)
        else:
            for apt in appointments:
                list_column.controls.append(
                    _build_appointment_card(apt, page, on_archive=vm.archive, on_edit=open_edit, on_toggle_status=vm.set_status, url_launcher=url_launcher)
                )
        logger.info("_render() done -> list_column now has %d controls", len(list_column.controls))

    def _on_change():
        logger.info("_on_change() called")
        _render()
        try:
            page.update()
        except Exception as e:
            logger.warning("_on_change() page.update() error: %s", e)

    vm.add_listener(_on_change)
    _render()

    fab = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: (
            setattr(add_dialog, "open", True),
            page.update(),
        ),
    )

    content = ft.Column(
        [
            ft.Container(
                content=filter_row,
                padding=ft.Padding(left=16, right=16, top=10, bottom=4),
            ),
            ft.Container(
                content=list_column,
                padding=ft.Padding(left=16, right=16, top=0, bottom=0),
                expand=True,
            ),
        ],
        expand=True,
    )

    return content, fab, add_dialog, edit_dialog
