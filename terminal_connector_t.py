# Импортируем необходимые библиотеки
import os  # Для работы с файлами и путями
import logging  # Для ведения логов (записей о работе программы)
import ctypes  # Для работы с DLL (библиотеками Windows)
import xml.etree.ElementTree as ET  # Для разбора XML-данных
from cryptography.fernet import Fernet  # Для шифрования паролей
from datetime import datetime  # Для работы с датой и временем
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QHBoxLayout, QComboBox, QFormLayout, QTextEdit, QApplication)  # Элементы интерфейса
from PyQt5.QtCore import QObject, pyqtSignal  # Сигналы для связи между компонентами
from PyQt5.QtGui import QIcon  # Иконки для кнопок
import sys  # Для работы с системными функциями (например, выход из программы)

# Настраиваем логгер для вывода в терминал VSC (Visual Studio Code)
logging.basicConfig(
    level=logging.INFO,  # Уровень INFO (вывод информационных сообщений)
    format='%(asctime)s - %(message)s',  # Формат записи: время + сообщение
    handlers=[logging.StreamHandler()]  # Вывод в консоль
)
logger = logging.getLogger(__name__)  # Создаем логгер с именем текущего модуля

# Ключ шифрования для паролей (ЗАМЕНИТЕ НА СВОЙ, сгенерированный через generate_key.py!)
KEY = b'ваш сгенерированный ключ разработчика'
cipher_suite = Fernet(KEY)  # Объект для шифрования/расшифровки

class Log:
    """Класс для ведения лог-файла (только важные сообщения)"""
    def __init__(self):
        self.log_flag = False  # Флаг, разрешена ли запись логов
        self.log_file = None   # Файл, куда пишутся логи

    def write_log(self, log_str):
        """Записывает строку в лог-файл (только важные сообщения)"""
        if self.log_flag and self.log_file:  # Если запись разрешена и файл открыт
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Текущее время (часы:минуты:секунды.миллисекунды)
            self.log_file.write(f"{timestamp} {log_str}\n")  # Пишем строку в файл
            self.log_file.flush()  # Сразу сохраняем изменения

    def start_logging(self, path):
        """Начинает запись логов в указанный файл"""
        if not os.path.exists(path):  # Если файла нет — создаем пустой
            open(path, 'w').close()
        self.log_file = open(path, 'a')  # Открываем файл в режиме добавления (append)
        self.log_flag = True  # Разрешаем запись
        self.write_log("START LOGGING")  # Пишем первую запись

    def stop_logging(self):
        """Останавливает запись логов"""
        if self.log_flag and self.log_file:  # Если запись была активна
            self.write_log("STOP LOGGING")  # Пишем последнюю запись
            self.log_file.close()  # Закрываем файл
        self.log_flag = False  # Запрещаем дальнейшую запись

class ConnectorSignals(QObject):
    """Сигналы для работы с соединением (только важные события)"""
    connection_status_changed = pyqtSignal(str)  # Сигнал об изменении статуса соединения
    error_occurred = pyqtSignal(str)  # Сигнал об ошибке
    important_data_received = pyqtSignal(str)  # Сигнал о получении важных данных (не все данные, а только ключевые)

