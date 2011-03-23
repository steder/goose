Goose_
----------------------

About
======================

Goose is a tool for managing and applying SQL Database Migrations.

Because our geese use SQLAlchemy to manage their migration tables
you can connect to and migrate any database supported by SQLAlchemy.

Migrations are just plain SQL files and the order migrations are applied
is specified through configuration in a YAML file.

Usage
=======================

First initialize your database by installing the migration_info table::

  goose -d sqlite:///my.db -m migrations/ init

Now go ahead and migrate::
  
  goose -d sqlite:///my.db -m migrations/ migrate

To find out what migrations have been applied you can do::

  goose -d sqlite:///my.db -m migrations/ list

Installation
======================

pip install pyyaml
pip install sqlalchemy

And install whichever DB API driver you need for your specific DB:

pip install psycopg2

Project Layout
======================

Assuming you have a project you want to add migrations to in a directory like this::

  MyApp
  |-- README
  `-- package
      |-- __init__.py
      `-- somecode.py
  
You could add migrations like this::

  MyApp
  |-- README
  |-- package/
  |   |-- __init__.py
  |   `-- somecode.py
  `-- migrations/
      |-- create_user_tables.sql
      |-- db_skeleton.sql
      |-- index.yaml
      `-- update_users.sql

The contents of index.yaml would look like::

  migrations:
    - db_skeleton.sql
    - create_user_tables.sql
    - update_users.sql
    
.. _goose: http://bitbucket.org/steder/goose
.. _Michael Steder: http://penzilla.net
