import flet as ft
import threading
import os
import sys
import json
import math
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cian_parser import CianParser
from monitor import CianMonitor
from excel_exporter import export_results_to_excel

class CianParserGUI:

    def __init__(self):
        self.parser = None
        self.monitor = CianMonitor()
        self.parsing_thread = None
        self.is_parsing = False
        self.current_results = []
        self.filtered_results = []
        self.current_page = 0
        self.items_per_page = 5
        self.settings_file = "monitor_settings.json"

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_settings(self):
        settings = {
            "email_to": self.monitor_email.value.strip(),
            "email_from": self.monitor_from_email.value.strip(),
            "notify_always": self.notify_always_checkbox.value,
            "interval_min": int(self.monitor_interval.value) if self.monitor_interval.value.strip() else 60
        }
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.add_log(" Настройки мониторинга сохранены")
        except Exception as e:
            self.add_log(f"Ошибка сохранения настроек: {e}", True)

    def main(self, page: ft.Page):
        page.title = "Парсер ЦИАН - Аренда квартир + Мониторинг"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1480
        page.window_height = 1000
        page.window_min_width = 1150
        page.window_min_height = 780

        colors = {
            "grey": ft.Colors.GREY,
            "red": ft.Colors.RED,
            "green": ft.Colors.GREEN,
            "blue": ft.Colors.BLUE,
            "grey_800": ft.Colors.GREY_800,
            "grey_300": ft.Colors.GREY_300,
            "grey_200": ft.Colors.GREY_200,
            "grey_400": ft.Colors.GREY_400,
        }

        settings = self.load_settings()

        self.status_text = ft.Text("Готов к работе", size=12, color=colors["grey"])
        self.progress_bar = ft.ProgressBar(width=320, visible=False)
        self.log_area = ft.ListView(expand=True, spacing=5, auto_scroll=True)

        self.min_price_field = ft.TextField(label="Мин. цена", width=150, keyboard_type=ft.KeyboardType.NUMBER, hint_text="сумма")
        self.max_price_field = ft.TextField(label="Макс. цена", width=150, keyboard_type=ft.KeyboardType.NUMBER, hint_text="сумма")
        self.rooms_filter = ft.Dropdown(label="Комнаты", width=170, value="0", options=[
            ft.dropdown.Option("0", "Все"), ft.dropdown.Option("1", "1"),
            ft.dropdown.Option("2", "2"), ft.dropdown.Option("3", "3"),
            ft.dropdown.Option("4", "4+")
        ])
        self.min_area_field = ft.TextField(label="Мин. площадь (м²)", width=160, keyboard_type=ft.KeyboardType.NUMBER)

        url_field = ft.TextField(
            label="URL для парсинга", value="https://ekb.cian.ru/snyat-kvartiru/",
            width=500, dense=False
        )
        max_scrolls_field = ft.TextField(label="Прокруток", value="1", width=130)
        max_results_field = ft.TextField(label="Макс. объявлений", value="30", width=160)

        self.excel_prefix_field = ft.TextField(label="Префикс Excel", value="Cian_parser", width=180)
        self.include_datetime_checkbox = ft.Checkbox(label="Дата+время в имени", value=True)

        self.monitor_interval = ft.TextField(
            label="Интервал (мин)", value=str(settings.get("interval_min", 60)), width=130,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.monitor_email = ft.TextField(
            label="Email получателя", value=settings.get("email_to", ""), width=260,
            hint_text="your@gmail.com"
        )

        self.monitor_from_email = ft.TextField(
            label="Gmail отправитель", value=settings.get("email_from", ""), width=240,
            hint_text="your@gmail.com"
        )

        self.monitor_password = ft.TextField(
            label="Пароль приложения Gmail", width=190, password=True, can_reveal_password=True,
            hint_text="16 символов"
        )

        self.notify_always_checkbox = ft.Checkbox(
            label="Уведомлять всегда (даже без изменений)",
            value=settings.get("notify_always", False)
        )

        start_button = ft.ElevatedButton("Старт", icon=ft.Icons.PLAY_ARROW, width=110,
                                         on_click=lambda e: self.start_parsing(page, url_field.value,
                                              int(max_scrolls_field.value), int(max_results_field.value)))

        stop_button = ft.ElevatedButton("Стоп", icon=ft.Icons.STOP, color=colors["red"], width=110,
                                        on_click=self.stop_parsing, disabled=True)

        save_text_button = ft.ElevatedButton("TXT", icon=ft.Icons.TEXT_FIELDS,
                                             on_click=lambda e: self.save_results("txt"), disabled=True)
        save_json_button = ft.ElevatedButton("JSON", icon=ft.Icons.CODE,
                                             on_click=lambda e: self.save_results("json"), disabled=True)
        save_excel_button = ft.ElevatedButton("Excel", icon=ft.Icons.TABLE_CHART,
                                              on_click=lambda e: self.save_results("excel"), disabled=True, width=120)

        save_monitor_settings_btn = ft.ElevatedButton(
            "Сохранить настройки", icon=ft.Icons.SAVE,
            on_click=lambda e: self.save_settings()
        )

        monitor_start_btn = ft.ElevatedButton(
            "Запустить мониторинг", icon=ft.Icons.SCHEDULE, color=ft.Colors.GREEN_700,
            on_click=self.start_monitoring
        )

        monitor_stop_btn = ft.ElevatedButton(
            "Остановить мониторинг", icon=ft.Icons.STOP, color=colors["red"],
            on_click=self.stop_monitoring, disabled=True
        )

        clear_log_button = ft.IconButton(icon=ft.Icons.CLEAR_ALL, tooltip="Очистить лог",
                                         on_click=lambda e: (self.log_area.controls.clear(), page.update()))

        apply_filters_button = ft.ElevatedButton("Применить фильтры", icon=ft.Icons.FILTER_LIST,
                                                 on_click=lambda e: self.apply_filters())
        reset_filters_button = ft.OutlinedButton("Сбросить", icon=ft.Icons.CLEAR,
                                                 on_click=lambda e: self.reset_filters())

        top_panel = ft.Container(
            content=ft.Column([
                ft.Row([url_field, max_scrolls_field, max_results_field, start_button, stop_button], spacing=10, wrap=True),

                ft.Row([ft.Text("Фильтры:", weight=ft.FontWeight.BOLD, size=14),
                        self.min_price_field, self.max_price_field, self.rooms_filter,
                        self.min_area_field, apply_filters_button, reset_filters_button], spacing=10, wrap=True),

                ft.Row([
                    save_text_button, save_json_button, save_excel_button,
                    self.excel_prefix_field, self.include_datetime_checkbox,
                    clear_log_button,
                    ft.VerticalDivider(),
                    ft.Text("Мониторинг:", weight=ft.FontWeight.BOLD),
                    self.monitor_interval,
                    save_monitor_settings_btn
                ], spacing=10, wrap=True),

                ft.Row([
                    self.monitor_email, self.monitor_from_email, self.monitor_password,
                    self.notify_always_checkbox, monitor_start_btn, monitor_stop_btn
                ], spacing=10, wrap=True),

                ft.Row([self.status_text, self.progress_bar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=12),
            padding=14,
            bgcolor=colors["grey_200"],
            border_radius=12
        )

        self.results_list = ft.ListView(expand=True, spacing=10)
        self.pagination_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER)

        results_container = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Результаты", size=15, weight=ft.FontWeight.BOLD),
                        ft.Text("", color=colors["green"], key="count")],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(self.results_list, expand=True, border=ft.Border.all(1, colors["grey_300"]), border_radius=8, padding=6),
                self.pagination_row
            ], expand=True),
            expand=3
        )

        log_container = ft.Container(
            content=ft.Column([
                ft.Text("Лог", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(self.log_area, expand=True, border=ft.Border.all(1, colors["grey_300"]), border_radius=8, padding=8)
            ], expand=True),
            expand=2, height=200, padding=10, bgcolor=colors["grey_200"], border_radius=12
        )

        main_view = ft.Column([
            top_panel,
            ft.Row([results_container, log_container], expand=True, spacing=12)
        ], expand=True, spacing=10)

        page.add(main_view)

        self.start_button = start_button
        self.stop_button = stop_button
        self.save_text_button = save_text_button
        self.save_json_button = save_json_button
        self.save_excel_button = save_excel_button
        self.monitor_start_btn = monitor_start_btn
        self.monitor_stop_btn = monitor_stop_btn
        self.url_field = url_field
        self.page = page
        self.colors = colors

        self.add_log("Интерфейс загружен")
        self.add_log("Настройки мониторинга загружены из файла")

    def add_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.colors["red"] if is_error else self.colors["grey_800"]
        self.log_area.controls.append(ft.Text(f"[{timestamp}] {message}", color=color, size=12))
        self.page.update()

    def update_progress(self, message, progress):
        self.status_text.value = message
        self.progress_bar.visible = progress >= 0
        if progress >= 0:
            self.progress_bar.value = progress / 100
        self.page.update()

    def apply_filters(self):
        if not self.current_results:
            self.add_log("Нет результатов для фильтрации", True)
            return
        min_price = int(self.min_price_field.value) if self.min_price_field.value.strip() else 0
        max_price = int(self.max_price_field.value) if self.max_price_field.value.strip() else float('inf')
        rooms_filter = int(self.rooms_filter.value) if self.rooms_filter.value != "0" else 0
        min_area = int(self.min_area_field.value) if self.min_area_field.value.strip() else 0

        filtered = []
        for item in self.current_results:
            price_match = True
            if item.get('price') != "Цена не указана":
                try:
                    price = int(''.join(filter(str.isdigit, item['price'])))
                    if price < min_price or (max_price != float('inf') and price > max_price):
                        price_match = False
                except:
                    price_match = False

            rooms_match = True
            if rooms_filter > 0:
                if rooms_filter == 4:
                    if item.get('rooms', 0) < 4: rooms_match = False
                elif item.get('rooms', 0) != rooms_filter:
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
        self.add_log(f"Применены фильтры. Найдено: {len(filtered)}")

    def reset_filters(self):
        self.min_price_field.value = ""
        self.max_price_field.value = ""
        self.rooms_filter.value = "0"
        self.min_area_field.value = ""
        self.filtered_results = self.current_results.copy()
        self.current_page = 0
        self.update_results_display()
        self.add_log("Фильтры сброшены")

    def extract_float_from_string(self, text):
        if not text: return 0
        try:
            import re
            match = re.search(r'(\d+[.,]?\d*)', text)
            if match:
                return math.floor(float(match.group(1).replace(',', '.')))
            return 0
        except:
            return 0

    def update_results_display(self):
        self.results_list.controls.clear()
        results_to_show = self.filtered_results if self.filtered_results else self.current_results
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(results_to_show))

        for i in range(start_idx, end_idx):
            self.results_list.controls.append(self.create_result_card(results_to_show[i], i + 1))

        total_pages = (len(results_to_show) + self.items_per_page - 1) // self.items_per_page
        self.pagination_row.controls = [
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=lambda _: self.prev_page(),
                          disabled=self.current_page == 0),
            ft.Text(f"{self.current_page + 1} / {max(1, total_pages)}"),
            ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda _: self.next_page(),
                          disabled=self.current_page >= total_pages - 1),
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
        first_image = item['images'][0] if item.get('images') else None
        image_container = ft.Container(
            width=130, height=130, bgcolor=self.colors["grey_200"], border_radius=8,
            content=ft.Image(src=first_image, fit=ft.BoxFit.COVER, error_content=ft.Icon(ft.Icons.BROKEN_IMAGE)) if first_image else
                    ft.Icon(ft.Icons.HIDE_IMAGE, size=50)
        )

        info = ft.Column([
            ft.Text(f"{index}. {item.get('title')}", weight=ft.FontWeight.BOLD, size=13),
            ft.Text(item.get('subtitle', ''), size=12, color=self.colors["grey"]),
            ft.Text(item.get('price', ''), size=15, color=self.colors["green"], weight=ft.FontWeight.BOLD),
            ft.Text(item.get('address', ''), size=11, color=self.colors["blue"]),
        ], spacing=4, expand=True)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([image_container, info], spacing=12),
                padding=10
            ),
            margin=ft.margin.only(bottom=6)
        )

    def show_images_dialog(self, images):
        if not images: return
        dlg = ft.AlertDialog(title=ft.Text("Фото объявления"), content=ft.Image(src=images[0], width=600))
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def start_parsing(self, page, url, max_scrolls, max_results):
        if self.is_parsing: return
        self.is_parsing = True
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.save_text_button.disabled = True
        self.save_json_button.disabled = True
        self.save_excel_button.disabled = True
        self.results_list.controls.clear()

        threading.Thread(target=self.run_parser, args=(url, max_scrolls, max_results), daemon=True).start()

    def run_parser(self, url, max_scrolls, max_results):
        try:
            self.parser = CianParser(headless=False, max_scrolls=max_scrolls, max_results=max_results)
            def cb(msg, prog):
                self.update_progress(msg, prog)
                self.add_log(msg)

            results = self.parser.parse(url, cb)
            self.current_results = results
            self.filtered_results = results.copy()

            if results:
                self.update_results_display()
                self.save_text_button.disabled = False
                self.save_json_button.disabled = False
                self.save_excel_button.disabled = False
                self.add_log(f"Парсинг завершён — найдено {len(results)} объявлений")
            else:
                self.add_log("Объявления не найдены", True)
        except Exception as e:
            self.add_log(f"Ошибка: {e}", True)
        finally:
            if self.parser: self.parser.close()
            self.is_parsing = False
            self.start_button.disabled = False
            self.stop_button.disabled = True
            self.page.update()

    def stop_parsing(self, e):
        if self.parser: self.parser.close()
        self.is_parsing = False
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.add_log("Парсинг остановлен")

    def start_monitoring(self, e):
        if self.monitor.is_monitoring:
            self.add_log("Мониторинг уже работает", True)
            return

        email_settings = {
            'to': self.monitor_email.value.strip(),
            'from': self.monitor_from_email.value.strip(),
            'password': self.monitor_password.value.strip()
        }

        if not email_settings['to'] or not email_settings['from'] or not email_settings['password']:
            self.add_log(" Заполните данные почты", True)
            return

        try:
            interval_sec = int(self.monitor_interval.value) * 60

            self.monitor_start_btn.disabled = True
            self.monitor_stop_btn.disabled = False
            self.page.update()

            def progress_cb(msg, prog):
                self.update_progress(msg, prog)
                self.add_log(msg)

            threading.Thread(
                target=self.monitor.start,
                args=(self.url_field.value, interval_sec, 30, email_settings,
                      self.notify_always_checkbox.value, progress_cb),
                daemon=True
            ).start()

            self.add_log(f" Мониторинг запущен каждые {self.monitor_interval.value} минут")
        except Exception as ex:
            self.add_log(f"Ошибка запуска мониторинга: {ex}", True)

    def stop_monitoring(self, e):
        self.monitor.stop()
        self.monitor_start_btn.disabled = False
        self.monitor_stop_btn.disabled = True
        self.add_log("Мониторинг остановлен")
        self.page.update()

    def save_results(self, format_type):
        if not self.current_results:
            self.add_log("Нет данных для сохранения", True)
            return
        try:
            if format_type == "txt":
                filename = self.parser.save_to_text(self.current_results)
            elif format_type == "json":
                filename = self.parser.save_to_json(self.current_results)
            elif format_type == "excel":
                filename = export_results_to_excel(
                    self.current_results,
                    self.excel_prefix_field.value.strip() or "Cian_parser",
                    self.include_datetime_checkbox.value
                )
            self.add_log(f" Сохранено: {filename}")
        except Exception as e:
            self.add_log(f"Ошибка сохранения: {e}", True)


def main():
    app = CianParserGUI()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()