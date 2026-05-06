import sys
sys.path.insert(0, '.')

with open('ui/main_window.py', 'r') as f:
    content = f.read()

# Find the function
idx = content.find('def mostrarVistaPreferencias')
if idx >= 0:
    print(repr(content[idx:idx+200]))
else:
    print("Function not found")
