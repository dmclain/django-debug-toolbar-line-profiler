=======================================
Django Debug Toolbar Line Profile Panel
=======================================

The `Django Debug Toolbar 
<https://github.com/django-debug-toolbar/django-debug-toolbar>`_ is a configurable set of panels that display various
debug information about the current request/response and when clicked, display
more details about the panel's content.

This package provides a panel that incorporates output from line_profiler_

line_profiler is only compatible with the 2.x branch of python. This panel
will only function with django_debug_toolbar>=1.0, before that it's functionality
was contained in the debug_toolbar.panels.profiling.ProfilingPanel

This Django Debug Toolbar panel is released under the BSD license, like Django
and the Django Debug Toolbar. If you like it, please consider contributing!

The Django Debug Toolbar was originally created by Rob Hudson
in August 2008 and was further developed by many contributors.

.. _line_profiler: http://pythonhosted.org/line_profiler/


Installation
============

To install the line_profiler panel, first install this package with ``pip install django-debug-toolbar-line-profiler``, then add debug_toolbar_line_profiler to the INSTALLED_APPS::

    INSTALLED_APPS = (
        ...
        'debug_toolbar_line_profiler',
    )

and add the panel to DEBUG_TOOLBAR_PANELS::

    DEBUG_TOOLBAR_PANELS = (
        ...
        'debug_toolbar_line_profiler.panel.ProfilingPanel',
    )

Configuration
=============

By default, the panel will profile your view function. If you use class based views
the panel will profile all functions on the class that don't start with _. If you
want additional code to be profiled, add the @profile_additional decorator like so::

    from debug_toolbar_line_profiler import profile_additional
    from boto.s3.connection import S3Connection
    
    ...
    
    @profile_additional(S3Connection.make_request)
    def your_view_code(*args, **kwargs):
        ...
