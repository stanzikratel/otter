"""
:module:`otter.worker.launch_server_v1`-specific code for RackConnect v3.

At some point, this should just be moved into that module.
"""
from functools import partial

from effect import Effect
from effect.twisted import perform

from otter.convergence.effecting import steps_to_effect
from otter.convergence.steps import BulkAddToRCv3, BulkRemoveFromRCv3
from otter.http import TenantScope


def _generic_rcv3_request(step_class, request_bag, lb_id, server_id):
    """
    Perform a generic RCv3 bulk step on a single (lb, server) pair.

    :param IStep step_class: The step class to perform the action.
    :param request_bag: An object with a bunch of useful data on it. Called
        a ``request_func`` by other worker/supervisor code.
    :param str lb_id: The id of the RCv3 load balancer to act on.
    :param str server_id: The Nova server id to act on.
    :return: A deferred that will fire when the request has been performed,
        firing with the parsed result of the request, or :data:`None` if the
        request has no body.
    """
    step = step_class(lb_node_pairs=[(lb_id, server_id)])
    effect = steps_to_effect([step])
    # Unfortunate that we have to TenantScope here, but here's where we're
    # performing.
    scoped = Effect(TenantScope(effect, request_bag.tenant_id))

    d = perform(request_bag.dispatcher, scoped)

    def get_response_body(result):
        # The body must be provided for adding, because that is stored in
        # the DB so that the worker can delete the server and remove it
        # from all the load balancers later.  The body is unimportant for
        # deletes.

        # TODO: when/before #956 lands, this needs refactoring
        if result[0] is None:
            assert step_class == BulkRemoveFromRCv3
            return None
        else:
            _response, body = result[0]
            return body

    return d.addCallback(get_response_body)


add_to_rcv3 = partial(_generic_rcv3_request, BulkAddToRCv3)
remove_from_rcv3 = partial(_generic_rcv3_request, BulkRemoveFromRCv3)
