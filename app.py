from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import plotly.express as px
import os
import io
import base64
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

data_store = {"df": None, "latest_plot": None}


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        row_count = request.form.get('rowCount', '5')

        if not file:
            return render_template('index.html', error="⚠️ Please upload a CSV file.")

        try:
            df = pd.read_csv(file)
            data_store["df"] = df
        except Exception as e:
            return render_template('index.html', error=f"❌ Error reading file: {e}")

        df_display = df if row_count == 'all' else df.head(int(row_count) if row_count.isdigit() else 5)
        data_store["display_df"] = df_display

        df_html = df_display.to_html(classes='table table-striped table-hover', index=False)
        summary = get_summary(df)
        return render_template('index.html', table=df_html, columns=df.columns.tolist(), summary=summary)

    return render_template('index.html')


@app.route('/plot', methods=['POST'])
def plot():
    df = data_store.get("df")
    if df is None:
        return render_template('index.html', error="⚠️ Please upload a CSV file first.")

    col_x = request.form.get('x_column')
    col_y = request.form.get('y_column')
    plot_type = request.form.get('plot_type', 'count')

    if col_x not in df.columns:
        return render_template('index.html', error=f"Column '{col_x}' not found.", columns=df.columns.tolist())

    try:
        if plot_type == 'count':
            fig = px.histogram(df, x=col_x)
        elif plot_type == 'hist':
            fig = px.histogram(df, x=col_x, nbins=20, marginal='box', color_discrete_sequence=['#007bff'])
        elif plot_type == 'scatter' and col_y in df.columns:
            fig = px.scatter(df, x=col_x, y=col_y, color_discrete_sequence=['#28a745'])
        else:
            fig = px.histogram(df, x=col_x)

        fig.update_layout(
            template="plotly_dark",
            title=f"{plot_type.capitalize()} plot of {col_x}" + (f" vs {col_y}" if col_y else ""),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white")
        )

        img_bytes = fig.to_image(format="png")
        data_store["latest_plot"] = img_bytes

        plot_html = fig.to_html(full_html=False)

    except Exception as e:
        return render_template('index.html', error=f"Error creating plot: {e}")

    df_html = df.head().to_html(classes='table table-striped table-hover', index=False)
    summary = get_summary(df)
    return render_template(
        'index.html',
        table=df_html,
        columns=df.columns.tolist(),
        summary=summary,
        plot_html=plot_html,
        downloadable=True
    )


@app.route('/download/data')
def download_data():
    df = data_store.get("display_df")
    if df is None:
        return "No data available to download.", 400
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(buf, mimetype='text/csv', as_attachment=True, download_name='filtered_data.csv')


@app.route('/download/plot')
def download_plot():
    img_bytes = data_store.get("latest_plot")
    if img_bytes is None:
        return "No plot generated yet.", 400
    return send_file(io.BytesIO(img_bytes), mimetype='image/png', as_attachment=True, download_name='plot.png')


@app.route('/download/summary')
def download_summary():
    df = data_store.get("df")
    if df is None:
        return "No dataset loaded.", 400
    summary = get_summary(df)
    buf = io.BytesIO(json.dumps(summary, indent=4).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name='summary.json')


def get_summary(df):
    return {
        "Shape": f"{df.shape[0]} rows × {df.shape[1]} columns",
        "Columns": list(df.columns),
        "Data Types": df.dtypes.astype(str).to_dict(),
        "Missing Values": df.isnull().sum().to_dict()
    }


if __name__ == '__main__':
    app.run(debug=True)




