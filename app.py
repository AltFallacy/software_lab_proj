from flask import Flask, render_template,request,jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

app=Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
df_cache=None
@app.route('/',methods=['GET','POST'])
def home():
    global df_cache
    if request.method == "POST":
        file = request.files.get('csv_file')
        row_count = request.form.get('rowCount', '5')
        if not file:
            return "No file uploaded", 400
        df_cache = pd.read_csv(file)
        if row_count == 'all':
            df_display = df_cache
        else:
            try:
                row_count = int(row_count)
                df_display = df_cache.head(row_count)
            except ValueError:
                df_display = df_cache.head(5)

        columns = df_cache.columns.tolist()
        df_html = df_display.to_html(classes='table table-striped', index=False)
        return render_template('index.html', table=df_html, columns=columns)
    return render_template('index.html')
@app.route('/update_rows',methods=['POST'])
def update_rows():
    global df_cache
    if df_cache is None:
        return "No DataFrame available. Please upload a CSV first.", 400

    row_count = request.form.get('rowCount', '5')

    if row_count == 'all':
        df_display = df_cache
    else:
        try:
            row_count = int(row_count)
            df_display = df_cache.head(row_count)
        except ValueError:
            df_display = df_cache.head(5)

    df_html = df_display.to_html(classes='table table-striped', index=False)
    return render_template('index.html', table=df_html, columns=df_cache.columns.tolist(), plot_url='uploads/plot.png')

@app.route('/plot', methods=['POST'])
def plot():
    global df_cache
    if df_cache is None:
        return "No DataFrame available. Please upload a CSV first.", 400

    col = request.form.get('column')
    if col not in df_cache.columns:
        return f"Column '{col}' not found in DataFrame.", 400

    plt.figure(figsize=(8, 4))
    sns.countplot(x=df_cache[col])
    plt.xticks(rotation=45)
    plot_path = os.path.join(UPLOAD_FOLDER, 'plot.png')
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    df_html = df_cache.head().to_html(classes='table table-striped', index=False)
    return render_template('index.html', table=df_html, columns=df_cache.columns.tolist(), plot_url='uploads/plot.png')


if __name__ == '__main__':
    app.run(debug=True)
