# Python 3.14 compatibility: BaseContext.__copy__ uses copy(super()) which
# breaks in Python 3.14 because super() proxies can no longer be copied.
# Patch it to use a safe clone approach instead.
try:
    from django.template.context import BaseContext

    def _py314_safe_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    if not getattr(BaseContext.__copy__, "_py314_patched", False):
        _py314_safe_copy._py314_patched = True
        BaseContext.__copy__ = _py314_safe_copy
except Exception:
    pass
