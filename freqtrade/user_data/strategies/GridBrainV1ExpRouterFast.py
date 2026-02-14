from GridBrainV1 import GridBrainV1


class GridBrainV1ExpRouterFast(GridBrainV1):
    """
    Experiment variant:
    - Faster mode-switch persistence
    - Lower mode-switch score margin
    """

    regime_router_switch_persist_bars = 3
    regime_router_switch_margin = 0.5
