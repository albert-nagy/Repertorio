import os, sys

document_root = "{}/".format(os.getcwd())

sys.path.insert(0, document_root)

from application import app as application
