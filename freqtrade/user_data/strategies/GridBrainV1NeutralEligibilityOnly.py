from GridBrainV1ExpRouterFast import GridBrainV1ExpRouterFast


class GridBrainV1NeutralEligibilityOnly(GridBrainV1ExpRouterFast):
    neutral_grid_levels_ratio = 1.0
    neutral_grid_budget_ratio = 1.0
    neutral_enter_persist_min = 10
    neutral_enter_persist_max = 12
    neutral_persistence_default_enter = 10
    neutral_cooldown_multiplier = 1.0

