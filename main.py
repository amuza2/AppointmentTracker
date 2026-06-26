import asyncio
import logging
import flet as ft

from services import database
from viewmodels.appointments_vm import AppointmentsViewModel
from viewmodels.archive_vm import ArchiveViewModel
from views.appointments_view import create_appointments_view
from views.archive_view import create_archive_view

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("main")


async def main(page: ft.Page):
    page.title = "House Tracker"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.theme_mode = ft.ThemeMode.LIGHT

    database.init_db()

    url_launcher = ft.UrlLauncher()

    appointments_vm = AppointmentsViewModel()
    archive_vm = ArchiveViewModel()

    appointments_view, fab, add_dialog, edit_dialog = create_appointments_view(appointments_vm, page, url_launcher)
    archive_view = create_archive_view(archive_vm, page, url_launcher)

    page.overlay.append(add_dialog)
    page.overlay.append(edit_dialog)
    page.floating_action_button = fab

    content_area = ft.Container(expand=True)

    def _switch_tab(index: int):
        logger.info("_switch_tab(%d)", index)
        if index == 0:
            content_area.content = appointments_view
            page.floating_action_button = fab
            appointments_vm.load()
        else:
            content_area.content = archive_view
            page.floating_action_button = None
            archive_vm.load()

    _switch_tab(0)

    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: _switch_tab(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Appointments"),
            ft.NavigationBarDestination(icon=ft.Icons.ARCHIVE_OUTLINED, selected_icon=ft.Icons.ARCHIVE, label="Archive"),
        ],
    )

    page.add(
        ft.Column(
            [
                content_area,
                nav_bar,
            ],
            expand=True,
        )
    )

    _request_browser_notification_permission(page)

    async def _notification_loop():
        notified_ids = set()
        while True:
            try:
                upcoming = database.get_upcoming_appointments(within_minutes=60)
                for apt in upcoming:
                    if apt.id not in notified_ids:
                        notified_ids.add(apt.id)
                        _show_notification(page, apt)
            except Exception:
                pass
            await asyncio.sleep(60)

    page.run_task(_notification_loop)


def _request_browser_notification_permission(page: ft.Page):
    pass


def _show_notification(page: ft.Page, apt):
    message = f"Appointment today at {apt.time} in {apt.city}"
    snack = ft.SnackBar(ft.Text(f"Upcoming: {message}"), duration=5000)
    page.overlay.append(snack)
    snack.open = True
    try:
        page.update()
    except Exception:
        pass


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
