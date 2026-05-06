import re

# Read the file as bytes
with open('ui/main_window.py', 'rb') as f:
    data = f.read()

# Decode with error handling
content = data.decode('utf-8', errors='ignore')

# Fix 1: Remove orphaned _crear_submenu_estilos function
# Based on earlier reads, it's around lines 62-79
pattern1 = r'    def _crear_submenu_estilos\(self, submenu\) -> None:.*?(?=\n    def _crear_menu_vistas)'
match1 = re.search(pattern1, content, re.DOTALL)
if match1:
    print(f"Found _crear_submenu_estilos at {match1.start()}-{match1.end()}")
    content = content[:match1.start()] + '    def _crear_menu_vistas(self, menu) -> None:' + content[match1.end():]
    print("Removed _crear_submenu_estilos")
else:
    print("Could not find _crear_submenu_estilos")

# Fix 2: Update mostrarVistaPreferencias
old_mostrar = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(Preferencias)'''

new_mostrar = '''    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(
            lambda: Preferencias(style_callback=self._cambiar_estilo)
        )'''

if old_mostrar in content:
    content = content.replace(old_mostrar, new_mostrar)
    print("Updated mostrarVistaPreferencias")
else:
    print("Could not find mostrarVistaPreferencias to update")

# Write back
with open('ui/main_window.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