class Connector:
    """Основной класс для работы с Transaq Connector (версия для разработчиков)"""
    def __init__(self):
        self.signals = ConnectorSignals()  # Создаем объект сигналов
        self.log = Log()  # Создаем логгер
        self._load_dll()  # Загружаем DLL

    def _load_dll(self):
        """Загружает DLL-библиотеку для работы с Transaq"""
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Папка, где лежит программа
        dll_path = os.path.join(script_dir, "txmlconnector64.dll")  # Путь к DLL
        os.environ['PATH'] += os.pathsep + script_dir  # Добавляем путь в системный PATH (чтобы DLL была доступна)

        try:
            self.txml = ctypes.WinDLL(dll_path)  # Загружаем DLL
            logger.info(f"DLL успешно загружена из {dll_path}")  # Пишем в лог
            self._setup_dll_functions()  # Настраиваем функции DLL
            self._setup_callbacks()  # Настраиваем обработчики событий
        except Exception as e:
            logger.error(f"Ошибка при загрузке DLL: {e}")  # Если ошибка — пишем в лог
            raise  # Прерываем выполнение

    def _setup_dll_functions(self):
        """Настраивает типы аргументов и возвращаемых значений для функций DLL"""
        self.CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p)  # Тип callback-функции
        
        # Настройка функций DLL:
        self.txml.SetCallback.argtypes = [self.CALLBACK_TYPE]  # Устанавливаем callback
        self.txml.SetCallback.restype = ctypes.c_bool
        
        self.txml.SendCommand.argtypes = [ctypes.c_char_p]  # Отправка команды
        self.txml.SendCommand.restype = ctypes.c_void_p
        
        self.txml.FreeMemory.argtypes = [ctypes.c_void_p]  # Освобождение памяти
        self.txml.FreeMemory.restype = None
        
        self.txml.Initialize.argtypes = [ctypes.c_char_p, ctypes.c_int]  # Инициализация
        self.txml.Initialize.restype = ctypes.c_void_p
        
        self.txml.UnInitialize.argtypes = []  # Деинициализация
        self.txml.UnInitialize.restype = ctypes.c_void_p

    def _setup_callbacks(self):
        """Настраивает callback-функцию для обработки входящих данных"""
        @self.CALLBACK_TYPE
        def callback(pData):
            try:
                if pData:  # Если данные получены
                    data_ptr = ctypes.cast(pData, ctypes.c_char_p)  # Преобразуем указатель
                    if data_ptr:
                        data = data_ptr.value.decode('utf-8')  # Декодируем строку
                        
                        # Выводим все данные в терминал VSC (первые 200 символов)
                        logger.info(f"Получены данные: {data[:200]}...")  
                        
                        self._handle_data(data)  # Обрабатываем данные
                        self.txml.FreeMemory(pData)  # Освобождаем память
                return True
            except Exception as e:
                logger.error(f"Ошибка в callback: {e}")  # Логируем ошибку
                return False

        self.callback_func = callback  # Сохраняем callback
        
        if not self.txml.SetCallback(self.callback_func):  # Устанавливаем callback
            raise RuntimeError("Не удалось установить callback")  # Если ошибка

    def _handle_data(self, data):
        """Обрабатывает входящие данные и фильтрует только важные сообщения"""
        try:
            root = ET.fromstring(data)  # Пытаемся разобрать XML
            
            # Определяем, какие данные важные:
            is_important = False
            message = ""
            
            if root.tag == "server_status":  # Если это статус сервера
                status = root.get("connected", "unknown")  # Получаем статус
                message = f"Состояние соединения: {status}"
                is_important = True
                self.signals.connection_status_changed.emit(message)  # Отправляем сигнал
            elif root.tag == "error":  # Если это ошибка
                message = f"Ошибка: {root.text}"
                is_important = True
                self.signals.error_occurred.emit(message)  # Отправляем сигнал
            elif root.tag == "result":  # Если это результат команды
                if "success" in root.attrib:  # Если есть атрибут success
                    message = f"Результат команды: {root.attrib['success']}"
                    is_important = True
                else:
                    message = f"Результат: {data[:100]}..."  # Первые 100 символов
                    is_important = True
            
            # Если сообщение важное — записываем в лог и отправляем в интерфейс
            if is_important:
                self.log.write_log(message)
                self.signals.important_data_received.emit(message)
                
        except ET.ParseError:  # Если это не XML
            # Проверяем, содержит ли текст слова "error" или "fail"
            if "error" in data.lower() or "fail" in data.lower():
                self.log.write_log(data[:200])  # Записываем первые 200 символов
                self.signals.important_data_received.emit(data[:200])  # Отправляем в интерфейс

    def send_command(self, command):
        """Отправляет команду на сервер"""
        try:
            cmd_ptr = ctypes.c_char_p(command.encode('utf-8'))  # Преобразуем команду в байты
            result_ptr = self.txml.SendCommand(cmd_ptr)  # Отправляем команду
            
            if result_ptr:  # Если есть ответ
                result = ctypes.cast(result_ptr, ctypes.c_char_p).value.decode('utf-8')  # Декодируем
                self.txml.FreeMemory(result_ptr)  # Освобождаем память
                return result
            return ""  # Если ответа нет
        except Exception as e:
            logger.error(f"Ошибка при отправке команды: {e}")  # Логируем ошибку
            raise  # Прерываем выполнение

    def initialize(self, path, log_level):
        """Инициализирует подключение к серверу"""
        try:
            path_ptr = ctypes.c_char_p(path.encode('utf-8'))  # Путь к конфигурации
            result_ptr = self.txml.Initialize(path_ptr, log_level)  # Инициализация
            
            if result_ptr:
                result = ctypes.cast(result_ptr, ctypes.c_char_p).value.decode('utf-8')  # Ответ
                self.txml.FreeMemory(result_ptr)  # Освобождаем память
                
                log_path = os.path.join(path, "important_messages.log")  # Путь к лог-файлу
                self.log.start_logging(log_path)  # Начинаем запись логов
                
                return result
            return ""
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise

    def uninitialize(self):
        """Отключает соединение с сервером"""
        try:
            result_ptr = self.txml.UnInitialize()  # Деинициализация
            
            if result_ptr:
                result = ctypes.cast(result_ptr, ctypes.c_char_p).value.decode('utf-8')
                self.txml.FreeMemory(result_ptr)
                
                self.log.stop_logging()  # Останавливаем запись логов
                
                return result
            return ""
        except Exception as e:
            logger.error(f"Ошибка деинициализации: {e}")
            raise

    def encrypt_password(self, password):
        """Шифрует пароль"""
        return cipher_suite.encrypt(password.encode()).decode()  # Возвращает зашифрованную строку

    def decrypt_password(self, encrypted_password):
        """Расшифровывает пароль"""
        return cipher_suite.decrypt(encrypted_password.encode()).decode()  # Возвращает расшифрованный пароль

