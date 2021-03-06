"""Validation checks"""

from typing import Iterable, Any, Container

# old version of CHECKTYPES, left for backwards compatibility
def validateInput(input: str)->bool:
    '''
    DEPRECATED. Use CHECKTYPES.
    Validates the input string, float, or integer. input is the input to be validated.
    Returns boolean'''

    isString=isinstance(input,str)

    #strings
    if isString==True:
        if len(input)==0 or input== ' ' or input == "":
            return True #use this boolean to know whether to re-ask the question
    else:
        return False
    
    #numbers
    if isString==False:
        if input==0 or input<0 or len(input)==0:
            return True
        else:
            return False


# CHECKS
def lengthCheck(value: Any, minLength: int = None, maxLength: int = None) -> bool:
    """Check that the value's length is within the range of minLength and maxLength.
    Leave minLength or maxLength as None if there is no boundary. One boundary must be defined."""

    # ensure at least one boundary was passed
    assert (minLength or maxLength)

    if minLength and maxLength:
        return (minLength <= len(value) <= maxLength)

    elif minLength:
        return (minLength <= len(value))

    else:
        return (len(value) <= maxLength)


def withinCheck(value: Any, toCheck: Container) -> bool:
    """Check that the value exists in iterable.
    Use lambda: not withinCheck(value, toCheck) to get the inverse."""

    return (value in toCheck)


def typeCheck(value: Any, targetType: type, subclassCheck: bool = False) -> bool:
    """Check if the type of the value is targetType.
    If subclass check is set: check if value's type is descended from targetType"""

    if subclassCheck:
        return (issubclass(value.__class__, targetType))

    else:
        return (type(value) is targetType)


def defaultCheck(*args, **kwargs):  # absorb any args
    """No check currently but this was added for maintainability."""

    return True


# dict of all check types to allow importing all checks at once
# without needing to know which checks are available
CHECKTYPES = {
    "lengthCheck" : lengthCheck,
    "withinCheck" : withinCheck,
    "typeCheck" : typeCheck,
    "defaultCheck" : defaultCheck,
    }