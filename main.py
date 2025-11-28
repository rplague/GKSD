import sys
from tqdm import tqdm
import traceback
import json
import numpy as np

import config_operator
import basic_program
import gksd_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

GKSD_operator = gksd_operator.GKSD_operator()