from explorer.utils import passes_blacklist, swap_params, extract_params, shared_dict_update, get_connection
from django.db import models, DatabaseError
from time import time
from django.core.urlresolvers import reverse
from django.conf import settings
import app_settings
import logging
import six

MSG_FAILED_BLACKLIST = "Query failed the SQL blacklist."


logger = logging.getLogger(__name__)


class Query(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run_date = models.DateTimeField(auto_now=True)
    cache_table = models.CharField(max_length=40, null=True, blank=True)
    database = models.CharField(max_length=40, null=True, blank=True)
    schedule = models.CharField(max_length=40, null=True, blank=True)
    last_auto_run_date = models.DateTimeField(null=True,blank=True)
    last_auto_run_result = models.TextField(null=True,blank=True, max_length=10000)
    autorun_state= models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        self.params = kwargs.get('params')
        kwargs.pop('params', None)
        super(Query, self).__init__(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Queries'

    def __unicode__(self):
        return six.text_type(self.title)

    def passes_blacklist(self):
        return passes_blacklist(self.final_sql())

    def final_sql(self):
        return swap_params(self.sql, self.params)

    def try_execute(self):
        """
        A lightweight version of .execute to just check the validity of the SQL.
        Skips the processing associated with QueryResult.
        """
        QueryResult(self.final_sql(), self.database)

    def execute(self):
        ret = QueryResult(self.final_sql(), self.database)
        ret.process()
        return ret

    def execute_cache(self):
        """
        A lightweight version of .execute to just check the validity of the SQL.
        Skips the processing associated with QueryResult.
        """
        if not self.cache_table:
            return

        sql = "drop table if exists %(table)s; create table %(table)s as %(sql)s" % {
            "table": self.cache_table,
            "sql": self.sql
        }

        t = time()
        QueryResult(sql, self.database)
        t = time() - t

        sql = "select %(t)f as rebuild_time, count(*) as row_count from %(table)s" % {
            "table": self.cache_table,
            "t": t
        }
        ret = QueryResult(sql, self.database)
        ret.process()
        return ret

    def available_params(self):
        """
            Merge parameter values into a dictionary of available parameters

        :param param_values: A dictionary of Query param values.
        :return: A merged dictionary of parameter names and values. Values of non-existent parameters are removed.
        """

        p = extract_params(self.sql)
        if self.params:
            shared_dict_update(p, self.params)
        return p

    def get_absolute_url(self):
        return reverse("query_detail", kwargs={'query_id': self.id})

    def log(self, user):
        log_entry = QueryLog(sql=self.sql, query_id=self.id, run_by_user=user, is_playground=not bool(self.id))
        log_entry.save()

    @property
    def shared(self):
        return self.id in set(sum(app_settings.EXPLORER_GET_USER_QUERY_VIEWS().values(), []))


class QueryLog(models.Model):

    sql = models.TextField()
    query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.SET_NULL)
    is_playground = models.BooleanField(default=False)
    run_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    run_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-run_at']


class QueryResult(object):

    def __init__(self, sql, database = None):

        self.sql = sql
        self.database = database

        cursor, duration = self.execute_query()

        self._description = cursor.description or []
        self._data = [list(r) for r in cursor.fetchall()]
        self.duration = duration

        cursor.close()

        self._headers = self._get_headers()
        self._summary = {}

    @property
    def data(self):
        return self._data or []

    @property
    def headers(self):
        return self._headers or []

    def _get_headers(self):
        return [ColumnHeader(d[0]) for d in self._description] if self._description else [ColumnHeader('--')]

    def _get_numerics(self):
        conn = get_connection(self.database)
        if hasattr(conn.Database, "NUMBER"):
            return [ix for ix, c in enumerate(self._description) if hasattr(c, 'type_code') and c.type_code in conn.Database.NUMBER.values]
        elif self.data:
            d = self.data[0]
            return [ix for ix, _ in enumerate(self._description) if not isinstance(d[ix], six.string_types) and six.text_type(d[ix]).isnumeric()]
        return []

    def _get_unicodes(self):
        if len(self.data):
            return [ix for ix, c in enumerate(self.data[0]) if type(c) is six.text_type]
        return []

    def _get_transforms(self):
        transforms = dict(app_settings.EXPLORER_TRANSFORMS)
        return [(ix, transforms[str(h)]) for ix, h in enumerate(self.headers) if str(h) in transforms.keys()]

    def column(self, ix):
        return [r[ix] for r in self.data]

    def process(self):
        start_time = time()

        self.process_columns()
        self.process_rows()

        logger.info("Explorer Query Processing took in %sms." % ((time() - start_time) * 1000))

    def process_columns(self):
        for ix in self._get_numerics():
            self.headers[ix].add_summary(self.column(ix))

    def process_rows(self):
        unicodes = self._get_unicodes()
        transforms = self._get_transforms()
        for r in self.data:
            for u in unicodes:
                r[u] = r[u].encode('utf-8') if r[u] is not None else r[u]
            for ix, t in transforms:
                r[ix] = t.format(str(r[ix]))

    def execute_query(self):
        conn = get_connection(self.database)
        cursor = conn.cursor()
        start_time = time()

        try:
            cursor.execute(self.sql)
        except DatabaseError as e:
            cursor.close()
            raise e

        return cursor, ((time() - start_time) * 1000)


class ColumnHeader(object):

    def __init__(self, title):
        self.title = title
        self.summary = None

    def add_summary(self, column):
        self.summary = ColumnSummary(self, column)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


class ColumnStat(object):

    def __init__(self, label, statfn, precision=2, handles_null=False):
        self.label = label
        self.statfn = statfn
        self.precision = precision
        self.handles_null = handles_null

    def __call__(self, coldata):
        self.value = round(float(self.statfn(coldata)), self.precision) if coldata else 0

    def __unicode__(self):
        return self.label

    def foo(self):
        return "foobar"


class ColumnSummary(object):

    def __init__(self, header, col):
        self._header = header
        self._stats = [
            ColumnStat("Sum", sum),
            ColumnStat("Avg", lambda x: float(sum(x)) / float(len(x))),
            ColumnStat("Min", min),
            ColumnStat("Max", max),
            ColumnStat("NUL", lambda x: int(sum(map(lambda y: 1 if y is None else 0, x))), 0, True)
        ]
        without_nulls = list(map(lambda x: 0 if x is None else x, col))

        for stat in self._stats:
            stat(col) if stat.handles_null else stat(without_nulls)

    @property
    def stats(self):
        # dict comprehensions are not supported in Python 2.6, so do this instead
        return dict((c.label, c.value) for c in self._stats)

    def __str__(self):
        return str(self._header)