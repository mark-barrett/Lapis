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
def build_database(project_id, server_address,
                   database_name, database_user, database_password):

    # Try connect to the database by its name to check if it exists.
    try:
        conn = db.connect(host=server_address, port=3306,
                          user=database_user, password=database_password,
                          database=database_name)

        # If all good close the connection
        conn.close()

        # Now try to actually build the database
        try:
            conn = db.connect(host=server_address, port=3306,
                              user=database_user, password=database_password,
                              database='information_schema')

            project = Project.objects.get(id=project_id)

            # Now that we know we can connect, let's construct a database object
            database = Database(
                name=database_name,
                user=database_user,
                password=database_password,
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

                query = "SELECT * FROM information_schema.columns WHERE table_name='{0}' AND table_schema='{1}'".format(
                    row[2], database_name)

                # For each row, get the columns in that table
                cursor2.execute(query)

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

            # Close all the stuff
            cursor.close()
            cursor2.close()
            conn.close()

            return 'Built Database'

        except Exception as e:

            return str(e)

    except Exception as e:

        return str(e)


