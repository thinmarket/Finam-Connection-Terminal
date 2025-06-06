# Finam-Connection-Terminal

Графический интерфейс для работы с TRANSAQ Connector через официальную DLL (`txmlconnector64.dll`) от Финам.

## Требования для работы

### 1. Библиотека Transaq
Необходимо скачать файл `txmlconnector64.dll` с сайта брокера:  
[Скачать DLL](https://www.finam.ru/howtotrade/soft/tconnector/)

### 2. Данные для подключения
Требуется получить у брокера:
- Логин
- Пароль для Transaq Connector

## Версии программы

### `terminal_connector_j.py` 
Версия, которая:
- Выводит сообщения в интерфейс программы после соединения.

### `terminal_connector_t.py`
Версия, которая:
- Логирует только важные события в интерфейс после соединения.
- Выводит все сырые данные в терминал VSC.

## 🔑 Генерация ключа шифрования

Перед запуском откройте скрипт:

**generate_key.py**

Запустите и Скопируйте сгенерированный ключ

Вставьте его в файлы terminal_connector_j.py и terminal_connector_t.py в нужнуе место.

### **Как получить доступ у брокера**
Авторизуйтесь в личном кабинете Финам

Перейдите в раздел «Торговля» → «Управление терминалами»

Нажмите «Получение новой ИТС»

Выберите «Transaq Connector»

Укажите номер телефона для SMS-пароля

Выберите нужный торговый счет

Нажмите «Подключить», затем «Подписать» (подтвердите SMS-кодом)

Логин можно найти в «Отчётность» → «Журнал уведомлений»

Пароль придет в SMS

### **История проекта**
 
В одном из моих проектов процесс соединения с брокером разделен не несколько модулей, так же отдельные модули для подписок на данные. 

Тут решил воспроизвести процесс соединения в одном файле, с которым можно работать.   

**После установки соединения вы можете:**

Подписываться на нужные данные (рекоменую ознакомиться с "Руководством пользователя TRANSAQ Connector" на сайте брокера )

Обрабатывать их в своих программах

Строить собственные торговые системы

Текущая версия предоставляет базовый функционал для подключения, который можно расширять под свои нужды.

⚠️ Важно: 

Не забудьте заменить стандартный ключ шифрования на собственный! 

Не забудьте разместить файл (txmlconnector64.dll) в одной директории. 

### *Основные зависимости для работы terminal_connector_j.py и terminal_connector_t.py*

PyQt5==5.15.9             # Для графического интерфейса

cryptography==41.0.7       # Для шифрования паролей (Fernet)

Видео про программы https://youtu.be/7iEggXmUTNw?feature=shared 
