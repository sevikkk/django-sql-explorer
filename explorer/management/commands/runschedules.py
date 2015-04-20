from datetime import datetime
from traceback import print_exc, print_tb, format_exc
from crontab import CronTab
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from explorer.models import Query, QueryLog
from pytz import UTC

class Command(BaseCommand):
    help = "Runs scheduled tasks."

    def handle(self, *args, **options):
        todo = Query.objects.all().filter(Q(schedule__isnull=False) & ~Q(schedule__startswith ='#') & ~Q(schedule = "") & Q(autorun_state = 0)).order_by("last_auto_run_date")
        #print todo.query.sql_with_params()
        for t in todo:
            c = CronTab(t.schedule)
            next_run = -c.previous()
            if t.last_auto_run_date:
                delta = (datetime.now(UTC) - t.last_auto_run_date).total_seconds()
                print t.title, t.schedule, delta, next_run
                if delta < next_run:
                    print "not yet"
                    continue
            t.last_auto_run_date=datetime.now(UTC)
            t.autorun_state = 1
            t.save()
            print t.sql
            error = None
            try:
                result = t.execute_cache()
            except Exception, e:
                error = format_exc()

            t.last_auto_run_date=datetime.now(UTC)
            if error:
                t.autorun_state = 2
                t.last_auto_run_result = error
                print "error:"
                print error
            else:
                t.autorun_state = 0
                t.last_auto_run_result = "Ok"
                if result is not None:
                    t.last_auto_run_result = "Ok, time: %.3fs, rows: %d" % (result.data[0][0], result.data[0][1])
                print "rebuild done"

            t.save()


