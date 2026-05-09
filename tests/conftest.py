"""Fixtures compartidas para toda la suite de tests."""

import pytest
import pandas as pd
from pathlib import Path

from call_center.data_loader import load_raw, load_clean
from call_center.cleaning import clean


@pytest.fixture(scope="session")
def df_raw() -> pd.DataFrame:
    return load_raw()


@pytest.fixture(scope="session")
def df_clean(df_raw) -> pd.DataFrame:
    # Usa el pipeline en memoria para no depender del CSV procesado en disco
    return clean(df_raw)
