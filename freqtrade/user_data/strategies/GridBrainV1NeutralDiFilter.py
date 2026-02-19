from GridBrainV1ExpRouterFast import GridBrainV1ExpRouterFast


class GridBrainV1NeutralDiFilter(GridBrainV1ExpRouterFast):
    neutral_di_flip_max = 0.18

    def _regime_router_state(self, pair, clock_ts, features):
        state = super()._regime_router_state(pair, clock_ts, features)
        di_rate = features.get("di_flip_rate_4h")
        if (state.get("desired_mode") == "neutral_choppy"
                and di_rate is not None
                and float(di_rate) > float(self.neutral_di_flip_max)):
            for field in ("desired_mode", "target_mode"):
                state[field] = "intraday"
            state["desired_reason"] = "di_flip_block"
            state["target_reason"] = "di_flip_block"
        return state
