"""Shared fixtures for the Study 3 tool test suites (dedup finding):
one home for the validity-screen-passing reply text and the ResultKey
factory, so screen-threshold or proto changes update once. A plain
module rather than conftest members — conftest names collide across the
repo's several test trees."""
from modelwelfare.v1 import common_pb2

GOOD_REPLY = ("a perfectly substantial reply with plenty of distinct words "
              "in it so the lexical screen is satisfied entirely")


def make_result_key(experiment_id, condition_id, item_id, sample_index=0):
    return common_pb2.ResultKey(experiment_id=experiment_id,
                                condition_id=condition_id,
                                item_id=item_id, sample_index=sample_index)
