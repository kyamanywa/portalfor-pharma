"""
Compatibility shim for Python 3.14+ where pkgutil.find_loader was removed
This patches pkgutil to make django_filters work with newer Python versions
"""
import pkgutil
import importlib.util

def find_loader(fullname):
    """
    Compatibility function to replace removed pkgutil.find_loader in Python 3.14+
    """
    try:
        spec = importlib.util.find_spec(fullname)
        return spec.loader if spec else None
    except (ImportError, AttributeError, ValueError, ModuleNotFoundError):
        return None

# Monkey patch pkgutil if find_loader is missing
if not hasattr(pkgutil, 'find_loader'):
    pkgutil.find_loader = find_loader