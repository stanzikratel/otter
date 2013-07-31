"""
Autoscale REST endpoints having to do with internal metrics.

(/metrics)
"""

import json

from otter.util import timestamp

from otter.rest.application import app, get_store
from otter.rest.decorators import fails_with, succeeds_with
from otter.rest.errors import exception_codes


@app.route('/metrics', methods=['GET'])
@fails_with(exception_codes)
@succeeds_with(200)
def get_metrics(request, log):
    """
    Get a list of metrics from cassandra.

    Example response::

        {
            "metrics": [
                {
                    "id": "otter.metrics.scaling_groups",
                    "value": 3207,
                    "time": 13120497123
                },
                {
                    "id": "otter.metrics.scaling_policies",
                    "value": 2790,
                    "time": 13139792343
                }
            ]
        }
    """
    def format_data(results):
        """
        :param results: Results from running the collect_metrics call.

        :return: Correctly formatted data to be jsonified.
        """
        metrics = []
        for key, value in results.iteritems():
            metrics.append(dict(
                id="otter.metrics.{0}".format(key),
                value=value,
                time=timestamp.now()))

        return {'metrics': metrics}

    deferred = get_store().get_metrics(log)
    deferred.addCallback(format_data)
    deferred.addCallback(json.dumps)
    return deferred
