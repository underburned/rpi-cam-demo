# rpi-cam-demo

Демонстрационное ПО для работы с Raspberry Pi Camera Module 3 с использованием GStreamer.  
PyQt5 необходим для реализации асинхронного взаимодействия (сигнал-слот) и отображения кадров в отдельном потоке.

> Протестировано на RPi OS от 13.04.2026.

## Установка

### Обновление библиотек

```bash
sudo apt update
sudo apt upgrade
```

### Менеджер пакетов UV

[UV](https://github.com/astral-sh/uv) ([сайт](https://astral.sh/)) &ndash; это быстрый пакетный менеджер Python, написанный на Rust. Разработан как замена для `pip`, `pip-tools` и других утилит.

Подробнее: [UV. Обзор пакетного менеджера Python @ Хабр](https://habr.com/ru/articles/828016/).

Установка (скачивание bash-скрипта `uv-installer.sh` и его запуск):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Пример вывода результата выполнения команды:

```bash
ud@udrpi5:~/Downloads $ curl -LsSf https://astral.sh/uv/install.sh | sh
downloading uv 0.11.6 aarch64-unknown-linux-gnu
installing to /home/ud/.local/bin
  uv
  uvx
everything's installed!

To add $HOME/.local/bin to your PATH, either restart your shell or run:

    source $HOME/.local/bin/env (sh, bash, zsh)
    source $HOME/.local/bin/env.fish (fish)
```

Считываем заново переменные среды в текущей сессии:

```bash
source $HOME/.local/bin/env
```

### Зависимости

```bash
sudo apt install cmake libcairo2-dev libgirepository-2.0-dev libgtk2.0-dev pkg-config
```

#### GStreamer

GStreamer и плагины:

```bash
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl \
gstreamer1.0-gtk3 gstreamer1.0-pulseaudio
sudo apt install gstreamer1.0-libcamera
```

### Виртуальное окружение WIP

Виртуальное окружение (*virtual environment*) &ndash; создание изолированного пространства для работы над конкретным проектом, что позволяет управлять его зависимостями, не влияя на другие проекты или глобальную установку Python. Физически представляет собой отдельную директорию с копиями интерпретатора и менеджера пакетов и скриптом активации виртуального окружения.

Начиная с Python 3.3, библиотека языка включает в себя модуль `venv`, который признан наиболее удобным и предпочтительным методом для этой задачи.

Создание виртуального окружения `rpi-cam-demo` (по умолчанию создастся директория в *текущей папке*, поэтому укажем абсолютный путь `~/.venvs/rpi-cam-demo`):

```commandline
uv venv ~/.venvs/rpi-cam-demo
```

Вывод:

```commandline
ud@udrpi5:~/Downloads $ uv venv ~/.venvs/rpi-cam-demo
Using CPython 3.13.5 interpreter at: /usr/bin/python
Creating virtual environment at: /home/ud/.venvs/rpi-cam-demo
Activate with: source /home/ud/.venvs/rpi-cam-demo/bin/activate
```

Для активации достаточно в терминале ввести:

```commandline
source ~/.venvs/rpi-cam-demo/bin/activate
```

и после активации установить необходимые библиотеки.

В терминале слева от юзер@хост должно появиться название виртуального окружения:

```bash
(rpi-cam-demo) ud@udrpi5:~ $
```

В IDE в качестве интерпретатора задать:

```
/home/<имя юзера>/.venvs/rpi-cam-demo/bin/python3.13
```

### Библиотеки Python

#### Зависимости проекта

Для интроспекции типов PyGobject (GStreamer) необходимо установить `pygobject-stubs`:

```bash
uv pip install pycairo pygobject-stubs
```

OpenCV:

```bash
uv pip install opencv-python
```

PyQt5:

```bash
uv pip install PyQt6 PyQt6-stubs
```

## Запуск

Активация виртуального окружения:

```bash
source ~/.venvs/rpi-cam-demo/bin/activate
```

Запуск:

```bash
python3 rpi_cam_demo.py
```

В коде при желании поменять (по умолчанию после получения 100 кадров с камеры приложение завершает работу):

```python
self.width = 1536
self.height = 864
self.fps = 30
self.frame_num = 100
```