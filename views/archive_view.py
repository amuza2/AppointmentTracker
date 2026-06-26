import flet as ft
import logging
from models.appointment import Appointment

logger = logging.getLogger("archive_view")


async def _launch_url(url):
    await ft.UrlLauncher().launch_url(url)


def _build_archived_card(apt: Appointment, page: ft.Page, on_delete=None, on_recover=None, url_launcher=None):
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

    return ft.Card(
        elevation=1,
        content=ft.Container(
            padding=16,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        [ft.Icon(ft.Icons.HOME, color=ft.Colors.GREY_400),
                         ft.Text(f"{apt.day} · {apt.time} · {apt.city}",
                                 size=16, weight=ft.FontWeight.BOLD)],
                        spacing=8,
                    ),
                    ft.Text(apt.description, size=14, selectable=True) if apt.description else ft.Container(),
                    ft.Row([url_chip]),
                    ft.Row(
                        [
                            ft.TextButton("Recover", icon=ft.Icons.RESTORE_OUTLINED,
                                            on_click=lambda _: on_recover(apt.id)),
                            ft.TextButton("Delete", icon=ft.Icons.DELETE_OUTLINE,
                                            on_click=lambda _: on_delete(apt.id)),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
            ),
        ),
    )


def create_archive_view(vm, page: ft.Page, url_launcher=None):
    list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    empty_text = ft.Text("Archive is empty.", size=14, color=ft.Colors.GREY_500)

    def _render():
        appointments = vm.appointments
        logger.info("_render() -> %d archived, list_column has %d controls before clear",
                    len(appointments), len(list_column.controls))
        list_column.controls.clear()
        if not appointments:
            list_column.controls.append(empty_text)
        else:
            for apt in appointments:
                list_column.controls.append(
                    _build_archived_card(apt, page, on_delete=vm.delete, on_recover=vm.recover, url_launcher=url_launcher)
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

    return ft.Container(
        content=list_column,
        padding=ft.Padding(left=16, right=16, top=10, bottom=10),
        expand=True,
    )
