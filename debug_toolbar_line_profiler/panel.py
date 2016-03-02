from __future__ import absolute_import, division, unicode_literals

from colorsys import hsv_to_rgb
import cProfile
import inspect
import os
from pstats import Stats
from six import PY2

from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.six.moves import cStringIO
from debug_toolbar.panels import Panel
from django.views.generic.base import View

from line_profiler import LineProfiler, show_func

from . import signals


class DjangoDebugToolbarStats(Stats):
    __root = None

    def get_root_func(self, view_func):
        if self.__root is None:
            filename = view_func.__code__.co_filename
            firstlineno = view_func.__code__.co_firstlineno
            for func, (cc, nc, tt, ct, callers) in self.stats.items():
                if (len(callers) == 0
                        and func[0] == filename
                        and func[1] == firstlineno):
                    self.__root = func
                    break
        return self.__root


class FunctionCall(object):
    """
    The FunctionCall object is a helper object that encapsulates some of the
    complexity of working with pstats/cProfile objects

    """
    def __init__(self, statobj, func, depth=0, stats=None,
                 id=0, parent_ids=[], hsv=(0, 0.5, 1)):
        self.statobj = statobj
        self.func = func
        if stats:
            self.stats = stats
        else:
            self.stats = statobj.stats[func][:4]
        self.depth = depth
        self.id = id
        self.parent_ids = parent_ids
        self.hsv = hsv
        self._line_stats_text = None

    def parent_classes(self):
        return self.parent_classes

    def background(self):
        r, g, b = hsv_to_rgb(*self.hsv)
        return 'rgb(%f%%,%f%%,%f%%)' % (r * 100, g * 100, b * 100)

    def func_std_string(self):  # match what old profile produced
        func_name = self.func
        if func_name[:2] == ('~', 0):
            # special case for built-in functions
            name = func_name[2]
            if name.startswith('<') and name.endswith('>'):
                return '{%s}' % name[1:-1]
            else:
                return name
        else:
            file_name, line_num, method = self.func
            idx = file_name.find('/site-packages/')
            if idx > -1:
                file_name = file_name[(idx + 14):]

            file_path, file_name = file_name.rsplit(os.sep, 1)

            return mark_safe(
                '<span class="path">{0}/</span>'
                '<span class="file">{1}</span>'
                ' in <span class="func">{3}</span>'
                '(<span class="lineno">{2}</span>)'.format(
                    file_path,
                    file_name,
                    line_num,
                    method))

    def subfuncs(self):
        i = 0
        h, s, v = self.hsv
        count = len(self.statobj.all_callees[self.func])
        for func, stats in self.statobj.all_callees[self.func].items():
            i += 1
            h1 = h + (i / count) / (self.depth + 1)
            if stats[3] == 0:
                s1 = 0
            else:
                s1 = s * (stats[3] / self.stats[3])
            yield FunctionCall(self.statobj,
                               func,
                               self.depth + 1,
                               stats=stats,
                               id=str(self.id) + '_' + str(i),
                               parent_ids=self.parent_ids + [self.id],
                               hsv=(h1, s1, 1))

    def count(self):
        return self.stats[1]

    def tottime(self):
        return self.stats[2]

    def cumtime(self):
        return self.stats[3]

    def tottime_per_call(self):
        cc, nc, tt, ct = self.stats

        if nc == 0:
            return 0

        return tt / nc

    def cumtime_per_call(self):
        cc, nc, tt, ct = self.stats

        if cc == 0:
            return 0

        return ct / cc

    def indent(self):
        return 16 * self.depth

    def line_stats_text(self):
        if self._line_stats_text is None:
            lstats = self.statobj.line_stats
            if self.func in lstats.timings:
                out = cStringIO()
                fn, lineno, name = self.func
                try:
                    show_func(fn,
                              lineno,
                              name,
                              lstats.timings[self.func],
                              lstats.unit, stream=out)
                    self._line_stats_text = out.getvalue()
                except ZeroDivisionError:
                    self._line_stats_text = ("There was a ZeroDivisionError, "
                                             "total_time was probably zero")
            else:
                self._line_stats_text = False
        return self._line_stats_text


