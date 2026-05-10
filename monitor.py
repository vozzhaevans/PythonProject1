import json
import os
import time
import threading
from datetime import datetime

from cian_parser import CianParser
from email_notifier import send_change_notification


class CianMonitor:

    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_results = None
        self.history_file = "cian_monitor_history.json"
        self.parser = None

    def load_last_results(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.last_results = data.get("results", [])
                    return self.last_results
            except:
                pass
        return []

    def save_results(self, results):
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "count": len(results),
                "results": results[:100]
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def compare_results(self, new_results):
        if not self.last_results:
            return {"new": len(new_results), "removed": 0, "changed": 0,
                   "details": "Первый запуск мониторинга"}

        last_links = {r['link'] for r in self.last_results}
        new_links = {r['link'] for r in new_results}

        new_ads = [r for r in new_results if r['link'] not in last_links]
        removed_ads = [r for r in self.last_results if r['link'] not in new_links]

        changes = []
        if new_ads:
            changes.append(f" Новых объявлений: {len(new_ads)}")
        if removed_ads:
            changes.append(f" Снятых объявлений: {len(removed_ads)}")

        return {
            "new": len(new_ads),
            "removed": len(removed_ads),
            "changed": len(new_ads) + len(removed_ads),
            "details": "\n".join(changes) if changes else "Изменений не обнаружено"
        }

    def run_monitoring(self, url, interval_seconds=3600, max_results=30,
                       email_settings=None, notify_always=False, progress_callback=None):
        self.is_monitoring = True
        self.load_last_results()

        while self.is_monitoring:
            try:
                if progress_callback:
                    progress_callback(f"[{datetime.now().strftime('%H:%M')}] Запуск парсинга...", 10)

                self.parser = CianParser(headless=False, max_scrolls=1, max_results=max_results)

                def cb(message, progress):
                    if progress_callback:
                        progress_callback(message, progress)

                results = self.parser.parse(url, cb)

                if results:
                    comparison = self.compare_results(results)

                    if email_settings and email_settings.get('to'):
                        if notify_always or comparison["changed"] > 0:
                            send_change_notification(
                                to_email=email_settings['to'],
                                from_email=email_settings['from'],
                                password=email_settings['password'],
                                new_count=len(results),
                                changes=comparison["details"]
                            )

                    self.save_results(results)
                    self.last_results = results

                    if progress_callback:
                        status = "Уведомление отправлено" if (notify_always or comparison["changed"] > 0) else "Без изменений"
                        progress_callback(
                            f" Найдено: {len(results)} | {status}", 100
                        )
                else:
                    if progress_callback:
                        progress_callback(" Объявления не найдены", 100)

            except Exception as e:
                if progress_callback:
                    progress_callback(f" Ошибка: {e}", -1)
                print(f"Monitor error: {e}")

            finally:
                if self.parser:
                    try:
                        self.parser.close()
                    except:
                        pass

            for _ in range(interval_seconds // 10):
                if not self.is_monitoring:
                    break
                time.sleep(10)

    def start(self, url, interval_seconds=3600, max_results=30,
              email_settings=None, notify_always=False, progress_callback=None):
        if self.is_monitoring:
            return False

        self.monitor_thread = threading.Thread(
            target=self.run_monitoring,
            args=(url, interval_seconds, max_results, email_settings, notify_always, progress_callback),
            daemon=True
        )
        self.monitor_thread.start()
        return True

    def stop(self):
        self.is_monitoring = False
        if self.parser:
            try:
                self.parser.close()
            except:
                pass