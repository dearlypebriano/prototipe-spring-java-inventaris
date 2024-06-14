from flsak import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

def get_products():
    product_list_url = 'http://127.0.0.1:5050/api/products/list'
    response = requests.get(product_list_url)
    return response

def format_idr(price):
    harga = f"Rp. {int(price):,}".replace(",", ".")
    return harga + ",00"

@app.route('/api/products', methods=['GET'])
def fetch_products():
    response = get_products()
    
    if response.status_code == 200:
        products = response.json()['content']
        
        for product in products:
            if isinstance(product['price'], (int, float)):
                product['price'] = format_idr(product['price'])
            else:
                app.logger.warning(f"Product price is not numeric: {product['price']}")
            
            for variant in product.get('variants', []):
                if isinstance(variant['price'], (int, float)):
                    variant['price'] = format_idr(variant['price'])
                else:
                    app.logger.warning(f"Variant price is not numeric: {variant['price']}")
        
        return jsonify(products)
    else:
        return jsonify({'error': 'Failed to get products'}), 500

@app.route('/api/products/search/price/cheap', methods=['GET'])
def search_cheapest_products():
    max_price = float(request.args.get('q', default=float('inf')))

    response = get_products()
    if response.status_code == 200:
        data = response.json()['content']

        cheapest_products = []
        for product in data:
            product_price = float(product['price'])
            if product_price <= max_price:
                product_info = {
                    'title': product['title'],
                    'price': format_idr(product_price),
                    'category': product['categories'][0] if product['categories'] else None,
                    'images': product['imageUrls']
                }
                cheapest_products.append(product_info)

            for variant in product['variants']:
                variant_price = float(variant['price'])
                if variant_price <= max_price:
                    variant_info = {
                        'title': f"{product['title']} - {variant['name']}",
                        'price': format_idr(variant_price),
                        'category': product['categories'][0] if product['categories'] else None,
                        'images': product['imageUrls']
                    }
                    cheapest_products.append(variant_info)

        cheapest_products = sorted(cheapest_products, key=lambda x: float(x['price'].replace('Rp ', '').replace('.', '').replace(',-', '').replace(',', '.')))
        return jsonify(cheapest_products)
    else:
        return jsonify({'message': 'Failed to fetch products'}), 500

@app.route('/')
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
