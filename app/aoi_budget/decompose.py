"""Split an estimate's error into quantity x unit list price x discount (docs/accuracy-target.md).

Cost = sum over categories of quantity x unit list x (1 - discount). On a log scale the error of
each category splits exactly into three parts:

    log(est / actual) = log(q_est / q_act)
                      + log(list_est / list_act)
                      + log(net_share_est / net_share_act)

where net_share = 1 - discount. The project's total error is the cost-weighted combination, so
we report each part weighted by the actual cost share of its category. When a source gives only
net unit prices (no list), list and discount cannot be separated: they are reported together as
"unit net price".
"""

from dataclasses import dataclass
from math import log


@dataclass(frozen=True)
class LineCost:
    category: str
    quantity: float
    unit_list: float | None  # None when only a net price is known
    unit_net: float


@dataclass(frozen=True)
class Attribution:
    quantity: float  # cost-weighted log error parts; sum = log(total_est / total_act) approx
    unit_list: float | None
    discount: float | None
    unit_net: float  # list + discount combined (always available)
    total_log_error: float


def decompose(estimate: list[LineCost], actual: list[LineCost]) -> Attribution:
    est = {line.category: line for line in estimate}
    act = {line.category: line for line in actual}
    shared = sorted(est.keys() & act.keys())
    if not shared:
        raise ValueError("no categories in common")
    total_act = sum(act[c].quantity * act[c].unit_net for c in shared)
    total_est = sum(est[c].quantity * est[c].unit_net for c in shared)
    q = ul = d = un = 0.0
    split_ok = all(est[c].unit_list and act[c].unit_list for c in shared)
    for c in shared:
        w = act[c].quantity * act[c].unit_net / total_act
        q += w * log(est[c].quantity / act[c].quantity)
        un += w * log(est[c].unit_net / act[c].unit_net)
        if split_ok:
            ul += w * log(est[c].unit_list / act[c].unit_list)
            share_est = est[c].unit_net / est[c].unit_list
            share_act = act[c].unit_net / act[c].unit_list
            d += w * log(share_est / share_act)
    return Attribution(
        quantity=q,
        unit_list=ul if split_ok else None,
        discount=d if split_ok else None,
        unit_net=un,
        total_log_error=log(total_est / total_act),
    )
