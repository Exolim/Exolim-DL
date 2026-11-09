#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exolim Downloader — терминальный загрузчик медиа.

YouTube, SoundCloud, TikTok, Instagram, VK и ещё ~1800 сайтов (yt-dlp).
Интерактивный интерфейс: выбор качества, выбор видео из плейлиста.
"""

import os
import shutil
import sys

import yt_dlp
from yt_dlp.utils import DownloadError

if os.name == "nt":
    os.system("chcp 65001 >nul")  # UTF-8 в консоли
    os.system("")  # включаем ANSI-цвета в консоли Windows

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ------------------------------------------------------------------
# Оформление
# ------------------------------------------------------------------

C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
    "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
}

BANNER = r"""
 ________   ______  _      _____ __  __
|  ____\ \ / / __ \| |    |_   _|  \/  |
| |__   \ V / |  | | |      | | | \  / |
|  __|   > <| |  | | |      | | | |\/| |
| |____ / . \ |__| | |____ _| |_| |  | |
|______/_/ \_\____/|______|_____|_|  |_|

 ___   _____      ___  _ _    ___   _   ___  ___ ___
|   \ / _ \ \    / / \| | |  / _ \ /_\ |   \| __| _ \
| |) | (_) \ \/\/ /| .` | |_| (_) / _ \| |) | _||   /
|___/ \___/ \_/\_/ |_|\_|____\___/_/ \_\___/|___|_|_\

      youtube • soundcloud • tiktok • instagram • vk • ещё ~1800 сайтов
"""

OUT_DIR = "downloads"
AUTH = {}  # сюда кладём cookies-опции после запроса у пользователя

BROWSERS = {"chrome", "firefox", "edge", "brave", "opera", "vivaldi", "chromium", "safari"}

# ------------------------------------------------------------------
# Утилиты
# ------------------------------------------------------------------

def find_ffmpeg_dir():
    """Ищем ffmpeg: рядом с exe/скриптом, в PATH, в imageio-ffmpeg."""
    candidates = []
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidates += [
            os.path.join(base, "ffmpeg.exe"),
            os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
        ]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(here, "ffmpeg.exe"))

    which = shutil.which("ffmpeg")
    if which:
        candidates.append(which)

    for path in candidates:
        if path and os.path.exists(path):
            return os.path.dirname(os.path.abspath(path))

    try:
        import imageio_ffmpeg
        return os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None


def fmt_size(n):
    if not n:
        return ""
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return f"{n:.1f} {unit}".replace(".0 ", " ")
        n /= 1024


def fmt_speed(bps):
    return fmt_size(bps) + "/с" if bps else ""


def fmt_eta(sec):
    if not sec:
        return ""
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_dur(sec):
    if not sec:
        return ""
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def progress_hook(d):
    status = d.get("status")
    if status == "finished":
        print()
        return
    if status != "downloading":
        return

    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
    done = d.get("downloaded_bytes") or 0
    pct = done * 100 / total if total else 0.0
    speed = d.get("speed") or 0
    eta = d.get("eta")

    name = os.path.basename(d.get("filename") or "")[:42]
    line = (
        f"\r{C['cyan']}{name}{C['reset']} "
        f"{C['bold']}{pct:5.1f}%{C['reset']}  "
        f"{C['dim']}{fmt_speed(speed)}"
    )
    if eta:
        line += f"  ETA {fmt_eta(eta)}"
    if total:
        line += f"  {C['dim']}({fmt_size(done)}/{fmt_size(total)}){C['reset']}"
    print(line, end="", flush=True)


# ------------------------------------------------------------------
# yt-dlp опции
# ------------------------------------------------------------------

def base_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": False,
        "windowsfilenames": True,
        "restrictfilenames": False,
        "continuedl": True,
        "retries": 10,
        "fragment_retries": 10,
        "writethumbnail": True,
        "progress_hooks": [progress_hook],
        "outtmpl": os.path.join(OUT_DIR, "%(title)s [%(id)s].%(ext)s"),
    }
    ff_dir = find_ffmpeg_dir()
    if ff_dir:
        opts["ffmpeg_location"] = ff_dir
    opts.update(AUTH)
    return opts


def download(urls, fmt, to_mp3):
    opts = base_opts()
    opts["format"] = fmt
    if to_mp3:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }]
    errors = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        for u in urls:
            try:
                ydl.download([u])
            except DownloadError as e:
                errors.append(e)
                print(f"\n{C['red']}Пропущено: {e}{C['reset']}")
    if errors and len(urls) == 1:
        raise errors[0]


# ------------------------------------------------------------------
# Определение сайта и меню форматов
# ------------------------------------------------------------------

def site_key(info):
    extractor = (info.get("extractor_key") or "").lower()
    if "youtube" in extractor:
        return "youtube"
    if "soundcloud" in extractor:
        return "soundcloud"
    if "tiktok" in extractor:
        return "tiktok"
    return "generic"


# (подпись, формат yt-dlp, конвертировать в mp3?)
MENUS = {
    "youtube": [
        ("MP4  •  2160p (4K)",            "bestvideo[height<=2160]+bestaudio/best", False),
        ("MP4  •  1440p",                 "bestvideo[height<=1440]+bestaudio/best", False),
        ("MP4  •  1080p",                 "bestvideo[height<=1080]+bestaudio/best", False),
        ("MP4  •  720p",                  "bestvideo[height<=720]+bestaudio/best",  False),
        ("MP4  •  480p",                  "bestvideo[height<=480]+bestaudio/best",  False),
        ("MP4  •  360p",                  "bestvideo[height<=360]+bestaudio/best",  False),
        ("Лучшее качество (без лимита)",  "bestvideo*+bestaudio/best",              False),
        ("MP3  •  аудио",                 "bestaudio/best",                        True),
    ],
    "soundcloud": [
        ("MP3  •  аудио (320 kbps)",      "bestaudio/best",          True),
        ("Оригинал  •  лучшее качество",  "best",                     False),
        ("Видео  •  если доступно",       "bestvideo*+bestaudio/best", False),
        ("Аудио  •  исходный формат",    "bestaudio/best",           False),
    ],
    "tiktok": [
        ("Видео  •  лучшее качество",    "bestvideo*+bestaudio/best", False),
        ("Видео  •  оригинал",           "best",                     False),
        ("MP3  •  аудио",                "bestaudio/best",           True),
    ],
    "generic": [
        ("Лучшее качество  •  видео+аудио", "bestvideo*+bestaudio/best", False),
        ("MP3  •  аудио",                   "bestaudio/best",            True),
        ("Аудио  •  исходный формат",       "bestaudio/best",            False),
        ("Оригинал  •  best",               "best",                      False),
        ("Свой формат yt-dlp…",             None,                        False),
    ],
}

SITE_NAMES = {
    "youtube": "YouTube",
    "soundcloud": "SoundCloud",
    "tiktok": "TikTok",
    "generic": "сайт",
}


# ------------------------------------------------------------------
# Интерактивные элементы
# ------------------------------------------------------------------

def ask(prompt):
    return input(f"{C['cyan']}{prompt}{C['reset']} ").strip()


def choose(title, options):
    print(f"\n{C['bold']}{title}{C['reset']}")
    for i, label in enumerate(options, 1):
        print(f"  {C['cyan']}{i}{C['reset']}) {label}")
    while True:
        s = ask(">")
        if s.isdigit() and 1 <= int(s) <= len(options):
            return int(s) - 1
        print(f"{C['red']}Введи число от 1 до {len(options)}{C['reset']}")


def parse_selection(text, total):
    """Парсит 'all', '1,3,5', '1-10', '2-4,7'. Возвращает список индексов или None."""
    text = text.strip().lower()
    if text in ("all", "а", "все", "*", ""):
        return list(range(total))
    idx = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                idx.extend(range(int(a) - 1, int(b)))
            except ValueError:
                return None
        elif part.isdigit():
            idx.append(int(part) - 1)
        else:
            return None
    result = sorted({i for i in idx if 0 <= i < total})
    return result or None


def ask_cookies():
    print(f"\n{C['yellow']}Похоже, нужен доступ к приватному/возрастному контенту.{C['reset']}")
    print("Введи путь к файлу cookies (Netscape) или имя браузера:")
    print(f"  {', '.join(sorted(BROWSERS))}")
    s = ask("> (Enter — пропустить)")
    if not s:
        return
    if s.lower() in BROWSERS:
        AUTH["cookiesfrombrowser"] = (s.lower(),)
    elif os.path.exists(s):
        AUTH["cookiefile"] = s
    else:
        print(f"{C['red']}Файл не найден, продолжаю без cookies.{C['reset']}")


def looks_like_auth_error(msg):
    low = msg.lower()
    return any(k in low for k in (
        "sign in", "private", "cookie", "login", "members-only",
        "age", "confirm you're not a bot", "403", "unauthorized",
    ))


# ------------------------------------------------------------------
# Основная логика
# ------------------------------------------------------------------

def entry_url(entry, parent_key=""):
    """Достаёт прямую ссылку из плоской (flat) записи плейлиста."""
    for key in ("webpage_url", "url"):
        u = entry.get(key) or ""
        if u.startswith("http"):
            return u

    ie = (entry.get("ie_key") or entry.get("extractor_key") or parent_key or "").lower()
    vid = entry.get("id") or entry.get("url") or ""
    if not vid:
        return ""
    if "youtube" in ie:
        return f"https://www.youtube.com/watch?v={vid}"
    if "soundcloud" in ie:
        return f"https://soundcloud.com/{vid}"
    if "tiktok" in ie:
        return f"https://www.tiktok.com/video/{vid}" if vid.isdigit() else f"https://www.tiktok.com/{vid}"
    return ""


def show_video_info(info):
    title = info.get("title") or "?"
    dur = fmt_dur(info.get("duration"))
    author = info.get("uploader") or info.get("channel") or info.get("creator") or ""
    site = SITE_NAMES.get(site_key(info), "?")
    print(f"\n{C['green']}{C['bold']}▶ {title}{C['reset']}")
    meta = f"   {C['dim']}{site}"
    if dur:
        meta += f"  •  {dur}"
    if author:
        meta += f"  •  {author}"
    print(meta)


def handle_playlist(info):
    """Возвращает (site, urls) или None, если плейлист пуст."""
    entries = [e for e in (info.get("entries") or []) if e]
    if not entries:
        print(f"{C['yellow']}Плейлист пуст или недоступен.{C['reset']}")
        return None

    title = info.get("title") or "Плейлист"
    print(f"\n{C['bold']}{title}{C['reset']}  {C['dim']}— {len(entries)} видео{C['reset']}")

    for i, e in enumerate(entries, 1):
        t = (e.get("title") or "?")[:60]
        d = fmt_dur(e.get("duration"))
        print(f"  {C['cyan']}{i:>3}{C['reset']}. {t:<62} {C['dim']}{d}{C['reset']}")

    while True:
        s = ask(f"\nВыбор ({len(entries)} видео) — номера, диапазон или 'all'")
        sel = parse_selection(s, len(entries))
        if sel:
            break
        print(f"{C['red']}Неверный ввод. Пример: 1,3,5 или 1-10 или all{C['reset']}")

    parent_key = info.get("extractor_key") or ""
    urls = [entry_url(entries[i], parent_key) for i in sel]
    urls = [u for u in urls if u]
    print(f"{C['green']}Выбрано: {len(urls)} видео{C['reset']}")
    return site_key(info), urls


def pick_format(site):
    options = MENUS.get(site, MENUS["generic"])
    labels = [o[0] for o in options]
    idx = choose(f"Формат для {SITE_NAMES.get(site, 'сайта')}", labels)

    fmt, to_mp3 = options[idx][1], options[idx][2]
    if fmt is None:  # свой формат
        fmt = ask("Формат yt-dlp (напр. bestvideo[height<=1080]+bestaudio/best):")
        if not fmt:
            return None, None
    return fmt, to_mp3


def process_url(url):
    opts = base_opts()
    opts["extract_flat"] = "in_playlist"  # плейлист — только список, без распаковки
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        print(f"{C['red']}Не удалось получить информацию по ссылке.{C['reset']}")
        return

    # Плейлист или одиночное видео
    entries = info.get("entries")
    if info.get("_type") == "playlist" or entries:
        result = handle_playlist(info)
        if not result:
            return
        site, urls = result
    else:
        show_video_info(info)
        site, urls = site_key(info), [url]

    fmt, to_mp3 = pick_format(site)
    if fmt is None:
        return

    print(f"\n{C['green']}Скачиваю {len(urls)} файл(ов)…{C['reset']}  {C['dim']}→ {OUT_DIR}/{C['reset']}")
    download(urls, fmt, to_mp3)
    print(f"{C['green']}{C['bold']}Готово!{C['reset']} Файлы в папке {C['cyan']}{OUT_DIR}/{C['reset']}")


# ------------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    if os.name == "nt":
        os.system("cls")
    print(BANNER)

    ff = find_ffmpeg_dir()
    if not ff:
        print(f"{C['yellow']}Внимание: ffmpeg не найден — MP3 и склейка видео+аудио "
              f"могут не работать. Установи ffmpeg или запусти exe рядом с ffmpeg.exe.{C['reset']}")

    print(f"{C['dim']}Вставь ссылку и нажми Enter. 'q' — выход.{C['reset']}\n")

    while True:
        url = ask("Ссылка >")
        if not url:
            continue
        if url.lower() in ("q", "quit", "exit", "выход"):
            break

        try:
            process_url(url)
        except DownloadError as e:
            msg = str(e)
            if looks_like_auth_error(msg) and not AUTH:
                ask_cookies()
                if AUTH:
                    try:
                        process_url(url)
                    except DownloadError as e2:
                        print(f"\n{C['red']}Ошибка: {e2}{C['reset']}")
            else:
                print(f"\n{C['red']}Ошибка: {msg}{C['reset']}")
        except KeyboardInterrupt:
            print(f"\n{C['yellow']}Отменено.{C['reset']}")
        except Exception as e:
            print(f"\n{C['red']}Ошибка: {e}{C['reset']}")

        input(f"\n{C['dim']}Enter — продолжить …{C['reset']}")

    print(f"\n{C['magenta']}До встречи!{C['reset']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # чтобы окно exe не закрывалось при падении
        print(f"\n{C['red']}Критическая ошибка: {e}{C['reset']}")
        try:
            input("Enter для выхода")
        except EOFError:
            pass
        sys.exit(1)