class ProfilingPanel(Panel):
    """
    Panel that displays profiling information.
    """
    title = _('Profiling')

    template = 'debug_toolbar_line_profiler/panels/profiling.html'

    def _unwrap_closure_and_profile(self, func):
        if not hasattr(func, '__code__'):
            return
        self.line_profiler.add_function(func)
        for subfunc in getattr(func, 'profile_additional', []):
            self._unwrap_closure_and_profile(subfunc)
        if func.__closure__:
            for cell in func.__closure__:
                if hasattr(cell.cell_contents, '__code__'):
                    self._unwrap_closure_and_profile(cell.cell_contents)

    def process_view(self, request, view_func, view_args, view_kwargs):
        self.view_func = view_func
        self.profiler = cProfile.Profile()
        args = (request,) + view_args
        self.line_profiler = LineProfiler()
        self._unwrap_closure_and_profile(view_func)
        if PY2:
            view_func_name = view_func.func_globals['__name__']
        else:
            view_func_name = view_func.__globals__['__name__']
        if view_func_name == 'django.views.generic.base':
            if PY2:
                func_closure = view_func.func_closure
            else:
                func_closure = view_func.__closure__
            for cell in func_closure:
                target = cell.cell_contents
                if inspect.isclass(target) and View in inspect.getmro(target):
                    for name, value in inspect.getmembers(target):
                        if name[0] != '_' and inspect.ismethod(value):
                            self._unwrap_closure_and_profile(value)
        signals.profiler_setup.send(sender=self,
                                    profiler=self.line_profiler,
                                    view_func=view_func,
                                    view_args=view_args,
                                    view_kwargs=view_kwargs)
        self.line_profiler.enable_by_count()
        out = self.profiler.runcall(view_func, *args, **view_kwargs)
        self.line_profiler.disable_by_count()
        return out

    def add_node(self, func_list, func, max_depth, cum_time=0.1):
        """
        add_node does a depth first traversal of the call graph, appending a
        FunctionCall object to func_list, so that the Django template only
        has to do a single for loop over func_list that can render a tree
        structure

        Parameters:
            func_list is an array that will have a FunctionCall for each call
                added to it
            func is a FunctionCall object that will have all its callees added
            max_depth is the maximum depth we should recurse
            cum_time is the minimum cum_time a function should have to be
                included in the output
        """
        func_list.append(func)
        func.has_subfuncs = False
        # this function somewhat dangerously relies on FunctionCall to set its
        # subfuncs' depth argument correctly
        if func.depth >= max_depth:
            return

        # func.subfuncs returns FunctionCall objects
        for subfunc in func.subfuncs():
            # a sub function is important if it takes a long time or it has
            # line_stats
            if (subfunc.cumtime >= cum_time or
                    (hasattr(self.stats, 'line_stats') and
                     subfunc.func in self.stats.line_stats.timings)):
                func.has_subfuncs = True
                self.add_node(func_list, subfunc, max_depth, cum_time=cum_time)

    def process_response(self, request, response):
        if not hasattr(self, 'profiler'):
            return None
        # Could be delayed until the panel content is requested (perf. optim.)
        self.profiler.create_stats()
        self.stats = DjangoDebugToolbarStats(self.profiler)
        self.stats.line_stats = self.line_profiler.get_stats()
        self.stats.calc_callees()

        func_list = []

        root_func = self.stats.get_root_func(self.view_func)

        if root_func is not None:
            root_node = FunctionCall(statobj=self.stats,
                                     func=root_func,
                                     depth=0)
            self.add_node(
                func_list=func_list,
                func=root_node,
                max_depth=10,
                cum_time=root_node.cumtime / 8
            )
        # else:
        # what should we do if we didn't detect a root function? It's not
        # clear what causes this, but there are real world examples of it (see
        # https://github.com/dmclain/django-debug-toolbar-line-profiler/issues/11)

        self.record_stats({'func_list': func_list})
