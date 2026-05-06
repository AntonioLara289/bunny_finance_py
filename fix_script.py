with open('ui/main_window.py', 'r') as f:
    lines = f.readlines()

# Find and remove orphaned _crear_submenu_estilos function
new_lines = []
skip = False
for i, line in enumerate(lines):
    # Check if this line starts the orphaned function
    if '    def _crear_submenu_estilos(self, submenu) -> None:' in line:
        skip = True
        continue
    # If we're skipping and find the next method (starts with '    def ')
    if skip and line.startswith('    def '):
        skip = False
    if skip:
        continue
    new_lines.append(line)

# Update mostrarVistaPreferencias
content = ''.join(new_lines)
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

print("Done!")
