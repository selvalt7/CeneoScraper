from app import app
import os
import json
from flask import render_template, redirect, url_for, request, abort, send_file
import pandas as pd

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/download/<product_id>/<file_type>')
def download_file(product_id, file_type):
  opinions_file = os.path.join(app.root_path, 'data', 'opinions', f"{product_id}.json")
  
  if not os.path.exists(opinions_file):
    abort(404, description="Opinions file not found.")
  
  if file_type == 'json':
    return send_file(opinions_file, as_attachment=True)
  elif file_type in ['csv', 'xlsx']:
    # Load JSON data
    with open(opinions_file, 'r', encoding='utf-8') as file:
      opinions = pd.read_json(file)
    
    # Save as CSV or XLSX
    output_file = os.path.join(app.root_path, 'data', 'temp', f"{product_id}.{file_type}")
    if file_type == 'csv':
      opinions.to_csv(output_file, index=False, encoding='utf-8')
    elif file_type == 'xlsx':
      opinions.to_excel(output_file, index=False, engine='openpyxl')
    
    return send_file(output_file, as_attachment=True)
  else:
    abort(400, description="Invalid file type.")

@app.route('/display_form', methods=['POST'])
def extract_post():
  product_id = request.form.get('product_id')
  return redirect(url_for('product', product_id=product_id))

@app.route('/display_form', methods=['GET'])
def display_form():
  return render_template('extract.html')

@app.route('/products')
def products():
  products_dir = "app/data/products"
  products = []
  try:
    for filename in os.listdir(products_dir):
      if filename.endswith('.json'):
        file_path = os.path.join(products_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
          try:
            product = json.load(file)
            products.append(product)
          except json.JSONDecodeError:
            continue
  except FileNotFoundError:
    error = "Nie pobrano jeszcze żadnych danych"
    return render_template('products.html', error=error)
  return render_template('products.html', products=products)

@app.route('/author')
def author():
  return render_template('author.html')

@app.route('/product/<int:product_id>')
def product(product_id:int):
  with open(os.path.join(app.root_path, 'data', 'opinions', f"{product_id}.json"), 'r', encoding='utf-8') as file:
    try:
      opinions = json.load(file)
    except json.JSONDecodeError:
      abort(404, description="Opinions not found.")
      
  return render_template('product.html', product_id=product_id, opinions=opinions)