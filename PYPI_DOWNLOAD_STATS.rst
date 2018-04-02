Retrieving PyPI Download Stats
------------------------------

As of May 2016,
PyPI download stats are now available from BigQuery at:
https://bigquery.cloud.google.com/table/the-psf:pypi.downloads

Here is an example query for number of downloads in the last 30 days:

.. code:: sql

   SELECT
     DATE(timestamp) as day,
     file.project,
     file.version,
     COUNT(*) as total_downloads,
   FROM
     TABLE_DATE_RANGE(
       [the-psf:pypi.downloads],
       DATE_ADD(CURRENT_TIMESTAMP(), -1, 'month'),
       CURRENT_TIMESTAMP()
     )
   WHERE
     file.project = 'bidict'
   GROUP BY
     day, file.project, file.version
   ORDER BY
     day asc
   LIMIT
     99999999