class ConnectionWindow(QDialog):
    """Главное окно программы (версия для разработчиков)"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Соединение с Transaq (Dev Mode)")  # Заголовок окна
        self.setGeometry(370, 240, 920, 660)  # Позиция и размер окна

        self.connector = Connector()  # Создаем объект Connector
        
        # Подключаем сигналы (только важные сообщения):
        self.connector.signals.connection_status_changed.connect(self._add_log_message)
        self.connector.signals.error_occurred.connect(self._add_log_message)
        self.connector.signals.important_data_received.connect(self._add_log_message)

        main_layout = QVBoxLayout()  # Основной макет (вертикальный)
        
        # Форма для ввода данных:
        form_layout = QFormLayout()
        
        # Поля ввода:
        self.login_input = QLineEdit()  # Поле для логина
        self.password_input = QLineEdit()  # Поле для пароля
        self.password_input.setEchoMode(QLineEdit.Password)  # Скрываем пароль
        
        # Кнопка показа пароля:
        self.toggle_password_btn = QPushButton()
        self.toggle_password_btn.setIcon(QIcon("eye_icon.png"))  # Иконка глаза
        self.toggle_password_btn.setCheckable(True)  # Кнопка-переключатель
        self.toggle_password_btn.toggled.connect(self._toggle_password_visibility)  # Обработчик
        
        # Компоновка поля пароля:
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_btn)
        
        # Выбор сервера:
        self.server_combo = QComboBox()
        self.server_combo.addItems([
            "АО «ФИНАМ» Основной адрес",
            "АО «ФИНАМ» Резервный адрес",
            "АО «Банк Финам» Основной адрес",
            "АО «Банк Финам» Резервный адрес"
        ])
        
        # Параметры серверов:
        self.server_params = {
            "АО «ФИНАМ» Основной адрес": {"ip": "tr1.finam.ru", "port": "3900"},
            "АО «ФИНАМ» Резервный адрес": {"ip": "tr2.finam.online", "port": "3900"},
            "АО «Банк Финам» Основной адрес": {"ip": "tr1.finambank.ru", "port": "3324"},
            "АО «Банк Финам» Резервный адрес": {"ip": "tr2.finambank.ru", "port": "3324"},
        }
        
        # Добавляем элементы в форму:
        form_layout.addRow("Логин:", self.login_input)
        form_layout.addRow("Пароль:", password_layout)
        form_layout.addRow("Сервер:", self.server_combo)
        
        # Кнопки управления:
        button_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Стереть")  # Кнопка очистки
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.disconnect_btn = QPushButton("Отключить")  # Кнопка отключения
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)  # По умолчанию выключена
        self.connect_btn = QPushButton("Подключить")  # Кнопка подключения
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.connect_btn)
        
        # Журнал важных сообщений:
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)  # Только для чтения
        self.log_text.setPlaceholderText("Здесь будут отображаться только важные сообщения...")  # Подсказка
        
        # Компоновка интерфейса:
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("Важные сообщения:"))  # Заголовок журнала
        main_layout.addWidget(self.log_text)
        
        self.setLayout(main_layout)  # Устанавливаем макет
        
        self._load_saved_credentials()  # Загружаем сохраненные данные

    def _toggle_password_visibility(self, checked):
        """Показывает или скрывает пароль"""
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def _load_saved_credentials(self):
        """Загружает сохраненные логин и пароль из файла"""
        config_path = os.path.join(os.path.dirname(__file__), "config.xml")
        if os.path.exists(config_path):
            try:
                tree = ET.parse(config_path)  # Читаем XML
                root = tree.getroot()
                
                login = root.find("login").text  # Логин
                password = self.connector.decrypt_password(root.find("password").text)  # Пароль
                host = root.find("host").text  # Адрес сервера
                port = root.find("port").text  # Порт
                
                self.login_input.setText(login)  # Заполняем поле логина
                self.password_input.setText(password)  # Заполняем поле пароля
                
                # Устанавливаем выбранный сервер:
                for server, params in self.server_params.items():
                    if params["ip"] == host and params["port"] == port:
                        self.server_combo.setCurrentText(server)
                        break
                        
                self._add_log_message("Конфигурация загружена")
            except Exception as e:
                self._add_log_message(f"Ошибка загрузки конфигурации: {e}")

    def _save_config(self, login, password, host, port):
        """Сохраняет настройки в файл config.xml"""
        config_path = os.path.join(os.path.dirname(__file__), "config.xml")
        
        config = ET.Element("config")  # Создаем XML-структуру
        ET.SubElement(config, "login").text = login
        ET.SubElement(config, "password").text = self.connector.encrypt_password(password)  # Шифруем пароль
        ET.SubElement(config, "host").text = host
        ET.SubElement(config, "port").text = port
        ET.SubElement(config, "language").text = "ru"
        ET.SubElement(config, "autopos").text = "true"
        ET.SubElement(config, "milliseconds").text = "true"
        ET.SubElement(config, "utc_time").text = "true"

        tree = ET.ElementTree(config)
        tree.write(config_path, encoding="utf-8", xml_declaration=True)  # Сохраняем в файл
        
        self._add_log_message("Конфигурация сохранена")

    def _add_log_message(self, message):
        """Добавляет сообщение в журнал"""
        self.log_text.append(message)  # Добавляем текст
        self.log_text.ensureCursorVisible()  # Прокручиваем вниз

    def _on_connect_clicked(self):
        """Обработчик нажатия кнопки 'Подключить'"""
        login = self.login_input.text()  # Получаем логин
        password = self.password_input.text()  # Получаем пароль
        server = self.server_combo.currentText()  # Получаем выбранный сервер
        
        if not login or not password:  # Если логин или пароль пустые
            self._add_log_message("Ошибка: необходимо указать логин и пароль")
            return
            
        if server not in self.server_params:  # Если сервер не найден
            self._add_log_message("Ошибка: выбран несуществующий сервер")
            return
            
        server_info = self.server_params[server]  # Получаем параметры сервера
        
        try:
            self._save_config(login, password, server_info["ip"], server_info["port"])  # Сохраняем настройки
            
            result = self.connector.initialize(os.path.dirname(__file__), 1)  # Инициализация
            self._add_log_message(f"Инициализация: {result}")
            
            # Формируем команду подключения в XML:
            connect_cmd = f"""<command id="connect">
                <login>{login}</login>
                <password>{password}</password>
                <host>{server_info['ip']}</host>
                <port>{server_info['port']}</port>
                <language>ru</language>
                <autopos>true</autopos>
                <milliseconds>true</milliseconds>
                <utc_time>true</utc_time>
            </command>"""
            
            response = self.connector.send_command(connect_cmd)  # Отправляем команду
            self._add_log_message(f"Ответ сервера: {response}")
            
            self.connect_btn.setEnabled(False)  # Отключаем кнопку подключения
            self.disconnect_btn.setEnabled(True)  # Включаем кнопку отключения
            
        except Exception as e:
            self._add_log_message(f"Ошибка подключения: {e}")

    def _on_disconnect_clicked(self):
        """Обработчик нажатия кнопки 'Отключить'"""
        try:
            result = self.connector.uninitialize()  # Отключаемся
            self._add_log_message(f"Отключение: {result}")
            self.connect_btn.setEnabled(True)  # Включаем кнопку подключения
            self.disconnect_btn.setEnabled(False)  # Отключаем кнопку отключения
        except Exception as e:
            self._add_log_message(f"Ошибка отключения: {e}")

    def _on_clear_clicked(self):
        """Обработчик нажатия кнопки 'Стереть'"""
        config_path = os.path.join(os.path.dirname(__file__), "config.xml")
        if os.path.exists(config_path):  # Если файл конфигурации существует
            try:
                os.remove(config_path)  # Удаляем его
                self.login_input.clear()  # Очищаем поле логина
                self.password_input.clear()  # Очищаем поле пароля
                self._add_log_message("Конфигурация очищена")
            except Exception as e:
                self._add_log_message(f"Ошибка очистки: {e}")
        else:
            self._add_log_message("Конфигурация не найдена")

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Создаем приложение
    window = ConnectionWindow()  # Создаем окно
    window.show()  # Показываем окно
    sys.exit(app.exec_())  # Запускаем цикл обработки событий