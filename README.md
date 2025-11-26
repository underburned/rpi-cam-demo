# rpi-cam-demo

Демонстрационное ПО для работы с Raspberry Pi Camera Module 3 с использованием GStreamer.  
PyQt5 необходим для реализации асинхронного взаимодействия (сигнал-слот) и отображения кадров в отдельном потоке.

## Установка

### Обновление библиотек

```bash
sudo apt update
sudo apt upgrade
```

### Зависимости

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

Создание:

```bash
python3 -m venv --system-site-packages ~/.virtualenvs/rpi-cam-demo
```

> `--system-site-packages` означает, что будет создано виртуальное окружение с пробросом библиотек системного интерпретатора.

Активация (в терминале на малине или в терминале SSH):

```bash
source ~/.virtualenvs/rpi-cam-demo/bin/activate
```

В терминале слева от юзер@хост должно появиться название виртуального окружения:

```bash
(rpi-cam-demo) ud@udrpi5:~ $
```

В IDE в качестве интерпретатора задать:

```
/home/pi/.virtualenvs/rpi-cam-demo/bin/python3.11
```

### Библиотеки Python

#### Обновление `pip`

```bash
pip install --upgrade pip
```

#### Зависимости проекта

Для интроспекции типов PyGobject (GStreamer) необходимо установить `pygobject-stubs`:

```bash
pip3 install pygobject-stubs
```

OpenCV:

```bash
pip3 install opencv-python
```

PyQt5:

```bash
pip3 install PyQt5 PyQt5-stubs
```

## Запуск

Активация виртуального окружения:

```bash
source ~/.virtualenvs/rpi-cam-demo/bin/activate
```

Запуск:

```bash
python3 rpi_cam_demo.py
```

В коде при желании поменять (по умолчанию после получения 100 кадров с камеры приложение завершает работу):

```python
self.width = 1024
self.height = 768
self.fps = 30
self.frame_num = 100
```