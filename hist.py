import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

raw_df = pd.read_csv(sys.argv[1])
df = raw_df[raw_df["peak_height"] > int(sys.argv[2])]
df.hist("peak_height", bins=1024)
plt.show()
