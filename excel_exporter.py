import pandas as pd
from datetime import datetime
import os

class ExcelExporter:

    def __init__(self):
        self.default_prefix = "Cian_parser"

    def export_to_excel(self, results, filename_prefix=None, include_datetime=True):

        if not results:
            return None

        if filename_prefix is None or filename_prefix.strip() == "":
            filename_prefix = self.default_prefix

        if include_datetime:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.xlsx"
        else:
            filename = f"{filename_prefix}.xlsx"

        try:

            data = []
            for item in results:
                data.append({
                    "№": len(data) + 1,
                    "Заголовок": item.get("title", ""),
                    "Подзаголовок": item.get("subtitle", ""),
                    "Цена": item.get("price", ""),
                    "Доп. информация о цене": item.get("price_info", ""),
                    "Адрес": item.get("address", ""),
                    "Комнат": item.get("rooms", 0),
                    "Площадь (м²)": item.get("area", 0),
                    "Этаж": item.get("floor", ""),
                    "Описание": item.get("description", ""),
                    "Ссылка": item.get("link", ""),
                    "Количество фото": len(item.get("images", [])),
                })

            df = pd.DataFrame(data)

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="ЦИАН_Аренда")

                worksheet = writer.sheets["ЦИАН_Аренда"]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    ) + 2
                    worksheet.column_dimensions[worksheet.cell(row=1, column=idx + 1).column_letter].width = min(
                        max_length, 50)

            return os.path.abspath(filename)

        except Exception as e:
            print(f"Ошибка при экспорте в Excel: {e}")
            return None


def export_results_to_excel(results, prefix="Cian_parser", include_datetime=True):
    exporter = ExcelExporter()
    return exporter.export_to_excel(results, prefix, include_datetime)