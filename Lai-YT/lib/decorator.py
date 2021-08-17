import copy
import functools
from typing import Any, Callable, List, Tuple


Func = Callable[..., Any]

def pass_by_copy(pos: List[int] = [], kw: List[str] = []) -> Callable[[Func], Callable[..., Func]]:
    """Arguments at the "pos" and named "kw" will be copied by copy.deepcopy() before passing to the wrapped function.
    It's okay to specify an argument twice or in both "pos" and "kw", but it'll be copied twice also.

    Arguments:
        pos (List[int]):
            Positions of the arguments to be copied in the argument list of the wrapped function.
            Starts from 0.
        kw (List[str]):
            Names of the arguments to be copied in the argument list of the wrapped function.
    """
    def decorator(func: Func) -> Callable[..., Func]:
        arguments: Tuple[str, ...] = func.__code__.co_varnames
        @functools.wraps(func)
        def decorated(*args: Any, **kwargs: Any) -> Func:
            args_list: List[Any] = list(args)
            # the positional arguments
            try:
                for p in pos:
                    # the positional argument is passes by keyword
                    if len(args_list) <= p:
                        arg_name: str = arguments[p]
                        kwargs[arg_name] = copy.deepcopy(kwargs[arg_name])
                    else:
                        args_list[p] = copy.deepcopy(args[p])
            except IndexError:
                raise IndexError('position out of range') from None
            # the keyword arguments
            try:
                for w in kw:
                    # the keyword argument is passes by position
                    if w not in kwargs:
                        arg_pos: int = arguments.index(w)
                        args_list[arg_pos] = copy.deepcopy(args[arg_pos])
                    else:
                        kwargs[w] = copy.deepcopy(kwargs[w])
            except ValueError:
                raise ValueError('keyword doesn\'t exist') from None
            return func(*args_list, **kwargs)
        return decorated
    return decorator
