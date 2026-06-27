import flet as ft
import httpx
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("mobile")

API_URL = "https://your-app.onrender.com"  # Change to your Render API URL

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class Appointment:
    id: int | None
    day: str
    time: str
    city: str
    url: str
    description: str
    archived: bool = False
    status: str = "pending"
    created_at: str | None = None


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_active(self) -> list[Appointment]:
        r = httpx.get(f"{self.base_url}/api/appointments", timeout=30)
        r.raise_for_status()
        return [Appointment(**a) for a in r.json()]

    def get_archived(self) -> list[Appointment]:
        r = httpx.get(f"{self.base_url}/api/appointments/archived", timeout=30)
        r.raise_for_status()
        return [Appointment(**a) for a in r.json()]

    def add(self, day, time, city, url, description):
        httpx.post(f"{self.base_url}/api/appointments", json={
            "day": day, "time": time, "city": city, "url": url, "description": description
        }, timeout=30)

    def update(self, apt_id, day, time, city, url, description, status):
        httpx.put(f"{self.base_url}/api/appointments/{apt_id}", json={
            "day": day, "time": time, "city": city, "url": url, "description": description, "status": status
        }, timeout=30)

    def set_status(self, apt_id, status):
        httpx.put(f"{self.base_url}/api/appointments/{apt_id}/status", json={"status": status}, timeout=30)

    def archive(self, apt_id):
        httpx.put(f"{self.base_url}/api/appointments/{apt_id}/archive", timeout=30)

    def unarchive(self, apt_id):
        httpx.put(f"{self.base_url}/api/appointments/{apt_id}/unarchive", timeout=30)

    def delete(self, apt_id):
        httpx.delete(f"{self.base_url}/api/appointments/{apt_id}", timeout=30)


class BaseViewModel:
    def __init__(self):
        self._listeners = []

    def add_listener(self, fn):
        self._listeners.append(fn)

    def notify_change(self):
        for fn in self._listeners:
            fn()


class AppointmentsViewModel(BaseViewModel):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._appointments: list[Appointment] = []
        self._filter_day: str | None = None
        self._filter_city: str = ""
        self.load()

    @property
    def appointments(self):
        filtered = self._appointments
        if self._filter_day:
            filtered = [a for a in filtered if a.day.lower() == self._filter_day.lower()]
        if self._filter_city:
            filtered = [a for a in filtered if self._filter_city.lower() in a.city.lower()]
        return filtered

    @property
    def cities(self):
        seen = []
        for a in self._appointments:
            if a.city not in seen:
                seen.append(a.city)
        return sorted(seen)

    def load(self):
        try:
            self._appointments = self.api.get_active()
        except Exception as e:
            logger.error("load error: %s", e)
            self._appointments = []
        self.notify_change()

    def add(self, day, time, city, url, description):
        self.api.add(day, time, city, url, description)
        self.load()

    def update(self, apt_id, day, time, city, url, description, status="pending"):
        self.api.update(apt_id, day, time, city, url, description, status)
        self.load()

    def archive(self, apt_id):
        self.api.archive(apt_id)
        self.load()

    def set_status(self, apt_id, status):
        self.api.set_status(apt_id, status)
        self.load()

    def set_filter_day(self, day):
        self._filter_day = day
        self.notify_change()

    def set_filter_city(self, city):
        self._filter_city = city
        self.notify_change()

    def clear_filters(self):
        self._filter_day = None
        self._filter_city = ""
        self.notify_change()


class ArchiveViewModel(BaseViewModel):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self._appointments: list[Appointment] = []
        self.load()

    @property
    def appointments(self):
        return self._appointments

    def load(self):
        try:
            self._appointments = self.api.get_archived()
        except Exception as e:
            logger.error("load error: %s", e)
            self._appointments = []
        self.notify_change()

    def delete(self, apt_id):
        self.api.delete(apt_id)
        self.load()

    def recover(self, apt_id):
        self.api.unarchive(apt_id)
        self.load()


