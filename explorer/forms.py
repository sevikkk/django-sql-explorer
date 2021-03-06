from django import forms
from django.forms import ModelForm, Field, ValidationError
from explorer.models import Query, MSG_FAILED_BLACKLIST
from django.db import DatabaseError, connections
from crontab import CronTab
from explorer.utils import get_connections_list

_ = lambda x: x


class SqlField(Field):

    def validate(self, value):
        """
        Ensure that the SQL passes the blacklist and executes. Execution check is skipped if params are present.

        :param value: The SQL for this Query model.
        """

        query = Query(sql=value)

        error = MSG_FAILED_BLACKLIST if not query.passes_blacklist() else None

        #if not error and not query.available_params():
        #    try:
        #        query.try_execute()
        #    except DatabaseError as e:
        #        error = str(e)

        if error:
            raise ValidationError(
                _(error),
                code="InvalidSql"
            )

class CrontabField(Field):

    def validate(self, value):
        """
        Ensure that the field is valid crontab entry

        :param value: The schedule entry for this Query model.
        """

        error = None

        if not value:
            return

        if value.startswith('#'):
            return

        try:
            cron = CronTab(value)
        except ValueError, e:
            error = str(e)

        if error:
            raise ValidationError(
                _(error),
                code="InvalidCrontabEntry"
            )

class DatabaseField(forms.ChoiceField):

    def __init__(self, *args, **kwargs):
        super(DatabaseField, self).__init__(choices=get_connections_list(), *args, **kwargs)

    def validate(self, value):
        """
        Ensure that the field is valid crontab entry

        :param value: The schedule entry for this Query model.
        """

        error = None

        if not value:
            return

        if value not in connections._databases:
            error = "Connection is not configured, known connections: %s" % (", ".join(connections._databases.keys()))

        if error:
            raise ValidationError(
                _(error),
                code="InvalidDatabase"
            )



class QueryForm(ModelForm):

    sql = SqlField()
    schedule = CrontabField()
    database = DatabaseField()

    def clean(self):
        if self.instance and self.data.get('created_by_user', None):
            self.cleaned_data['created_by_user'] = self.instance.created_by_user
        return super(QueryForm, self).clean()

    @property
    def created_by_user_email(self):
        return self.instance.created_by_user.email if self.instance.created_by_user else '--'

    @property
    def created_by_user_id(self):
        return self.instance.created_by_user.id if self.instance.created_by_user else '--'

    class Meta:
        model = Query
        fields = ['title', 'sql', 'description', 'created_by_user', 'database', 'cache_table', 'schedule', 'groups']