from GridBrainV1 import GridBrainV1Core


class GridBrainV1NoPause(GridBrainV1Core):
    """
    Router fallback variant:
    keep mode routing active, but disable pause state so the router
    keeps operating between intraday/swing instead of parking in pause.
    """

    regime_router_allow_pause = False
    regime_router_default_mode = "intraday"
