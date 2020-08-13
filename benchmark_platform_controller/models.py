from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy_jsonfield

# from benchmark_platform_controller.conf import DATABASE_URL

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# db = SQLAlchemy(app)

db = SQLAlchemy()


class ExecutionModel(db.Model):
    __tablename__ = 'execution'

    STATUS_RUNNING = 'RUNNING'
    STATUS_FINISHED = 'FINISHED'
    STATUS_CLEANUP = 'CLEANUP'

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.String(250), nullable=False)
    shutdown_id = db.Column(db.String(250), nullable=True)
    status = db.Column(db.String(250), default=STATUS_RUNNING)
    json_results = db.Column(
        sqlalchemy_jsonfield.JSONField(
            # MariaDB does not support JSON for now
            enforce_string=True,
            # MariaDB connector requires additional parameters for correct UTF-8
            enforce_unicode=False
        ),
        nullable=True
    )
    artefacts = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return f'<id: {self.id}, result_id:{self.result_id}, shutdown_id:{self.shutdown_id}, json_results: {self.json_results}, status: {self.status}, artefacts: {self.artefacts}>'
