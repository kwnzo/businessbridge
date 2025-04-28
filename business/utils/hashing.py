
password = input('Введите пароль: ')


hashed = {
    # Строчные буквы (предыдущий набор)
    "a": "b", "b": "k", "c": "q", "d": "w", "e": "z", "f": "m",
    "g": "r", "h": "t", "i": "p", "j": "s", "k": "u", "l": "v",
    "m": "a", "n": "y", "o": "x", "p": "j", "q": "i", "r": "n",
    "s": "e", "t": "l", "u": "f", "v": "d", "w": "c", "x": "o",
    "y": "g", "z": "h",
    
    # Заглавные буквы (новые замены)
    "A": "L", "B": "M", "C": "N", "D": "O", "E": "P", "F": "Q",
    "G": "R", "H": "S", "I": "T", "J": "U", "K": "V", "L": "W",
    "M": "X", "N": "Y", "O": "Z", "P": "A", "Q": "B", "R": "C",
    "S": "D", "T": "E", "U": "F", "V": "G", "W": "H", "X": "I",
    "Y": "J", "Z": "K",
    
    # Цифры и спецсимволы
    "0": "!", "1": "@", "2": "#", "3": "$", "4": "%", "5": "^",
    "6": "&", "7": "*", "8": "(", "9": ")", "!": "2", "@": "5",
    "#": "1", "$": "8", "%": "!", "^": "0", "&": "/"
}

hashed_password = password

ready_password = []

for i in hashed_password:
    if i in hashed:
        ready_password.append(hashed[i])


print(f'HASHED PASSWORD: {ready_password[::-1]}')


#print(f'INPUTED PASSWORD: {hashed_password}')


