import base64


def encrypt(plain, use_hash=False, _format=None):

    key_square = [
        ['A', 'B', 'C', 'D', 'E', 'F'],
        ['G', 'H', 'I', 'J', 'K', 'L'],
        ['M', 'N', 'O', 'P', 'Q', 'R'],
        ['S', 'T', 'U', 'V', 'W', 'X'],
        ['Y', 'Z', '0', '1', '2', '3'],
        ['4', '5', '6', '7', '8', '9'],
    ]
    transposition_key = "PASSWORD"

    def atbash(text):
        res = []
        for ch in text:
            res.append(chr((128 - ord(ch)) % 128))
        return ''.join(res)

    def caesar_all(text, shift):
        return ''.join(chr((ord(ch)+shift) % 128) for ch in text)

    def rail_fence_encrypt(text, rails):
        fence = [[] for _ in range(rails)]
        rail = 0
        direction = 1
        for ch in text:
            fence[rail].append(ch)
            rail += direction
            if rail == rails-1 or rail == 0:
                direction = -direction
        return ''.join(''.join(row) for row in fence)

    def vigenere_encrypt(text, keyword):
        encrypted = []
        keyword = keyword.upper()
        keyword_len = len(keyword)

        for i, char in enumerate(text.upper()):
            if 'B' <= char <= '[':
                shift = ord(keyword[i % keyword_len]) - ord('B')
                encrypted_char = chr(
                    (ord(char) - ord('B') + shift) % 26 + ord('B'))
                encrypted.append(encrypted_char)
            else:
                encrypted.append(char)
        return ''.join(encrypted)

    def adfgvx_encrypt(text, key_square, transposition_key):
        adfgvx = "abfgvx"

        coord = {}
        for i in range(6):
            for j in range(6):
                coord[key_square[i][j]] = adfgvx[i] + adfgvx[j]

        substituted = ""
        for char in text.upper():
            if char in coord:
                substituted += coord[char]
            else:
                continue

        key_len = len(transposition_key)

        rows = len(substituted) // key_len
        if len(substituted) % key_len != 0:
            rows += 1

        matrix = [['' for _ in range(key_len)] for _ in range(rows)]

        idx = 0
        for i in range(rows):
            for j in range(key_len):
                if idx < len(substituted):
                    matrix[i][j] = substituted[idx]
                    idx += 1

        key_order = sorted(range(key_len), key=lambda x: transposition_key[x])

        encrypted = ""
        for col in key_order:
            for row in range(rows):
                if matrix[row][col]:
                    encrypted += matrix[row][col]

        return encrypted

    def morse_binary_numbers(text):

        morse_dict = {

            'A': '.-.--',     'B': '.-...',   'C': '.-.-.',   'D': '..-..',
            'E': '...-.',      'F': '-..-.',   'G': '-.-..',

            '0': '-----',  '1': '.----',  '2': '..---',  '3': '...--',
            '4': '....-',  '5': '.....',  '6': '-....',  '7': '--...',
            '8': '---..',  '9': '----.'
        }

        morse_chars = []
        for ch in text.upper():
            if ch in morse_dict:

                morse_chars.append(morse_dict[ch])

        morse_str = ' '.join(morse_chars)

        binary = []
        for symbol in morse_str:
            if symbol == '.':
                binary.append('0')
            elif symbol == '-':
                binary.append('1')
            elif symbol == ' ':
                binary.append('10110')

        bin_str = ''.join(binary)
        padding = (8 - len(bin_str) % 8) % 8
        bin_str = bin_str + '0' * padding

        numbers = []
        for i in range(0, len(bin_str), 8):
            byte_str = bin_str[i:i+8]
            numbers.append(str(int(byte_str, 2)))

        return ' '.join(numbers)

    def CRT_encrypt(num):
        return int(num) % 43 * 6 + int(num) % 6

    def encode_custom_base(num, alphabet=''.join(chr(i) for i in range(33, 127))):
        base = len(alphabet)
        if num == 0:
            return alphabet[0]

        result = []
        while num > 0:
            num, rem = divmod(num, base)
            result.append(alphabet[rem])
        return ''.join(reversed(result))

    def base64_like_to_int(text, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"):
        base = len(alphabet)
        char_to_value = {char: idx for idx, char in enumerate(alphabet)}

        result = 0
        for char in text:
            result = result * base + char_to_value[char]

        return result

    def utf8_to_compact_hex(text, key="987654321"):
        bytes_data = text.encode('ascii')
        upper_str = bytes_data.hex().upper()
        square = "BF3749ADCE250G816"
        result = []

        key_len = len(key)

        for i, char in enumerate(upper_str):
            if char in square:
                pos = square.find(char)

                key_digit = int(key[i % key_len])

                new_pos = (pos * key_digit) % 17
                result.append(square[new_pos])
            else:
                result.append(char)

        return ''.join(result)

    def simple_encrypt(text, key):
        encrypted = ''.join(
            chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)
        )
        return base64.b32encode(encrypted.encode()).decode()

    def polynomial_encrypt_v2(text, chunk_size=32, negate_even=True):
        bytes_data = text.encode('utf-8')
        coefficients = []
        for i in range(0, chunk_size*4 if use_hash else len(bytes_data), chunk_size):
            chunk = bytes_data[i:i+chunk_size]
            if len(chunk) < chunk_size:
                chunk = chunk + b'\x00' * (chunk_size - len(chunk))
            num = int.from_bytes(chunk, 'big')
            coefficients.append(num)
        if use_hash:
            num_terms = 17
        else:
            num_terms = len(coefficients) + 1
        if negate_even:
            actual_coeffs = []
            for i, coeff in enumerate(coefficients):
                if i % 2 == 0:
                    actual_coeffs.append(-coeff)
                else:
                    actual_coeffs.append(coeff)
        else:
            actual_coeffs = coefficients
        poly_terms = []
        for i, coeff in enumerate(actual_coeffs):
            if coeff >= 0:
                sign = "+" if i > 0 else ""
                poly_terms.append(f"{sign}{coeff}x^{i}")
            else:
                poly_terms.append(f"{coeff}x^{i}")
        results = []
        for x in range(1, num_terms + 1):
            value = 0
            for i, coeff in enumerate(actual_coeffs):
                value += coeff * (x ** i)
            results.append(value)

        return results

    def encrypt_small(num_str):
        num_str = int(num_str)

        encrypted_int = (num_str * 7 + 6) % 10
        return str(encrypted_int)

    def encrypt_big(num_str, length=90):
        num_str = str(num_str)
        encrypted_int = ""
        for num in num_str:
            if num == "-":
                encrypted_int += "-"
            else:
                encrypted_int += encrypt_small(num)

        return encode_custom_base(base64_like_to_int(base64.b64encode(str(int(encrypted_int.ljust(length, "A"), base=11)).encode()).decode().replace("=", "")))

    def get_max_length(numbers):
        return max(len(str(n)) for n in numbers)

    def difference_polynomial_encrypt(numbers_str):
        if not numbers_str.strip():
            return ""

        nums = [int(x) for x in numbers_str.strip().split(" ")]

        first_terms = []
        current = nums if not use_hash else nums

        while current:
            first_terms.append(str(current[0]))
            if len(current) == 1:
                break
            current = [current[i+1] - current[i]
                       for i in range(len(current)-1)]

        return ' '.join(first_terms)

    layer_now = caesar_all(plain, 70)
    layer_now = atbash(layer_now)
    layer_now = rail_fence_encrypt(layer_now, 3)
    layer_now = utf8_to_compact_hex(layer_now)
    layer_now = morse_binary_numbers(layer_now)
    key = layer_now.strip().split(" ")[-1]
    layer_now = [CRT_encrypt(i) for i in layer_now.strip().split(" ")]
    for i in range(len(layer_now)):
        layer_now[i] = str(int(layer_now[i]) ^ int(layer_now[i-1]))
    layer_now = layer_now[::-1]
    layer_now = " ".join(layer_now)
    layer_now = difference_polynomial_encrypt(layer_now)
    layer_now = simple_encrypt(layer_now, key)
    layer_now = vigenere_encrypt(layer_now, "FLAG")
    layer_now = utf8_to_compact_hex(
        layer_now, key="314159265358929793238462643383")
    layer_now = adfgvx_encrypt(layer_now, key_square, transposition_key)
    layer_now = base64.b85encode(layer_now.encode()).decode()
    layer_now = polynomial_encrypt_v2(layer_now)
    layers = []
    for big in layer_now:
        layers.append(encrypt_big(big, get_max_length(layer_now)))
    if use_hash:
        layers = [i[16:48:3] for j, i in enumerate(layers)]
        if _format == None:
            return "".join(layers)
        elif _format == "hex":
            return "".join(layers).encode().hex().upper()
        elif _format == "base64":
            return base64.b64encode("".join(layers).encode()).decode()
        else:
            raise ValueError
    else:
        if _format == None:
            return "".join(layers)
        elif _format == "hex":
            return "".join(layers).encode().hex().upper()
        elif _format == "base64":
            return base64.b64encode("".join(layers).encode()).decode()
        else:
            raise ValueError


def main():
    import random
    import os
    if os.path.exists("flag.txt"):
        flag = open("flag.txt").read()
    else:
        flag = \
            "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
    with open("flag.txt", mode='w') as f:
        f.write(flag)
    return encrypt(flag)
