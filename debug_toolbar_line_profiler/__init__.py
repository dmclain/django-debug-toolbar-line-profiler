
def profile_additional(*subfuncs):
    def inner(func):
        func.profile_additional = subfuncs
        return func
    return inner
