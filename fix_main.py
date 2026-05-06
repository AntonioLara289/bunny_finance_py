# Fix main_window.py integration
with open('ui/main_window.py', 'r') as f:
    lines = f.readlines()

# Find and remove orphaned _crear_submenu_estilos function
new_lines = []
skip_until_next_def = False
for i, line in enumerate(lines):
    if 'def _crear_submenu_estilos' in line:
        skip_until_next_def = True
        continue
    if skip_until_next_def and line.startswith('    def '):
        skip_until_next_def = False
    if skip_until_next_def:
        continue
    new_lines.append(line)

# Find and update mostrarVistaPreferencias
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

print("Fixed!")
