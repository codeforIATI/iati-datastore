Data Error API
==============

Health status
-------------

Check the health status of the Datstore.

   `</api/1/about>`_

If the last fetch, last successful fetch, or last parsed date is
more than 24 hours ago, ``ok`` will be `false` and ``healthy`` will
be `unhealthy`.

If the last fetch, last successful fetch, or last parsed date is
less than 24 hours ago, ``ok`` will be `true` and ``healthy`` will
be `healthy`.


General data
------------

To retrieve metadata on the datasets known to the datastore.

-  ``/api/1/about/dataset`` retrieves the list of datasets currently in
   the datastore
-  ``/api/1/about/dataset/<dataset>`` retrieves specific details on the
   dataset

   -  ``last_modified`` - the date stamp that the dataset was updated in
      the IATI registry.
   -  ``resources``

      -  ``url`` - url datastore used to fetch the resource
      -  ``last_fetch`` - last time a fetch was attempted
      -  ``last_successful_fetch`` - latest date the datastore
         successfully fetched the resource
      -  ``last_status_code`` - last http status code on fetch
      -  ``last_parsed`` - last date resource was successfully parsed
      -  ``num_of_activities`` number of activities datastore has
         successfully parsed and stored

Errors
------

To retrieve detailed data on the errors encountered by the parser

In JSON
~~~~~~~

-  ``/api/1/error/dataset`` retrieves the list of datasets that have
   errored (in no order)

   -  ``dataset`` - name of dataset that contains errors
   -  ``logger`` - 'queue' indicates dataset errored whilst fetching and
      storing the resource whilst 'Parser' indicates that the resource
      was successfully fetched but failed whilst parsing activities

-  ``/api/1/error/dataset/<dataset_id>`` retrieves the list of datasets
   that have errored (in no order)

   -  ``datestamp`` - date/time that the error occurred
   -  ``resource_url`` - url of the errored resource/dataset
   -  ``msg`` - error message
   -  ``traceback`` - detailed traceback of error, useful if you are a
      developer, please include this any reports on errors
   -  ``logger`` - logger that reported the error

In plaintext
~~~~~~~~~~~~

You can also fetch a list of datasets
``wget https://datastore.codeforiati.org/api/1/error/dataset.log``

Detailed logs can be recreated using
``wget https://datastore.codeforiati.org/api/1/error/dataset.log/<dataset_id>``
sorted by date \`
