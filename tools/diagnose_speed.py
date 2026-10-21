"""Run this when the app feels slow:   python tools/diagnose_speed.py
It prints your library versions, your computer and how long every step takes on the demo data.
On a normal computer the whole thing finishes in about 5 seconds; 'clean_data' takes under 2 seconds."""
import os
from pathlib import Path
import platform
import sys
import time
import warnings

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import sklearn
import streamlit

print(f"Python {platform.python_version()} | pandas {pd.__version__} | numpy {np.__version__} | "
      f"scikit-learn {sklearn.__version__} | streamlit {streamlit.__version__}")
print(f"{platform.system()} {platform.release()} | CPU cores: {os.cpu_count()}")
try:
    import psutil
    memory = psutil.virtual_memory()
    python_processes = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower().startswith("python")]
    print(f"RAM: {memory.available / 1e9:.1f} GB free of {memory.total / 1e9:.1f} GB ({memory.percent}% used) | "
          f"CPU load now: {psutil.cpu_percent(interval=1)}% | python processes running: {len(python_processes)}")
except ImportError:
    print("(install psutil to also see RAM, CPU load and running python processes:  pip install psutil)")

from src.data import clean_data
from src.forecast import forecast_monthly
from src.model import train_and_evaluate
from src.security import prepare_table


def timed(name, function):
    start = time.time()
    result = function()
    print(f"  {name:28s} {time.time() - start:6.1f} s")
    return result


import joblib  # noqa: E402
print(f"joblib {joblib.__version__}")
print("\nTiming on the English demo data (10,194 rows):")
raw = timed("read csv + prepare_table", lambda: prepare_table(pd.read_csv(ROOT / "data" / "sample_superstore.csv")))
df, _ = timed("clean_data", lambda: clean_data(raw))
timed("train_and_evaluate", lambda: train_and_evaluate(df))
timed("forecast_monthly", lambda: forecast_monthly(df, "Sales", 3))

# Is it faster with all cores or with one? (the setting SALES_ML_JOBS)
from src.model import add_unit_price, build_model  # noqa: E402
data = add_unit_price(df)
pipeline, columns = build_model(data)
results = {}
print("\nRandomForest training with different numbers of cores:")
for jobs in (1, -1):
    pipeline.set_params(classifier__n_jobs=jobs)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        start = time.time()
        pipeline.fit(data[columns], data["Profitable"])
        results[jobs] = time.time() - start
    print(f"  n_jobs={jobs:>2}: {results[jobs]:6.1f} s   (warnings printed: {len(caught)})")
if results[-1] > results[1] * 1.3:
    print("\n  -> All cores is SLOWER on this computer. Use one core, in the SAME window where you start the app:")
    print('       PowerShell:  $env:SALES_ML_JOBS="1"      CMD:  set SALES_ML_JOBS=1      Linux/Mac:  export SALES_ML_JOBS=1')
else:
    print("\n  -> The default (all cores) is fine on this computer.")
print("\nSend me this whole output if 'clean_data' takes more than 5 seconds.")
