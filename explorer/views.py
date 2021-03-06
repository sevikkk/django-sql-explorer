import six

from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy, reverse
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.db import DatabaseError

from explorer.models import Query, QueryLog
from explorer import app_settings
from explorer.forms import QueryForm
from explorer.utils import url_get_rows,\
    url_get_query_id,\
    url_get_log_id,\
    schema_info,\
    url_get_params,\
    safe_login_prompt,\
    build_download_response,\
    build_stream_response,\
    user_can_see_query,\
    fmt_sql, get_connections_list

try:
    from collections import Counter
except:
    from counter import Counter


import re
import json
from functools import wraps


def view_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):

        if not app_settings.EXPLORER_PERMISSION_VIEW(request.user)\
                and not request.user.has_perm("explorer.query_view") \
                and not user_can_see_query(request, kwargs)\
                and not (app_settings.EXPLORER_TOKEN_AUTH_ENABLED()
                         and request.META.get('HTTP_X_API_TOKEN') == app_settings.EXPLORER_TOKEN):
            return safe_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


def change_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return safe_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


class ExplorerContextMixin(object):

    def gen_ctx(self):
        return {'can_view': app_settings.EXPLORER_PERMISSION_VIEW(self.request.user),
                'can_change': app_settings.EXPLORER_PERMISSION_CHANGE(self.request.user)}

    def get_context_data(self, **kwargs):
        ctx = super(ExplorerContextMixin, self).get_context_data(**kwargs)
        ctx.update(self.gen_ctx())
        return ctx

    def render_template(self, template, ctx):
        ctx.update(self.gen_ctx())
        return render_to_response(template, ctx)


@view_permission
@require_GET
def download_query(request, query_id):
    return _csv_response(request, query_id, False)


@view_permission
@require_GET
def view_csv_query(request, query_id):
    return _csv_response(request, query_id, True)


def _csv_response(request, query_id, stream=False):
    query = get_object_or_404(Query, pk=query_id)
    query.params = url_get_params(request)
    return build_stream_response(query) if stream else build_download_response(query)


@change_permission
@require_POST
def download_csv_from_sql(request):
    sql = request.POST.get('sql')
    return build_download_response(Query(sql=sql, title="Playground", params=url_get_params(request)))


@change_permission
@require_GET
def schema(request):
    return render_to_response('explorer/schema.html', {'schema': schema_info()})


@require_POST
def format_sql(request):
    sql = request.POST.get('sql', '')
    formatted = fmt_sql(sql)
    return HttpResponse(json.dumps({"formatted": formatted}), content_type="application/json")

def check_query_view_perms(user, query):
    if user.is_staff:
        return True

    if query.cache_table:
        # only staff can run scheduled queries
        return False

    if user.has_perm('explorer.query_view_any'):
        return True

    user_groups = { a.id for a in user.groups.all() }

    query_groups = { a.id for a in query.groups.all()}
    if user_groups is not None and not user_groups.intersection(query_groups):
        return False

    return True

class ListQueryView(ExplorerContextMixin, ListView):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ListQueryView, self).get_context_data(**kwargs)
        context['object_list'], context['recent_queries'] = self._build_queries_and_headers()
        return context

    def get_queryset(self):
        return Query.objects.prefetch_related('created_by_user').all()

    def _build_queries_and_headers(self):
        """
        Build a list of query information and headers (pseudo-folders) for consumption by the template.

        Strategy: Look for queries with titles of the form "something - else" (eg. with a ' - ' in the middle)
                  and split on the ' - ', treating the left side as a "header" (or folder). Interleave the
                  headers into the ListView's object_list as appropriate. Ignore headers that only have one
                  child. The front end uses bootstrap's JS Collapse plugin, which necessitates generating CSS
                  classes to map the header onto the child rows, hence the collapse_target variable.

                  To make the return object homogeneous, convert the object_list models into dictionaries for
                  interleaving with the header "objects". This necessitates special handling of 'created_at'
                  and 'created_by_user' because model_to_dict doesn't include non-editable fields (created_at)
                  and will give the int representation of the user instead of the string representation.

        :return: A list of model dictionaries representing all the query objects, interleaved with header dictionaries.
        """

        recent = []
        dict_list = []
        rendered_headers = []
        pattern = re.compile('[\W_]+')

        headers = Counter([q.title.split(' - ')[0] for q in self.object_list if check_query_view_perms(self.request.user, q) ])

        for q in self.object_list:
            model_dict = model_to_dict(q)
            header = q.title.split(' - ')[0]
            collapse_target = pattern.sub('', header)

            if headers[header] > 1 and header not in rendered_headers:
                dict_list.append({'title': header,
                                  'is_header': True,
                                  'collapse_target': collapse_target,
                                  'count': headers[header]})
                rendered_headers.append(header)

            if not check_query_view_perms(self.request.user, q):
                continue

            model_dict.update({'is_in_category': headers[header] > 1,
                               'collapse_target': collapse_target,
                               'created_at': q.created_at,
                               'created_by_user': six.text_type(q.created_by_user) if q.created_by_user else None})
            dict_list.append(model_dict)
            recent.append((q.last_run_date, q))

        recent.sort(reverse=True)
        recent = recent[:app_settings.EXPLORER_RECENT_QUERY_COUNT]
        recent = [b for (a,b) in recent]

        return dict_list, recent

    model = Query