def _build_appointment_card(apt: Appointment, page: ft.Page, on_archive=None, on_edit=None, on_toggle_status=None, url_launcher=None):
    async def _open_url(_):
        url = apt.url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            await url_launcher.launch_url(url, mode=ft.LaunchMode.EXTERNAL_APPLICATION)
        except Exception as e:
            logger.error("open_url error: %s", e)

    url_chip = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LINK, size=16), ft.Text("Open listing", size=13)], spacing=4),
        padding=ft.Padding(left=10, right=10, top=6, bottom=6),
        border_radius=20, bgcolor=ft.Colors.BLUE_GREY_50, on_click=_open_url, ink=True,
    )

    is_done = apt.status == "done"
    status_chip = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if is_done else ft.Icons.PENDING, size=14),
                        ft.Text("Done" if is_done else "Pending", size=12)], spacing=4),
        padding=ft.Padding(left=8, right=8, top=4, bottom=4),
        border_radius=12, bgcolor=ft.Colors.GREEN_50 if is_done else ft.Colors.ORANGE_50,
    )

    action_buttons = []
    if on_toggle_status:
        if is_done:
            action_buttons.append(ft.TextButton("Pending", icon=ft.Icons.UNDO_OUTLINED,
                on_click=lambda _: on_toggle_status(apt.id, "pending")))
        else:
            action_buttons.append(ft.TextButton("Done", icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                on_click=lambda _: on_toggle_status(apt.id, "done")))
    if on_edit:
        action_buttons.append(ft.TextButton("Edit", icon=ft.Icons.EDIT_OUTLINED, on_click=lambda _: on_edit(apt)))
    if on_archive:
        action_buttons.append(ft.TextButton("Archive", icon=ft.Icons.ARCHIVE_OUTLINED, on_click=lambda _: on_archive(apt.id)))

    return ft.Card(elevation=2, content=ft.Container(padding=16, content=ft.Column(spacing=8, controls=[
        ft.Row([ft.Icon(ft.Icons.HOME, color=ft.Colors.BLUE_400),
                ft.Text(f"{apt.day} · {apt.time} · {apt.city}", size=16, weight=ft.FontWeight.BOLD),
                status_chip], spacing=8),
        ft.Text(apt.description, size=14, selectable=True) if apt.description else ft.Container(),
        ft.Row([url_chip]),
        ft.Row(action_buttons, alignment=ft.MainAxisAlignment.END) if action_buttons else ft.Container(),
    ])))


def _build_archived_card(apt: Appointment, page: ft.Page, on_delete=None, on_recover=None, url_launcher=None):
    async def _open_url(_):
        url = apt.url
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            await url_launcher.launch_url(url, mode=ft.LaunchMode.EXTERNAL_APPLICATION)
        except Exception as e:
            logger.error("open_url error: %s", e)

    url_chip = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.LINK, size=16), ft.Text("Open listing", size=13)], spacing=4),
        padding=ft.Padding(left=10, right=10, top=6, bottom=6),
        border_radius=20, bgcolor=ft.Colors.BLUE_GREY_50, on_click=_open_url, ink=True,
    )

    return ft.Card(elevation=1, content=ft.Container(padding=16, content=ft.Column(spacing=8, controls=[
        ft.Row([ft.Icon(ft.Icons.HOME, color=ft.Colors.GREY_400),
                ft.Text(f"{apt.day} · {apt.time} · {apt.city}", size=16, weight=ft.FontWeight.BOLD)], spacing=8),
        ft.Text(apt.description, size=14, selectable=True) if apt.description else ft.Container(),
        ft.Row([url_chip]),
        ft.Row([
            ft.TextButton("Recover", icon=ft.Icons.RESTORE_OUTLINED, on_click=lambda _: on_recover(apt.id)),
            ft.TextButton("Delete", icon=ft.Icons.DELETE_OUTLINE, on_click=lambda _: on_delete(apt.id)),
        ], alignment=ft.MainAxisAlignment.END),
    ])))


def _build_form_fields():
    day_dropdown = ft.Dropdown(label="Day", options=[ft.dropdown.Option(d) for d in DAYS], width=200)
    time_field = ft.TextField(label="Time (14:30)", width=200)
    city_field = ft.TextField(label="City", width=200)
    url_field = ft.TextField(label="URL", width=400)
    description_field = ft.TextField(label="Description", multiline=True, min_lines=2, max_lines=4, width=400)
    return day_dropdown, time_field, city_field, url_field, description_field


