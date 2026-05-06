import re

# Read the file as bytes
with open('D:/Code/Tesis/Python/bunny_finance_py/ui/main_window.py', 'rb') as f:
    data = f.read()

# Decode with error handling
content = data.decode('utf-8', errors='ignore')

# Fix 1: Update mostrarVistaPreferencias to pass callback
old = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(Preferencias)'''

new = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(
            lambda: Preferencias(style_callback=self._cambiar_estilo)
        )'''

if old in content:
    content = content.replace(old, new)
    print("Fixed mostrarVistaPreferencias")
else:
    print("Could not find mostrarVistaPreferencias to update")
    # Let's see what's there
    idx = content.find('def mostrarVistaPreferencias')
    if idx >= 0:
        print(repr(content[idx:idx+150]))

# Write back
with open('D:/Code/Tesis/Python/bunny_finance_py/ui/main_window.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