class ListQueryLogView(ExplorerContextMixin, ListView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryLogView, self).dispatch(*args, **kwargs)

    context_object_name = "recent_logs"
    model = QueryLog
    paginate_by = 20


class CreateQueryView(ExplorerContextMixin, CreateView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(CreateQueryView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by_user = self.request.user
        return super(CreateQueryView, self).form_valid(form)

    form_class = QueryForm
    template_name = 'explorer/query.html'


class DeleteQueryView(ExplorerContextMixin, DeleteView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(DeleteQueryView, self).dispatch(*args, **kwargs)

    model = Query
    success_url = reverse_lazy("explorer_index")


class PlayQueryView(ExplorerContextMixin, View):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(PlayQueryView, self).dispatch(*args, **kwargs)

    def get(self, request):
        if url_get_query_id(request):
            query = get_object_or_404(Query, pk=url_get_query_id(request))
            return self.render_with_sql(request, query)

        if url_get_log_id(request):
            log = get_object_or_404(QueryLog, pk=url_get_log_id(request))
            query = Query(sql=log.sql, title="Playground", database=log.database)
            return self.render_with_sql(request, query)

        return self.render(request)

    def post(self, request):
        sql = request.POST.get('sql')
        database = request.POST.get('database')
        show_results = request.POST.get('show', True)
        query = Query(sql=sql, title="Playground", database=database)
        query.log(request.user)
        return self.render_with_sql(request, query, show_results)

    def render(self, request):
        return self.render_template('explorer/play.html', RequestContext(request, {'title': 'Playground', 'connections': get_connections_list()}))

    def render_with_sql(self, request, query, show_results=True):
        return self.render_template('explorer/play.html', query_viewmodel(request, query, title="Playground", show_results=show_results))


class QueryView(ExplorerContextMixin, View):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(QueryView, self).dispatch(*args, **kwargs)

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        if not check_query_view_perms(self.request.user, query):
            return HttpResponseRedirect(
                reverse('explorer_index')
            )

        query.save()  # updates the modified date
        vm = query_viewmodel(request, query, form=form)
        return self.render_template('explorer/query.html', vm)

    def post(self, request, query_id):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return HttpResponseRedirect(
                reverse_lazy('query_detail', kwargs={'query_id': query_id})
            )

        query, form = QueryView.get_instance_and_form(request, query_id)
        success = form.is_valid() and form.save()
        if form.has_changed():
            query.log(request.user)

        rebuild_cache = False
        message="Query saved." if success else None
        if success and request.POST.get("rebuild"):
            rebuild_cache = True
            message="Query saved and cache rebuilt"

        vm = query_viewmodel(request, query, form=form, message=message, rebuild_cache=rebuild_cache)
        return self.render_template('explorer/query.html', vm)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query, pk=query_id)
        query.params = url_get_params(request)
        form = QueryForm(request.POST if len(request.POST) else None, instance=query)
        return query, form


def query_viewmodel(request, query, title=None, form=None, message=None, show_results=True, rebuild_cache=False):
    rows = url_get_rows(request)
    res = None
    error = None
    if show_results:
        try:
            if rebuild_cache:
                res = query.execute_cache()
            else:
                res = query.execute()
        except DatabaseError as e:
            error = str(e)
    query.log(request.user)
    return RequestContext(request, {
            'params': query.available_params(),
            'title': title,
            'shared': query.shared,
            'connection': query.database,
            'connections': get_connections_list(),
            'query': query,
            'form': form,
            'message': message,
            'error': error,
            'data': res.data[:rows] if not error and show_results else None,
            'headers': res.headers if not error and show_results else None,
            'total_rows': len(res.data) if not error and show_results else None,
            'duration': res.duration if not error and show_results else None,
            'rows': rows,
            'has_stats': len([h for h in res.headers if h.summary]) if not error and show_results else False,
            'dataUrl': reverse_lazy('query_csv', kwargs={'query_id': query.id}) if query.id else ''})
