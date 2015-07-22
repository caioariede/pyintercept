from .handlers.json_handler import json
from .handlers.pickle_handler import pickle
from .handlers.print_handler import print_
from .handlers.pdb_handler import pdb

locals()['print'] = print_
