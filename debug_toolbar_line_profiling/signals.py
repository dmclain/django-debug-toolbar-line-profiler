import django.dispatch


profiler_setup = django.dispatch.Signal(providing_args=['profiler', 'view_func', 'view_args', 'view_kwargs'])