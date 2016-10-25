import os
import sys


# Virtualenv settings
#activate_this = "/var/www/html/data_quality_dashboard/venv/activate_this.py"
#execfile(activate_this, dict(__file__=activate_this))

# Replace stdout
sys.stdout = sys.stderr

# Add this file path to sys.path in order to import settings
#sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))

# Add this file path to sys.path in order to import app
sys.path.append("/var/www/data-quality-dashboard/")

# Create application for our app
from test_auth import app as application
