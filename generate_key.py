# Импортируем библиотеку для шифрования
from cryptography.fernet import Fernet  # Fernet — это метод симметричного шифрования

# Генерация ключа (случайная строка из 32 байт)
key = Fernet.generate_key()  # Создаем новый ключ

# Выводим ключ в консоль (чтобы его можно было скопировать)
print("Ключ шифрования:", key.decode())  # decode() преобразует байты в строку

# Пример вывода:
# Ключ шифрования: 2KXJDnq6GY7Me9c1omNuzjTfXVWqLIQP4jnkIHGKPck=