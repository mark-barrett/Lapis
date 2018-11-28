# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
from __future__ import absolute_import, unicode_literals

import os
import django
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RESTBroker.settings')

django.setup()

app = Celery('tasks', broker='pyamqp://guest@localhost//', backend='rpc://guest@localhost//',)

from sshtunnel import SSHTunnelForwarder
import MySQLdb as db
from core.models import Database, DatabaseTable, Project, DatabaseColumn


@app.task(name='build_database')
def build_database(project_id, ssh_address, ssh_user, ssh_password,
                   database_name, database_user, database_password):

    try:
        with SSHTunnelForwarder(
            (ssh_address, 22),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=('127.0.0.1', 3306),
        ) as server:
            try:
                conn = db.connect(host='127.0.0.1', port=server.local_bind_port,
                                  user=database_user, password=database_password,
                                  database='information_schema')

                project = Project.objects.get(id=project_id)

                # Now that we know we can connect, let's construct a database object
                database = Database(
                    name=database_name,
                    user=database_user,
                    password=database_password,
                    ssh_username=ssh_user,
                    ssh_password=ssh_password,
                    server_address=ssh_address,
                    project=project
                )

                print("Hello World")

                database.save()

                cursor = conn.cursor()
                cursor2 = conn.cursor()

                # Get all of the tables in that database
                cursor.execute("SELECT * FROM information_schema.tables WHERE table_schema='%s'" % database_name)

                for row in cursor:
                    database_table = DatabaseTable(
                        name=row[2],
                        database=database
                    )

                    database_table.save()

                    # For each row, get the columns in that table
                    cursor2.execute("SELECT * FROM information_schema.columns WHERE table_name='%s'" % row[2])

                    for inner_row in cursor2:
                        database_column = DatabaseColumn(
                            name=inner_row[3],
                            type=inner_row[7],
                            table=database_table
                        )

                        database_column.save()


                # Set the "database built" in the project ot true.
                project.database_built = True
                project.save()

                return 'Built Database'

            except Exception as e:

                return str(e)

    except Exception as e:

        return str(e)
