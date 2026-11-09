# Exolim Downloader

Терминальный загрузчик медиа с интерактивным меню. YouTube, SoundCloud, TikTok,
Instagram, VK, Twitter/X и ещё ~1800 сайтов — всё через [yt-dlp](https://github.com/yt-dlp/yt-dlp).

При запуске открывается консоль с баннером **EXOLIM DOWNLOADER**: вставляешь
ссылку — программа сама определяет сайт и предлагает нужный формат.

![platform](https://img.shields.io/badge/platform-Windows-blue)
![python](https://img.shields.io/badge/python-3.10%2B-green)
![license](https://img.shields.io/badge/license-MIT-yellow)

## Возможности

- **YouTube** — выбор качества (4K → 360p), MP3, выбор отдельных видео из плейлиста
- **SoundCloud** — MP3 320 kbps, оригинал, видео (если есть)
- **TikTok** — видео без водяного знака, MP3
- **Плейлисты** — нумерованный список, выбор через `1,3,5` / `1-10` / `all`
- **Прогресс-бар** — процент, скорость, ETA
- **Cookies** — при блокировке/приватном контенте спросит браузер или файл cookies
- **Докачка** — при обрыве продолжит с места разрыва
- **ffmpeg из коробки** — в exe встроен через imageio-ffmpeg (MP3 и склейка работают без установки)

## Запуск exe

Скачай `Exolim-DL.exe` из [Releases](../../releases) и запусти — откроется
терминал с интерфейсом. Файлы сохраняются в `downloads/` рядом с exe.

## Запуск из исходников

```bash
git clone https://github.com/<you>/Exolim-DL.git
cd Exolim-DL
pip install -r requirements.txt
python src/exolim.py
```

## Сборка exe

```bat
build.bat
```

Результат: `releases\Exolim-DL.exe` (onefile, ~консольное приложение).

## Использование

```
Ссылка > https://www.youtube.com/watch?v=...

▶ Название видео
   YouTube  •  3:33  •  Автор

Формат для YouTube
  1) MP4  •  2160p (4K)
  ...
  8) MP3  •  аудио
> 4
```

Для плейлиста после ссылки покажется список — введи номера через запятую,
диапазон (`1-10`) или `all`.

## Структура

```
Exolim-DL/
├── src/exolim.py      # весь код (один файл)
├── releases/          # сюда build.bat кладёт exe
├── requirements.txt
├── build.bat
├── LICENSE            # MIT
└── README.md
```

## Примечания

- YouTube может временно ограничивать IP — тогда программа сама предложит ввести
  cookies браузера (`chrome`, `firefox`, `edge`...) или путь к файлу cookies.
- Для приватных/возрастных видео нужен вход в аккаунт через cookies.
- Некоторые сайты (например, SoundCloud) могут временно блокировать yt-dlp —
  помогает `yt-dlp -U` (обновление) или cookies.
