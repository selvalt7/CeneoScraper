from app import app
import os
import json
import requests
import numpy as np
from bs4 import BeautifulSoup
from flask import render_template, redirect, url_for, request, abort, send_file
import pandas as pd
from config import headers

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

def extract(ancestor, selector, attribute=None, multiple=False):
  if selector:
    if multiple:
      if attribute:
        return [tag[attribute].strip() for tag in ancestor.select(selector)]
      return [tag.text.strip() for tag in ancestor.select(selector)]
    if attribute:
      try:
        return ancestor.select_one(selector)[attribute].strip()
      except TypeError:
        return None
    try:
      return ancestor.select_one(selector).text.strip()
    except AttributeError:
      return None
  if attribute:
    return ancestor[attribute].strip()
  return None

selectors = {
  "opinion_id": (None, "data-entry-id"),
  "author": ("span.user-post__author-name",),
  "recommendation": ("span.user-post__author-recommendation > em",),
  "stars": ("span.user-post__score-count",),
  "content": ("div.user-post__text",),
  "pros": ("div.review-feature__item--positive", None, True),
  "cons": ("div.review-feature__item--negative", None, True),
  "useful": ("button.vote-yes", "data-total-vote"),
  "useless": ("button.vote-no", "data-total-vote"),
  "post_date": ("span.user-post__published > time:nth-child(1)", "datetime"),
  "purchase_date": ("span.user-post__published > time:nth-child(2)", "datetime"),
}

@app.route('/display_form', methods=['POST'])
def extract_post():
  product_id = request.form.get('product_id')
  url = f"https://www.ceneo.pl/{product_id}#tab=reviews"
  print(url)
  response = requests.get(url, headers=headers)
  if response.status_code==200:
    page_dom = BeautifulSoup(response.text, "html.parser")
    product_name = extract(page_dom, "h1")
    opinions_count = extract(page_dom, "a.product-review__link > span")
    if not opinions_count:
      error = "Dla produktu o podanym kodzie nie ma opinii"
      return render_template("extract.html", error=error)
  else:
    error = "Podana wartość nie jest poprawnym kodem produktu"
    return render_template("extract.html", error=error)  
  all_opinions = []
  while url:
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code==200:
      page_dom = BeautifulSoup(response.text, "html.parser")
      opinions = page_dom.select("div.js_product-review:not(.user-post--highlight)")
      print(len(opinions))
      for opinion in opinions:
        single_opinion = {
          key: extract(opinion, *value) for key, value in selectors.items()
        }
        all_opinions.append(single_opinion)
      try:
        url = "https://www.ceneo.pl"+extract(page_dom, "a.pagination__next", "href")
      except TypeError:
        url = None         
        
  if not os.path.exists("./app/data"):
    os.mkdir("./app/data")
  if not os.path.exists("./app/data/opinions"):
    os.mkdir("./app/data/opinions") 
  with open(f"./app/data/opinions/{product_id}.json", "w", encoding="UTF-8") as jf:
    json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
  opinions = pd.DataFrame.from_dict(all_opinions)
  opinions.stars = opinions.stars.apply(lambda s: s.split("/")[0].replace(",",".")).astype(float)
  pros_count = int(opinions.pros.astype(bool).sum())
  cons_count = int(opinions.cons.astype(bool).sum())
  average_stars = float(opinions.stars.mean())
  stars_distr = opinions.stars.value_counts().reindex(list(np.arange(0, 5.5, 0.5)), fill_value=0)
  recommendation_distr = opinions.recommendation.value_counts(dropna=False).reindex(["Nie polecam", "Polecam", None], fill_value=0)
  product_info = {
    "product_id": product_id,
    "product_name": product_name,
    "opinions_count": opinions_count,
    "pros_count": pros_count,
    "cons_count": cons_count,
    "average_stars": average_stars,
    "stars_distr": stars_distr.to_dict(),
    "recommendation_distr": recommendation_distr.to_dict()
  }
  if not os.path.exists("./app/data/products"):
    os.mkdir("./app/data/products") 
  with open(f"./app/data/products/{product_id}.json", "w", encoding="UTF-8") as jf:
    json.dump(product_info, jf, indent=4, ensure_ascii=False)
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

@app.route('/product/<product_id>')
def product(product_id):
  with open(os.path.join(app.root_path, 'data', 'opinions', f"{product_id}.json"), 'r', encoding='utf-8') as file:
    try:
      opinions = json.load(file)
    except json.JSONDecodeError:
      abort(404, description="Opinions not found.")
      
  return render_template('product.html', product_id=product_id, opinions=opinions)