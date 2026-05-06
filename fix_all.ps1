# Fix main_window.py
$filePath = "ui\main_window.py"
$content = Get-Content $filePath -Raw

# Fix 1: Remove orphaned _crear_submenu_estilos function
$pattern1 = '(?s)    # MEN.*?def _crear_submenu_estilos.*?\)\n\n'
$content = [regex]::Replace($content, $pattern1, "    # MENÚS`n    def _crear_menus(self) -> None:`n")

# Fix 2: Update mostrarVistaPreferencias
$old_mostrar = '    def mostrarVistaPreferencias(self) -> None:`n        print("Mostrando la vista de Preferencias")`n        self._cambiar_vista(Preferencias)'
$new_mostrar = '    def mostrarVistaPreferencias(self) -> None:`n        print("Mostrando la vista de Preferencias")`n        self._cambiar_vista(`n            lambda: Preferencias(style_callback=self._cambiar_estilo)`n        )'

$content = $content.Replace($old_mostrar, $new_mostrar)

Set-Content $filePath $content -NoNewline
Write-Host "Fixed!"
