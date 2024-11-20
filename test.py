import re


def clean_error_message(err: str) -> str:
    cleaned_message = re.sub(r'Traceback $most recent call last$:.*?\n', '', err, flags=re.DOTALL)

    lines = cleaned_message.splitlines()
    detailed_lines = []

    for line in lines:
        if 'File "' in line or 'line ' in line:
            continue

        if detailed_lines and re.match(r'^\s*\^+', line):
            detailed_lines[-1] += '\n' + line
        else:
            detailed_lines.append(line)

    # Join cleaned lines while keeping the non-empty ones
    cleaned_message = '\n'.join(filter(None, detailed_lines)).strip()
    return cleaned_message


# Example usage of the function:
error_message = '''<b>Ваш код выдал ошибку</b>:
File "/env/restricted_dir/script_985547ec-2b56-4175-8b71-29f334237d46.py", line 4, in <module>
    result = a(2, 3)
             ^^^^^^^
  File "/env/restricted_dir/script_985547ec-2b56-4175-8b71-29f334237d46.py", line 2, in a
    def a(a, b): return a**B
                           ^
NameError: name 'B' is not defined. Did you mean: 'b'?'''

cleaned_message = clean_error_message(error_message)
print(cleaned_message)
