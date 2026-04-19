
import flet as ft
import threading
import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cian_parser import CianParser


class CianParserGUI:

    def __init__(self):
        self.parser = None
        self.parsing_thread = None
        self.is_parsing = False
        self.current_results = []
        self.filtered_results = []
        self.current_page = 0
        self.items_per_page = 5

    def main(self, page: ft.Page):
        page.title = "Парсер ЦИАН - Аренда квартир"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1400
        page.window_height = 900
        page.window_min_width = 1000
        page.window_min_height = 700

        colors = {
            "grey": ft.Colors.GREY if hasattr(ft, 'Colors') else "grey",
            "red": ft.Colors.RED if hasattr(ft, 'Colors') else "red",
            "green": ft.Colors.GREEN if hasattr(ft, 'Colors') else "green",
            "blue": ft.Colors.BLUE if hasattr(ft, 'Colors') else "blue",
            "grey_800": ft.Colors.GREY_800 if hasattr(ft, 'Colors') else "grey-800",
            "grey_300": ft.Colors.GREY_300 if hasattr(ft, 'Colors') else "grey-300",
            "grey_200": ft.Colors.GREY_200 if hasattr(ft, 'Colors') else "grey-200",
            "grey_400": ft.Colors.GREY_400 if hasattr(ft, 'Colors') else "grey-400",
        }

        self.status_text = ft.Text("Готов к работе", size=12, color=colors["grey"])
        self.progress_bar = ft.ProgressBar(width=300, visible=False)
        self.log_area = ft.ListView(
            expand=True,
            spacing=5,
            auto_scroll=True
        )

        self.min_price_field = ft.TextField(
            label="Мин. цена",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="введите сумму",
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        self.max_price_field = ft.TextField(
            label="Макс. цена",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="введите сумму",
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        self.rooms_filter = ft.Dropdown(
            label="Количество комнат",
            width=170,
            options=[
                ft.dropdown.Option("0", "Все комнаты"),
                ft.dropdown.Option("1", "1 комната"),
                ft.dropdown.Option("2", "2 комнаты"),
                ft.dropdown.Option("3", "3 комнаты"),
                ft.dropdown.Option("4", "4 комнаты и более"),
            ],
            value="0",
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            text_size=14
        )

        self.min_area_field = ft.TextField(
            label="Мин. площадь",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="м² от",
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        max_scrolls_field = ft.TextField(
            label="Количество прокруток",
            value="10",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        max_results_field = ft.TextField(
            label="Макс. объявлений",
            value="30",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        url_field = ft.TextField(
            label="URL для парсинга",
            value="https://ekb.cian.ru/snyat-kvartiru/",
            width=450,
            hint_text="Введите URL страницы ЦИАН",
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        self.excel_prefix_field = ft.TextField(
            label="Префикс имени Excel",
            value="Cian_parser",
            width=180,
            dense=False,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            text_size=14
        )

        self.include_datetime_checkbox = ft.Checkbox(
            label="Добавить дату и время в название",
            value=True
            # label_size=13 удалён — не поддерживается в твоей версии Flet
        )

        start_button = ft.ElevatedButton(
            "Старт",
            icon=ft.Icons.PLAY_ARROW,
            on_click=lambda e: self.start_parsing(
                page,
                url_field.value,
                int(max_scrolls_field.value),
                int(max_results_field.value)
            ),
            style=ft.ButtonStyle(padding=12),
            width=100
        )

        stop_button = ft.ElevatedButton(
            "Стоп",
            icon=ft.Icons.STOP,
            color=colors["red"],
            on_click=self.stop_parsing,
            disabled=True,
            style=ft.ButtonStyle(padding=12),
            width=100
        )

        save_text_button = ft.ElevatedButton(
            "Сохранить TXT",
            icon=ft.Icons.TEXT_FIELDS,
            on_click=lambda e: self.save_results("txt"),
            disabled=True,
            style=ft.ButtonStyle(padding=12)
        )

        save_json_button = ft.ElevatedButton(
            "Сохранить JSON",
            icon=ft.Icons.CODE,
            on_click=lambda e: self.save_results("json"),
            disabled=True,
            style=ft.ButtonStyle(padding=12)
        )

        save_excel_button = ft.ElevatedButton(
            "Сохранить Excel",
            icon=ft.Icons.TABLE_CHART,
            on_click=lambda e: self.save_results("excel"),
            disabled=True,
            style=ft.ButtonStyle(padding=12),
            width=130
        )

        clear_log_button = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL,
            tooltip="Очистить лог",
            icon_size=24,
            on_click=lambda e: self.log_area.controls.clear() or page.update()
        )

        apply_filters_button = ft.ElevatedButton(
            "Применить фильтры",
            icon=ft.Icons.FILTER_LIST,
            on_click=lambda e: self.apply_filters(),
            style=ft.ButtonStyle(padding=12)
        )

        reset_filters_button = ft.OutlinedButton(
            "Сбросить",
            icon=ft.Icons.CLEAR,
            on_click=lambda e: self.reset_filters(),
            style=ft.ButtonStyle(padding=12)
        )

        self.top_panel_height = 280
        self.top_panel_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        url_field,
                        max_scrolls_field,
                        max_results_field,
                        start_button,
                        stop_button,
                    ], spacing=12, wrap=True, alignment=ft.MainAxisAlignment.START),
                    margin=ft.margin.only(bottom=8)
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Text("Фильтры:", size=14, weight=ft.FontWeight.BOLD),
                        self.min_price_field,
                        self.max_price_field,
                        self.rooms_filter,
                        self.min_area_field,
                        apply_filters_button,
                        reset_filters_button,
                    ], spacing=12, wrap=True, alignment=ft.MainAxisAlignment.START),
                    margin=ft.margin.only(bottom=8)
                ),
                ft.Container(
                    content=ft.Row([
                        save_text_button,
                        save_json_button,
                        save_excel_button,
                        ft.VerticalDivider(width=1, color=colors["grey_400"]),
                        self.excel_prefix_field,
                        self.include_datetime_checkbox,
                        clear_log_button,
                    ], spacing=12, wrap=True),
                    margin=ft.margin.only(bottom=8)
                ),
                ft.Row([
                    self.status_text,
                    self.progress_bar,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=10),
            height=self.top_panel_height,
            margin=ft.margin.only(bottom=8),
            padding=ft.padding.all(12),
            bgcolor=colors["grey_200"],
            border_radius=12
        )

        top_splitter = ft.Container(height=2, margin=ft.margin.symmetric(vertical=5),
                                    bgcolor=colors["grey_300"], border_radius=1)

        self.results_list = ft.ListView(expand=True, spacing=10, auto_scroll=False)

        self.pagination_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER)

        results_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Результаты парсинга", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("", size=11, color=colors["green"], key="results_count"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(
                    content=self.results_list,
                    expand=True,
                    border=ft.border.all(1, colors["grey_300"]),
                    border_radius=8,
                    padding=5
                ),
                self.pagination_row,
            ], spacing=8, expand=True),
            expand=True,
            margin=ft.margin.only(bottom=5)
        )

        self.log_container = ft.Container(
            content=ft.Column([
                ft.Text("Лог парсинга", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.log_area,
                    expand=True,
                    border=ft.border.all(1, colors["grey_300"]),
                    border_radius=8,
                    padding=5
                ),
            ], spacing=8, expand=True),
            height=150,
            margin=ft.margin.only(top=5),
            padding=ft.padding.all(12),
            bgcolor=colors["grey_200"],
            border_radius=12
        )

        bottom_splitter = ft.Container(height=2, margin=ft.margin.symmetric(vertical=5),
                                       bgcolor=colors["grey_300"], border_radius=1)

        main_column = ft.Column([
            self.top_panel_container,
            top_splitter,
            ft.Container(
                content=ft.Row([
                    ft.Container(content=results_container, expand=3, margin=ft.margin.only(right=5)),
                    ft.Container(
                        content=ft.Column([bottom_splitter, self.log_container], spacing=0),
                        expand=2,
                        margin=ft.margin.only(left=5)
                    ),
                ], expand=True, spacing=10),
                expand=True
            ),
        ], spacing=0, expand=True)

        page.add(main_column)

        self.start_button = start_button
        self.stop_button = stop_button
        self.save_text_button = save_text_button
        self.save_json_button = save_json_button
        self.save_excel_button = save_excel_button
        self.max_scrolls_field = max_scrolls_field
        self.max_results_field = max_results_field
        self.url_field = url_field
        self.page = page
        self.colors = colors
        self.apply_filters_button = apply_filters_button
        self.reset_filters_button = reset_filters_button

        self.add_log("Интерфейс загружен")
        self.add_log("Готов к запуску парсинга")


    def add_log(self, message, is_error=False):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.colors["red"] if is_error else self.colors["grey_800"]
        self.log_area.controls.append(
            ft.Text(f"[{timestamp}] {message}", color=color, size=11)
        )
        self.page.update()

    def update_progress(self, message, progress):
        self.status_text.value = message
        if progress >= 0:
            self.progress_bar.visible = True
            self.progress_bar.value = progress / 100
        else:
            self.progress_bar.visible = False
        self.page.update()

    def extract_float_from_string(self, text):
        if not text:
            return 0
        try:
            import re
            match = re.search(r'(\d+[.,]?\d*)', text)
            if match:
                num_str = match.group(1).replace(',', '.')
                num = float(num_str)
                return math.floor(num)
            return 0
        except:
            return 0

    def apply_filters(self):
        if not self.current_results:
            self.add_log("Нет результатов для фильтрации", True)
            return

        min_price_str = self.min_price_field.value
        max_price_str = self.max_price_field.value
        rooms_filter = int(self.rooms_filter.value) if self.rooms_filter.value != "0" else 0
        min_area_str = self.min_area_field.value

        min_price = int(min_price_str) if min_price_str and min_price_str.strip() else 0
        max_price = int(max_price_str) if max_price_str and max_price_str.strip() else float('inf')
        min_area = int(min_area_str) if min_area_str and min_area_str.strip() else 0

        filters_applied = []
        if min_price > 0: filters_applied.append(f"цена от {min_price}")
        if max_price != float('inf'): filters_applied.append(f"цена до {max_price}")
        if rooms_filter > 0: filters_applied.append(f"{rooms_filter} комн.")
        if min_area > 0: filters_applied.append(f"площадь от {min_area} м²")

        self.add_log(f"Применяем фильтры: {', '.join(filters_applied) if filters_applied else 'все объявления'}")

        filtered = []
        for item in self.current_results:
            price_match = True
            if item['price'] != "Цена не указана":
                try:
                    price = int(''.join(filter(str.isdigit, item['price'])))
                    if price < min_price or price > max_price:
                        price_match = False
                except:
                    price_match = False

            rooms_match = True
            if rooms_filter > 0:
                if rooms_filter == 4:
                    if item['rooms'] < 4:
                        rooms_match = False
                else:
                    if item['rooms'] != rooms_filter:
                        rooms_match = False

            area_match = True
            if min_area > 0:
                area_value = self.extract_float_from_string(item.get('subtitle', ''))
                if area_value < min_area:
                    area_match = False

            if price_match and rooms_match and area_match:
                filtered.append(item)

        self.filtered_results = filtered
        self.current_page = 0
        self.update_results_display()

        if filtered:
            self.add_log(f" Применены фильтры. Найдено: {len(filtered)} из {len(self.current_results)}")
        else:
            self.add_log(f" По фильтрам ничего не найдено. Всего: {len(self.current_results)}")

    def reset_filters(self):
        self.min_price_field.value = ""
        self.max_price_field.value = ""
        self.rooms_filter.value = "0"
        self.min_area_field.value = ""
        self.filtered_results = self.current_results.copy()
        self.current_page = 0
        self.update_results_display()
        self.add_log("Фильтры сброшены. Показаны все объявления")
        self.page.update()

    def update_results_display(self):
        self.results_list.controls.clear()
        results_to_show = self.filtered_results if self.filtered_results else self.current_results

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(results_to_show))

        for i in range(start_idx, end_idx):
            self.results_list.controls.append(self.create_result_card(results_to_show[i], i + 1))

        total_pages = (len(results_to_show) + self.items_per_page - 1) // self.items_per_page
        self.pagination_row.controls = [
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=lambda e: self.prev_page(),
                          disabled=self.current_page == 0, icon_size=20),
            ft.Text(f"Страница {self.current_page + 1} из {max(1, total_pages)}", size=12),
            ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self.next_page(),
                          disabled=self.current_page >= total_pages - 1, icon_size=20),
        ]
        self.page.update()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_results_display()

    def next_page(self):
        results_to_show = self.filtered_results if self.filtered_results else self.current_results
        total_pages = (len(results_to_show) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_results_display()

    def create_result_card(self, item, index):
        first_image = item['images'][0] if item['images'] else None

        if first_image:
            image_container = ft.Container(
                width=120, height=120, bgcolor=self.colors["grey_200"], border_radius=8,
                content=ft.Image(src=first_image, width=120, height=120, fit=ft.BoxFit.COVER,
                                 error_content=ft.Icon(ft.Icons.BROKEN_IMAGE, size=30))
            )
        else:
            image_container = ft.Container(
                width=120, height=120, bgcolor=self.colors["grey_200"], border_radius=8,
                content=ft.Icon(ft.Icons.HIDE_IMAGE, size=30), alignment=ft.alignment.center
            )

        info_column = ft.Column([
            ft.Text(f"{index}. {item['title']}", weight=ft.FontWeight.BOLD, size=12),
            ft.Text(item['subtitle'], size=11, color=self.colors["grey"]),
            ft.Text(item['price'], size=14, color=self.colors["green"], weight=ft.FontWeight.BOLD),
            ft.Text(item['address'], size=10, color=self.colors["blue"]),
            ft.Text(
                item['description'][:150] + "..." if len(item['description']) > 150 else item['description'],
                size=10, color=self.colors["grey_800"], max_lines=2
            ),
            ft.Text(f"📷 {len(item['images'])} фото", size=9),
        ], spacing=4, expand=True)

        buttons_row = ft.Row([
            ft.IconButton(icon=ft.Icons.LINK, tooltip="Открыть ссылку",
                          on_click=lambda e, url=item['link']: self.page.launch_url(url), icon_size=18),
            ft.IconButton(icon=ft.Icons.IMAGE, tooltip="Показать все фото",
                          on_click=lambda e, images=item['images']: self.show_images_dialog(images), icon_size=18),
        ], spacing=0)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([image_container, ft.Column([info_column, buttons_row], expand=True, spacing=4)],
                               spacing=8),
                padding=8,
            ),
            margin=ft.margin.only(bottom=5),
        )

    def show_images_dialog(self, images):
        if not images:
            return

        current_index = [0]

        def change_image(delta):
            current_index[0] = (current_index[0] + delta) % len(images)
            image_display.src = images[current_index[0]]
            self.page.update()

        image_display = ft.Image(src=images[0], width=500, height=400, fit=ft.BoxFit.CONTAIN)

        dialog = ft.AlertDialog(
            title=ft.Text("Фото"),
            content=ft.Container(
                content=ft.Column([
                    image_display,
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.CHEVRON_LEFT,
                                      on_click=lambda e: change_image(-1),
                                      disabled=len(images) <= 1),
                        ft.Text(f"1/{len(images)}", size=12),
                        ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT,
                                      on_click=lambda e: change_image(1),
                                      disabled=len(images) <= 1),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=10),
                width=600, height=500,
            ),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: self.close_dialog(dialog))]
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def start_parsing(self, page, url, max_scrolls, max_results):
        if self.is_parsing:
            self.add_log("Парсинг уже выполняется!", True)
            return

        self.is_parsing = True
        self.current_results = []

        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.save_text_button.disabled = True
        self.save_json_button.disabled = True
        self.save_excel_button.disabled = True

        self.log_area.controls.clear()
        self.results_list.controls.clear()
        self.update_progress("Запуск парсера...", 0)

        self.parsing_thread = threading.Thread(
            target=self.run_parser,
            args=(url, max_scrolls, max_results),
            daemon=True
        )
        self.parsing_thread.start()

    def run_parser(self, url, max_scrolls, max_results):
        try:
            self.add_log(f"Инициализация парсера...")
            self.add_log(f"URL: {url}")
            self.add_log(f"Макс. прокруток: {max_scrolls}")
            self.add_log(f"Макс. объявлений: {max_results}")

            self.parser = CianParser(headless=False, max_scrolls=max_scrolls, max_results=max_results)

            def progress_callback(message, progress):
                self.update_progress(message, progress)
                self.add_log(message)

            results = self.parser.parse(url, progress_callback)
            self.current_results = results
            self.filtered_results = results.copy()

            if results:
                self.add_log(f"✓ Парсинг завершён! Найдено: {len(results)} объявлений")
                self.update_progress(f"Готово! Найдено {len(results)} объявлений", 100)
                self.update_results_display()

                self.save_text_button.disabled = False
                self.save_json_button.disabled = False
                self.save_excel_button.disabled = False
            else:
                self.add_log("Не найдено ни одного объявления", True)

        except Exception as e:
            self.add_log(f"Ошибка: {e}", True)
            self.update_progress(f"Ошибка: {e}", -1)
        finally:
            if self.parser:
                self.parser.close()
            self.is_parsing = False
            self.start_button.disabled = False
            self.stop_button.disabled = True
            self.page.update()

    def stop_parsing(self, e):
        if self.is_parsing:
            self.is_parsing = False
            if self.parser:
                self.parser.close()
            self.add_log("Парсинг остановлен пользователем")
            self.update_progress("Парсинг остановлен", -1)
            self.start_button.disabled = False
            self.stop_button.disabled = True
            self.page.update()

    def save_results(self, format_type):
        if not self.current_results:
            self.add_log("Нет результатов для сохранения", True)
            return

        try:
            if format_type == "txt":
                filename = self.parser.save_to_text(self.current_results)
                self.add_log(f" Сохранено в TXT: {filename}")

            elif format_type == "json":
                filename = self.parser.save_to_json(self.current_results)
                self.add_log(f" Сохранено в JSON: {filename}")

            elif format_type == "excel":
                from excel_exporter import export_results_to_excel
                prefix = self.excel_prefix_field.value.strip()
                include_dt = self.include_datetime_checkbox.value

                filename = export_results_to_excel(
                    self.current_results,
                    prefix=prefix if prefix else "Cian_parser",
                    include_datetime=include_dt
                )

                if filename:
                    self.add_log(f" Сохранено в Excel: {filename}")
                else:
                    self.add_log(" Ошибка при сохранении Excel", True)

        except Exception as e:
            self.add_log(f"Ошибка при сохранении: {e}", True)


def main():
    app = CianParserGUI()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()