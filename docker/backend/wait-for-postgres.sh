#!/bin/sh
# wait-for-postgres.sh

set -e

host="postgres"
db_name="crm_db"
db_user="crm_user"
db_password="crm_password"

until PGPASSWORD=$db_password psql -h "$host" -U "$db_user" -d "$db_name" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
python manage.py migrate
python manage.py runserver 0.0.0.0:8000