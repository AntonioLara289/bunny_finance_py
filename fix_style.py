import re

with open('ui/main_window.py', 'rb') as f:
    data = f.read()

content = data.decode('utf-8', errors='ignore')

# Fix mostrarVistaPreferencias
old = 'def mostrarVistaPreferencias(self) -> None:\r\n\r\n        print("Mostrando la vista de Preferencias")\r\n\r\n        self._cambiar_vista(Preferencias)\r\n'

new = 'def mostrarVistaPreferencias(self) -> None:\r\n\r\n        print("Mostrando la vista de Preferencias")\r\n\r\n        self._cambiar_vista(\r\n            lambda: Preferencias(style_callback=self._cambiar_estilo)\r\n        )\r\n'

if old in content:
    content = content.replace(old, new)
    print("Fixed!")
else:
    print("Not found")
    # Let's see what's there
    idx = content.find('def mostrarVistaPreferencias')
    if idx >= 0:
        print(repr(content[idx:idx+200]))

with open('ui/main_window.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)
