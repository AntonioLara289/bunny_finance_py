# Fix main_window.py
with open('ui/main_window.py', 'rb') as f:
    data = f.read()

# Decode with error handling
content = data.decode('utf-8', errors='ignore')

# Fix 1: Remove orphaned _crear_submenu_estilos function (lines 62-79)
import re
pattern1 = rb'\n    def _crear_submenu_estilos\(self, submenu\) -> None:[^\n]*\n(?:        [^\n]*\n)*'
match1 = re.search(pattern1, data)
if match1:
    print(f"Found function at {match1.start()}-{match1.end()}")
    # We'll handle this differently

print("Let's check what we can do...")
print("File size:", len(data))
