"""The various tools that I've built across my projects."""

__all__ = [
    "borg",
    "callbacks",
    "checks",
    "commandLineApp",
    "db",
    "decorators",
    "extraUtils",
    "factory",
    "searching",
    "sorting"
    ]

# some distributions of my library don't include these modules
try:
    for optionalMod in ("nameFilter", ):
        __all__.append(optionalMod)

except ModuleNotFoundError:
    pass