
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import json
from datetime import datetime
import os
import re

class CianParser:

    def __init__(self, headless=False, max_scrolls=10, max_results=30):
        self.headless = headless
        self.max_scrolls = max_scrolls
        self.max_results = max_results
        self.page = None
        self.results = []
        self.seen_links = set()

    def setup_browser(self):
        try:
            co = ChromiumOptions()
            co.set_browser_path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            co.headless(self.headless)
            co.set_argument('--start-maximized')

            self.page = ChromiumPage(co)
            return True
        except Exception as e:
            print(f"Ошибка при настройке браузера: {e}")
            return False

    def extract_description(self, card):
        try:
            desc_elem = card.ele('css:div[data-name="Description"]', timeout=0.1)
            if desc_elem:
                desc_text = desc_elem.text.strip()
                if desc_text:
                    return desc_text

            desc_elem = card.ele('css:.x31de4314--_74dfe--description', timeout=0.1)
            if desc_elem:
                desc_text = desc_elem.text.strip()
                if desc_text:
                    return desc_text

            return "Описание отсутствует"
        except:
            return "Описание отсутствует"

    def extract_address(self, card):
        try:
            address_parts = []
            geo_elements = card.eles('css:a[data-name="GeoLabel"]', timeout=0.1)
            for elem in geo_elements:
                address_parts.append(elem.text.strip())

            metro_elem = card.ele('css:div[data-name="SpecialGeo"]', timeout=0.1)
            if metro_elem:
                metro_text = metro_elem.text.strip()
                if metro_text:
                    address_parts.insert(0, metro_text)

            return " | ".join(address_parts) if address_parts else "Адрес не указан"
        except:
            return "Адрес не указан"

    def extract_price_info(self, card):
        try:
            price_info_elem = card.ele('css:p[data-mark="PriceInfo"]', timeout=0.1)
            if price_info_elem:
                return price_info_elem.text.strip()
            return ""
        except:
            return ""

    def parse_card(self, card):
        try:
            link_elem = card.ele('tag:a', timeout=0.1)
            link = link_elem.attr('href') if link_elem else ""
            if not link or link in self.seen_links:
                return None
            if not link.startswith("http"):
                link = "https://ekb.cian.ru" + link
            self.seen_links.add(link)

            title_elem = card.ele('css:span[data-mark="OfferTitle"]', timeout=0.1)
            title = title_elem.text.strip() if title_elem else "Без названия"

            subtitle_elem = card.ele('css:span[data-mark="OfferSubtitle"]', timeout=0.1)
            subtitle = subtitle_elem.text.strip() if subtitle_elem else ""

            price_elem = card.ele('css:span[data-mark="MainPrice"]', timeout=0.1)
            price = price_elem.text.strip() if price_elem else "Цена не указана"

            price_info = self.extract_price_info(card)

            address = self.extract_address(card)

            description = self.extract_description(card)

            images = []
            img_elements = card.eles('css:img.x31de4314--_18b0f--container')
            for img in img_elements:
                src = img.attr('src')
                if src and src.startswith('http'):
                    images.append(src)

            rooms = 0
            if subtitle:
                rooms_match = re.search(r'(\d+)-комн', subtitle)
                if rooms_match:
                    rooms = int(rooms_match.group(1))

            area = 0
            if subtitle:
                area_match = re.search(r'(\d+)\s*м²', subtitle)
                if area_match:
                    area = int(area_match.group(1))

            floor = ""
            if subtitle:
                floor_match = re.search(r'(\d+)/(\d+)\s*этаж', subtitle)
                if floor_match:
                    floor = f"{floor_match.group(1)}/{floor_match.group(2)}"

            return {
                "title": title,
                "subtitle": subtitle,
                "price": price,
                "price_info": price_info,
                "address": address,
                "description": description,
                "link": link,
                "images": images,
                "rooms": rooms,
                "area": area,
                "floor": floor
            }
        except Exception as e:
            print(f"Ошибка при парсинге карточки: {e}")
            return None

    def find_next_button(self):
        try:
            next_button = self.page.ele('css:a span:text("Дальше")', timeout=0.5)
            if next_button:
                parent_link = next_button.parent('tag:a')
                if parent_link:
                    return parent_link
                return next_button

            next_button = self.page.ele('css:a.x31de4314--a048a1--button span.x31de4314--a048a1--text', timeout=0.5)
            if next_button and next_button.text.strip() == "Дальше":
                parent_link = next_button.parent('tag:a')
                if parent_link:
                    return parent_link

            all_links = self.page.eles('css:a', timeout=0.5)
            for link in all_links:
                if link.text.strip() == "Дальше":
                    return link

            return None
        except Exception as e:
            print(f"Ошибка при поиске кнопки 'Дальше': {e}")
            return None

    def parse_page(self, progress_callback=None, page_num=1):

        if progress_callback:
            progress_callback(f"Парсинг страницы {page_num}...", 0)

        time.sleep(3)

        for scroll in range(self.max_scrolls):
            if progress_callback:
                progress_callback(f"Страница {page_num}, прокрутка {scroll + 1}/{self.max_scrolls}",
                                int((scroll / self.max_scrolls) * 50))

            cards = self.page.eles('css:div[data-testid="offer-card"]')

            for card in cards:
                result = self.parse_card(card)
                if result:
                    self.results.append(result)
                    if progress_callback:
                        progress_callback(f"Найдено: {result['title']} | {result['price']}",
                                        int((scroll / self.max_scrolls) * 50 +
                                            (len(self.results) / self.max_results) * 50))

                if len(self.results) >= self.max_results:
                    return True

            if len(self.results) >= self.max_results:
                return True

            self.page.scroll.to_bottom()
            time.sleep(2)

        return False

    def parse(self, url="https://ekb.cian.ru/snyat-kvartiru/", progress_callback=None):

        if not self.page:
            if not self.setup_browser():
                return []

        try:
            current_url = url
            page_num = 1
            max_pages = 20

            if progress_callback:
                progress_callback(f"Открываем страницу: {current_url}", 0)

            self.page.get(current_url)
            time.sleep(5)

            self.results = []
            self.seen_links = set()

            while page_num <= max_pages and len(self.results) < self.max_results:
                limit_reached = self.parse_page(progress_callback, page_num)

                if limit_reached:
                    if progress_callback:
                        progress_callback(f"Достигнут лимит объявлений ({self.max_results})", 100)
                    break

                if progress_callback:
                    progress_callback(f"Ищем кнопку 'Дальше' на странице {page_num}...",
                                    int((page_num / max_pages) * 90))

                next_button = self.find_next_button()

                if not next_button:
                    if progress_callback:
                        progress_callback(f"Кнопка 'Дальше' не найдена. Парсинг завершён.", 100)
                    break

                if progress_callback:
                    progress_callback(f"Переход на страницу {page_num + 1}...",
                                    int((page_num / max_pages) * 90))

                try:
                    next_button.click()
                    page_num += 1
                    time.sleep(4)

                    new_url = self.page.url
                    if progress_callback:
                        progress_callback(f"Перешли на: {new_url}",
                                        int((page_num / max_pages) * 90))
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Ошибка при переходе на следующую страницу: {e}", -1)
                    break

            if progress_callback:
                progress_callback(f"Парсинг завершён! Найдено: {len(self.results)} объявлений", 100)

            return self.results

        except Exception as e:
            if progress_callback:
                progress_callback(f"Ошибка: {e}", -1)
            return []

    def save_to_text(self, results=None, filename=None):
        if results is None:
            results = self.results

        if not results:
            return None

        if filename is None:
            filename = f"cian_snyat_kvartiru_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=== СВОДНАЯ ТАБЛИЦА ЦИАН (snyat-kvartiru) ===\n")
                f.write(f"Дата парсинга: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write(f"Всего найдено: {len(results)} объявлений\n\n")
                f.write("-" * 120 + "\n")

                for i, r in enumerate(results, 1):
                    f.write(f"{i:2d}. {r['title']}\n")
                    f.write(f"    {r['subtitle']}\n")
                    f.write(f"    Цена: {r['price']}\n")
                    if r['price_info']:
                        f.write(f"    Условия: {r['price_info']}\n")
                    f.write(f"    Адрес: {r['address']}\n")
                    f.write(f"    Ссылка: {r['link']}\n")
                    f.write(f"    Описание:\n    {r['description'][:500]}...\n")
                    f.write(f"    Фото ({len(r['images'])} шт.):\n")
                    for idx, img in enumerate(r['images'][:5], 1):
                        f.write(f"       {idx:2d}. {img}\n")
                    if len(r['images']) > 5:
                        f.write(f"       ... и ещё {len(r['images'])-5} фото\n")
                    f.write("-" * 120 + "\n")

            return filename
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            return None

    def save_to_json(self, results=None, filename=None):
        if results is None:
            results = self.results

        if not results:
            return None

        if filename is None:
            filename = f"cian_snyat_kvartiru_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return filename
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")
            return None

    def close(self):

        if self.page:
            try:
                self.page.quit()
            except:
                pass