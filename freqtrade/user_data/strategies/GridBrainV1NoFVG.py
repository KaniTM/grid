from GridBrainV1 import GridBrainV1


class GridBrainV1NoFVG(GridBrainV1):
    """GridBrain variant for controlled experiments with FVG gate disabled."""

    fvg_enabled = False
    defensive_fvg_enabled = False
    session_fvg_enabled = False
    session_fvg_inside_gate = False
    imfvg_enabled = False
