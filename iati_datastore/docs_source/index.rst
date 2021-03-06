Home
====

What is IATI Datastore?
-----------------------

The Datastore is an online service that gathers all data published to the IATI standard into a single queryable source. This can deliver selections of IATI data in JSON or XML formats, or CSV (spreadsheet) for less-technical users.

What is IATI Datastore Classic?
-------------------------------

The *IATI Datastore* was originally built in 2013 by the `Open Knowledge Foundation <https://okfn.org/>`_. `Code for IATI <https://codeforiati.org>`_ has updated the software to use Python3 and modern dependencies. Over time, we will include other bugfixes and feature improvements. Our fork of the software is called *IATI Datastore Classic*.

How does it work?
-----------------

Data that is recorded on the `IATI Registry <https://iatiregistry.org/>`__, and is valid against the standard, is pulled into the Datastore on a nightly basis. This enables people to query for IATI activities across several facets (eg: country, publisher, sector). Activities that satisfy the criteria can then be access in XML, JSON or CSV (spreadsheet) format.

Who is it for?
--------------

The Datastore is a service for analysts, data journalists, infomediaries and developers. It is a ‘back-end’ service to streamline the work of those who wish to build applications that can deliver accessible and usable information to a wide range of users.

Why a Datastore?
----------------

This repository is called a Datastore, not a database, because it cannot be used as a single dataset. IATI is a publishing standard, not an integral information system. One activity can be reported through IATI by a donor, an implementing organisation and a third-party (secondary-source publisher): in other words you cannot simply add everything together.

How to access the Datastore
---------------------------

* :doc:`An API </api/>` is available that enables people to construct queries.

* For those wishing to just access the data in CSV format, an `online form </#get-the-data>`__ is available to assist with queries

Are there any limitations on the Datastore?
-------------------------------------------

In its current format the Datastore allows you to filter IATI activities by publisher, organisation type, sector, or country as well as by the date of the most recent update. In future all fields will be queryable.

+---------------------+------+------+------+
| Query               |  XML | JSON |  CSV |
+---------------------+------+------+------+
|iati-identifier      | yes  | yes  | yes  |
+---------------------+------+------+------+
|reporting-org        | yes  | yes  | yes  |
+---------------------+------+------+------+
|title                | yes  | yes  | yes  |
+---------------------+------+------+------+
|description          | yes  | yes  | yes  |
+---------------------+------+------+------+
|participating-org    | yes  | yes  | yes  |
+---------------------+------+------+------+
|other-identifier     | yes  | yes  | no   |
+---------------------+------+------+------+
|activity-status      | yes  | yes  | yes  |
+---------------------+------+------+------+
|activity-date        | yes  | yes  | yes  |
+---------------------+------+------+------+
|contact-info         | yes  | yes  | no   |
+---------------------+------+------+------+
|activity-scope       | yes  | yes  | no   |
+---------------------+------+------+------+
|recipient-country    | yes  | yes  | yes  |
+---------------------+------+------+------+
|recipient-region     | yes  | yes  | yes  |
+---------------------+------+------+------+
|location             | yes  | yes  | no   |
+---------------------+------+------+------+
|sector               | yes  | yes  | yes  |
+---------------------+------+------+------+
|country-budget-items | yes  | yes  | no   |
+---------------------+------+------+------+
|humanitarian-scope   | yes  | yes  | no   |
+---------------------+------+------+------+
|policy-marker        | yes  | yes  | no   |
+---------------------+------+------+------+
|collaboration-type   | yes  | yes  | yes  |
+---------------------+------+------+------+
|default-flow-type    | yes  | yes  | yes  |
+---------------------+------+------+------+
|default-finance-type | yes  | yes  | yes  |
+---------------------+------+------+------+
|default-aid-type     | yes  | yes  | yes  |
+---------------------+------+------+------+
|default-tied-status  | yes  | yes  | yes  |
+---------------------+------+------+------+
|budget               | yes  | yes  | no   |
+---------------------+------+------+------+
|planned-disbursement | yes  | yes  | no   |
+---------------------+------+------+------+
|capital-spend        | yes  | yes  | no   |
+---------------------+------+------+------+
|transaction          | yes  | yes  | no   |
+---------------------+------+------+------+
|document-link        | yes  | yes  | no   |
+---------------------+------+------+------+
|related-activity     | yes  | yes  | no   |
+---------------------+------+------+------+
|legacy-data          | yes  | yes  | no   |
+---------------------+------+------+------+
|conditions           | yes  | yes  | no   |
+---------------------+------+------+------+
|result               | yes  | yes  | no   |
+---------------------+------+------+------+
|crs-add              | yes  | yes  | no   |
+---------------------+------+------+------+
|fss                  | no   | no   | no   |
+---------------------+------+------+------+

In its current CSV format the Datastore allows three different row outputs: where each row represents an activity, transaction or budget item. In future sub-national geographic information and results reporting will also be available.
