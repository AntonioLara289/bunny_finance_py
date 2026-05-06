import re

with open('ui/main_window.py', 'r') as f:
    content = f.read()

# Fix 1: Remove orphaned _crear_submenu_estilos function
pattern1 = r'\n    def _crear_submenu_estilos\(self, submenu\) -> None:.*?(?=\n    def |\nclass |\Z)'
content = re.sub(pattern1, '\n', content, flags=re.DOTALL)

# Fix 2: Update mostrarVistaPreferencias to pass callback
old = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(Preferencias)'''

new = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(
            lambda: Preferencias(style_callback=self._cambiar_estilo)
        )'''

content = content.replace(old, new)

with open('ui/main_window.py', 'w') as f:
    f.write(content)

print("Done")
