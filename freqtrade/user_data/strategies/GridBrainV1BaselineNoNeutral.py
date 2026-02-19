from GridBrainV1ExpRouterFast import GridBrainV1ExpRouterFast


class GridBrainV1BaselineNoNeutral(GridBrainV1ExpRouterFast):
    regime_router_enabled = False
    regime_router_force_mode = "intraday"
