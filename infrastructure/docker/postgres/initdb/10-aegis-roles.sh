#!/bin/sh
# Creates the AEGIS database and its roles (DECISIONS.md D-054).
#
# Run by the postgres image's entrypoint, once, when the data directory is
# first initialized (/docker-entrypoint-initdb.d). It never runs against an
# existing database, and it never drops anything.
#
# - aegis_owner: owns the database and schema; used only by the migration job
#   (alembic upgrade head). Not a superuser; cannot create databases or roles.
# - aegis_app: used by the API and the internal worker. Can read and change
#   rows, but cannot create, alter or drop tables.
# - The superuser can connect only through the local socket inside this
#   container, never over the network.
#
# Written to be sourced by the entrypoint (it runs .sh files that are not
# executable that way): it defines a function and changes no shell options.

aegis_create_roles() {
    aegis_owner_password="$(cat /run/secrets/postgres_owner_password)"
    aegis_app_password="$(cat /run/secrets/postgres_app_password)"

    # Passwords are passed as psql variables and quoted by psql (:'name'),
    # so they can contain any character.
    psql -v ON_ERROR_STOP=1 --no-psqlrc --username "$POSTGRES_USER" --dbname postgres \
        -v owner_password="$aegis_owner_password" \
        -v app_password="$aegis_app_password" <<'SQL'
CREATE ROLE aegis_owner LOGIN PASSWORD :'owner_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE aegis_app LOGIN PASSWORD :'app_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

CREATE DATABASE aegis OWNER aegis_owner;
REVOKE ALL ON DATABASE aegis FROM PUBLIC;
GRANT CONNECT ON DATABASE aegis TO aegis_app;
REVOKE CONNECT ON DATABASE postgres FROM PUBLIC;

\connect aegis
ALTER SCHEMA public OWNER TO aegis_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO aegis_app;

-- Tables and sequences created by migrations (as aegis_owner) are usable by
-- the application for data access only.
ALTER DEFAULT PRIVILEGES FOR ROLE aegis_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aegis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE aegis_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO aegis_app;
SQL

    unset aegis_owner_password aegis_app_password

    # First matching rule wins: refuse the superuser over TCP before the
    # image's general "host all all all scram-sha-256" rule.
    sed -i '1i host all postgres all reject' "$PGDATA/pg_hba.conf"
}

aegis_create_roles
