from GridBrainV1 import GridBrainV1Core


class GridBrainV1ExpRouterFast(GridBrainV1Core):
    """
    Experiment variant:
    - Faster mode-switch persistence
    - Lower mode-switch score margin
    """

    regime_router_switch_persist_bars = 3
    regime_router_switch_margin = 0.5
