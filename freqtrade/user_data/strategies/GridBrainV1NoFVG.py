from GridBrainV1 import GridBrainV1Core


class GridBrainV1NoFVG(GridBrainV1Core):
    """GridBrain variant for controlled experiments with FVG gate disabled."""

    fvg_enabled = False
    defensive_fvg_enabled = False
    session_fvg_enabled = False
    session_fvg_inside_gate = False
    imfvg_enabled = False
