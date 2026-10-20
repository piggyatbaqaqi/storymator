"""ComfyUI workflow generators.

A package rather than a plain directory so that
``gen_lineart_colour_test.py``, which sits beside the module it tests,
can say ``from . import gen_lineart_colour``.  That is the same answer
``penciltest`` gives, and it is what lets mypy -- based at ``comfyui/``
-- resolve the test's import.  Imported absolutely it runs under pytest
and is unresolvable to the checker; see ``comfyui/mypy.ini``.
"""
