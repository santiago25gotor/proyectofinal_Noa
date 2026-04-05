"""
utils/
======
Módulo de utilidades del proyecto Brecha Digital Discapacidad España.
"""

from .helpers import (
    load_and_clean,
    compute_derived_metrics,
    decode_ind_type,
    setup_style,
    bar_chart_brecha,
    save_figure,
    get_figures_path,
    get_outputs_path,
    PALETTE,
    COUNTRY_COLORS,
    COUNTRY_NAMES_ES,
)

__all__ = [
    "load_and_clean",
    "compute_derived_metrics",
    "decode_ind_type",
    "setup_style",
    "bar_chart_brecha",
    "save_figure",
    "get_figures_path",
    "get_outputs_path",
    "PALETTE",
    "COUNTRY_COLORS",
    "COUNTRY_NAMES_ES",
]
