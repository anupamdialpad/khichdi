# import functools
# Python class decorator with arguments
class SimpleRetry: # class: name of the decorator
    def __init__(self, tries=0): # tries: arguments of the decorator
        # functools.update_wrapper(self, func) # dont' know why functools is required
        self.func = None # func: function which is decorated
        self.tries = tries

    def __call__(self, func):
        # functools.update_wrapper(self, func)
        self.func = func
        return lambda *a, **k: self.wrapper(*a, **k) # returning self.wrapper doesn't send the object of `func`
    
    def wrapper(self, *args, **kwargs): # args & kwargs: arguments of `func`
        func_obj = args[0]
        print(f"{func_obj}.value={func_obj.value}")
        for _ in range(self.tries):
            self.func(*args, **kwargs)

class RandomClass:
    def __init__(self) -> None:
        self.value = 42

    @SimpleRetry(tries=2)
    def say_it(self, say):
        print(say)

rc = RandomClass()
rc.say_it('whiz!')