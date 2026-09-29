""" """

import google.auth
import world_cup_vars as wc_vars

credentials, _ = google.auth.default()

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
