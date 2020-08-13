#!/usr/bin/env python

from flask import Flask

from sqlalchemy import text
from benchmark_platform_controller.conf import DATABASE_URL
from benchmark_platform_controller.models import db


app = Flask('webservice')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.app_context().push()


sql_text = """
ALTER TABLE execution
ADD artefacts varchar(255) NULL;
"""
sql = text(sql_text)
result = db.engine.execute(sql)
