"""Import hardening across the whole app package.

B-01 (closure task): `mock_dialogue` used `Tuple` in annotations while
importing only `Mapping`. Python 3.14 evaluates module annotations
lazily (PEP 649), so the undefined name silently survives `import` on
that interpreter and explodes later — or immediately on Python <= 3.13.
This test forces annotation evaluation for every module so an undefined
annotation name fails here, on any interpreter.
"""

import importlib
import pkgutil

import app


def test_all_app_module_annotations_resolve() -> None:
    module_names = ["app"] + [
        info.name for info in pkgutil.walk_packages(app.__path__, prefix="app.")
    ]
    assert len(module_names) > 10  # the walk actually found the package tree

    for name in module_names:
        module = importlib.import_module(name)
        # PEP 649: accessing __annotations__ triggers deferred evaluation;
        # an undefined name inside any annotation raises NameError here.
        dict(module.__annotations__)