async def main(page: ft.Page):
    page.title = "House Tracker"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.theme_mode = ft.ThemeMode.LIGHT

    api = ApiClient(API_URL)
    url_launcher = ft.UrlLauncher()

    apt_vm = AppointmentsViewModel(api)
    arch_vm = ArchiveViewModel(api)

    # --- Appointments tab ---
    day_dd, time_f, city_f, url_f, desc_f = _build_form_fields()

    def _save_add(e):
        if not day_dd.value or not time_f.value or not city_f.value or not url_f.value:
            snack = ft.SnackBar(ft.Text("Fill all fields except description"))
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        apt_vm.add(day_dd.value, time_f.value.strip(), city_f.value.strip(), url_f.value.strip(),
                    desc_f.value.strip() if desc_f.value else "")
        add_dialog.open = False
        page.update()

    add_dialog = ft.AlertDialog(modal=True, title=ft.Text("Add Appointment"),
        content=ft.Column([ft.Row([day_dd, time_f]), city_f, url_f, desc_f], tight=True, spacing=12),
        actions=[ft.TextButton("Cancel", on_click=lambda e: setattr(add_dialog, "open", False) or page.update()),
                 ft.Button("Save", on_click=_save_add)], actions_alignment=ft.MainAxisAlignment.END)

    # Edit dialog
    ed_day, ed_time, ed_city, ed_url, ed_desc = _build_form_fields()
    ed_status = ft.Dropdown(label="Status", options=[ft.dropdown.Option("pending"), ft.dropdown.Option("done")], width=200)
    editing_id = [None]

    def open_edit(apt: Appointment):
        editing_id[0] = apt.id
        ed_day.value = apt.day
        ed_time.value = apt.time
        ed_city.value = apt.city
        ed_url.value = apt.url
        ed_desc.value = apt.description
        ed_status.value = apt.status
        edit_dialog.open = True
        page.update()

    def _save_edit(e):
        if not ed_day.value or not ed_time.value or not ed_city.value or not ed_url.value:
            return
        apt_vm.update(editing_id[0], ed_day.value, ed_time.value.strip(), ed_city.value.strip(),
                       ed_url.value.strip(), ed_desc.value.strip() if ed_desc.value else "",
                       ed_status.value or "pending")
        edit_dialog.open = False
        page.update()

    edit_dialog = ft.AlertDialog(modal=True, title=ft.Text("Edit Appointment"),
        content=ft.Column([ft.Row([ed_day, ed_time]), ed_city, ed_url, ed_desc, ed_status], tight=True, spacing=12),
        actions=[ft.TextButton("Cancel", on_click=lambda e: setattr(edit_dialog, "open", False) or page.update()),
                 ft.Button("Update", on_click=_save_edit)], actions_alignment=ft.MainAxisAlignment.END)

    page.overlay.append(add_dialog)
    page.overlay.append(edit_dialog)

    day_filter = ft.Dropdown(label="Filter day", options=[ft.dropdown.Option(d) for d in DAYS], value=None, width=150,
        on_select=lambda e: apt_vm.set_filter_day(e.control.value if e.control.value else None))
    city_filter = ft.Dropdown(label="Filter city", options=[], value=None, width=150,
        on_select=lambda e: apt_vm.set_filter_city(e.control.value if e.control.value else ""))

    apt_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    apt_empty = ft.Text("No appointments. Tap + to add.", size=14, color=ft.Colors.GREY_500)

    def _render_apt():
        appointments = apt_vm.appointments
        city_filter.options = [ft.dropdown.Option(c) for c in apt_vm.cities]
        apt_list.controls.clear()
        if not appointments:
            apt_list.controls.append(apt_empty)
        else:
            for apt in appointments:
                apt_list.controls.append(
                    _build_appointment_card(apt, page, on_archive=apt_vm.archive, on_edit=open_edit,
                                            on_toggle_status=apt_vm.set_status, url_launcher=url_launcher))
        page.update()

    apt_vm.add_listener(_render_apt)
    _render_apt()

    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda _: setattr(add_dialog, "open", True) or page.update())

    apt_view = ft.Column([
        ft.Container(content=ft.Row([day_filter, city_filter, ft.TextButton("Clear", on_click=lambda _: (
            setattr(day_filter, "value", None), setattr(city_filter, "value", None), apt_vm.clear_filters()))]),
            padding=ft.Padding(left=16, right=16, top=10, bottom=4)),
        ft.Container(content=apt_list, padding=ft.Padding(left=16, right=16, top=0, bottom=0), expand=True),
    ], expand=True)

    # --- Archive tab ---
    arch_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    arch_empty = ft.Text("Archive is empty.", size=14, color=ft.Colors.GREY_500)

    def _render_arch():
        appointments = arch_vm.appointments
        arch_list.controls.clear()
        if not appointments:
            arch_list.controls.append(arch_empty)
        else:
            for apt in appointments:
                arch_list.controls.append(
                    _build_archived_card(apt, page, on_delete=arch_vm.delete, on_recover=arch_vm.recover,
                                         url_launcher=url_launcher))
        page.update()

    arch_vm.add_listener(_render_arch)
    _render_arch()

    arch_view = ft.Container(content=arch_list, padding=ft.Padding(left=16, right=16, top=10, bottom=10), expand=True)

    # --- Navigation ---
    content_area = ft.Container(expand=True)

    def _switch_tab(index: int):
        if index == 0:
            content_area.content = apt_view
            page.floating_action_button = fab
            apt_vm.load()
        else:
            content_area.content = arch_view
            page.floating_action_button = None
            arch_vm.load()
        page.update()

    _switch_tab(0)

    nav_bar = ft.NavigationBar(selected_index=0,
        on_change=lambda e: _switch_tab(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Appointments"),
            ft.NavigationBarDestination(icon=ft.Icons.ARCHIVE, label="Archive"),
        ])

    page.add(content_area, nav_bar)


if __name__ == "__main__":
    ft.run(main)
