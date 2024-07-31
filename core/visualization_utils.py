import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from io import BytesIO
import base64

def generate_bar_chart(data, title, x_label, y_label):
    df = pd.DataFrame(data)
    fig = px.bar(df, x=x_label, y=y_label, title=title)
    return fig.to_json()

def generate_pie_chart(data, title):
    df = pd.DataFrame(data)
    fig = px.pie(df, values='value', names='label', title=title)
    return fig.to_json()

def generate_line_chart(data, title, x_label, y_label):
    df = pd.DataFrame(data)
    fig = px.line(df, x=x_label, y=y_label, title=title)
    return fig.to_json()
