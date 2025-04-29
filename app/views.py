from app import app
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
  return render_template('products.html')

@app.route('/author')
def author():
  return render_template('author.html')

@app.route('/product/<int:product_id>')
def product(product_id:int):
  return render_template('product.html', product_id=product_id)