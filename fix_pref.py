# Fix main_window.py
import re

with open('ui/main_window.py', 'rb') as f:
    data = f.read()

content = data.decode('utf-8', errors='ignore')

# Fix mostrarVistaPreferencias
old = '    def mostrarVistaPreferencias(self) -> None:\n\n        print("Mostrando la vista de Preferencias")\n\n        self._cambiar_vista(Preferencias)'

new = '    def mostrarVistaPreferencias(self) -> None:\n\n        print("Mostrando la vista de Preferencias")\n\n        self._cambiar_vista(\n            lambda: Preferencias(style_callback=self._cambiar_estilo)\n        )'

if old in content:
    content = content.replace(old, new)
    print("Fixed!")
else:
    print("Not found")
    print(repr(content[content.find('def mostrarVistaPreferencias'):content.find('def mostrarVistaPreferencias')+200]))

with open('ui/main_window.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)
