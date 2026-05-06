import sys
sys.path.insert(0, '.')

try:
    from ui.main_window import MainWindow
    print("Import OK")
    
    # Check if style_callback is in Preferencias
    from ui.preferencias import Preferencias
    import inspect
    sig = inspect.signature(Preferencias.__init__)
    print("Preferencias __init__ params:", sig)
    
except Exception as e:
    print("Error:", e)
