
import sys
import os
import ssl
import certifi
import urllib.request

def fix_ssl_before_import():
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl_context)
        )
        urllib.request.install_opener(opener)
        print("SSL fix applied successfully")
    except Exception as e:
        print(f"Warning: Could not apply SSL fix: {e}")

        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            print("Using unverified SSL context as fallback")
        except:
            pass


fix_ssl_before_import()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui_interface import main

if __name__ == "__main__":
    print("Запуск парсера ЦИАН...")
    main()