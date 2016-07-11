===============================
excerpt
===============================


Excerpt is a cli for generating database extracts from simple dump
specifications.

Example
-------

Create a file with you dump specification:

.. code:: yaml

    # dump.yml
    host: ""
    port: ""
    username: ""
    password: ""
    db: ""
    tables:
      - name: source_metrics
        where: "1"
      - name: source_metrics
        where: "source_group_id=1 ORDER BY id desc LIMIT 10"


And then run the CLI with the spec.

.. code:: bash

   excerpt $SERVICE_NAME dump.yml


This will generate a docker command for you to copy and paste into your terminal, which
will start a container with the dump you created.


Features
--------

* Creates static dumps of data with a simple yaml DSL that you can share with others.


Roadmap
-------
* Improve the DSL to auto-generate subqueries based on relationships.
* Add a directive for limiting the number of row within each table and each relationship.


Requirements
------------

- Python >= 2.7 or >= 3.3
