FROM postgres:10.5

COPY init.sql /docker-entrypoint-initdb.d/

################################################################################

# This can be used to define a different name for the default database
# that is created when the image is first started. If it is not
# specified, then the value of `POSTGRES_USER` will be used.
ENV POSTGRES_DB postgres

# This is used in conjunction with `POSTGRES_PASSWORD` to set a user
# and its password. This variable will create the specified user with
# superuser power and a database with the same name. If it is not
# specified, then the default user of postgres will be used.
ENV POSTGRES_USER postgres

# This is the superuser password for PostgreSQL. The default superuser
# is defined by the `POSTGRES_USER` environment variable.
ENV POSTGRES_PASSWORD mysecretpassword
