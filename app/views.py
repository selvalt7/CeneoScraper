from app import app
import os
import json
from flask import render_template, redirect, url_for, request

@app.route('/')
def index():
  return render_template('index.html')

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
            product = json.load(file)  # Wczytaj dane jako słownik
            products.append(product)  # Dodaj do listy produktów
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
  return render_template('product.html', product_id=product_id)