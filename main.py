import sqlite3
from flask import Flask, render_template, redirect, session, request, jsonify, make_response
from wtforms import PasswordField, BooleanField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_restful import reqparse, abort, Api, Resource