"""Fixtures compartidas para toda la suite de tests."""

import pandas as pd
import pytest
from call_center.cleaning import clean
from call_center.data_loader import load_raw


@pytest.fixture(scope="session")
def df_raw() -> pd.DataFrame:
    return load_raw()


@pytest.fixture(scope="session")
def df_clean(df_raw) -> pd.DataFrame:
    # Usa el pipeline en memoria para no depender del CSV procesado en disco
    return clean(df_raw)
