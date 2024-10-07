from PIL import Image, ImageEnhance
from io import BytesIO
import math
from flask import Flask, render_template, request, send_file, jsonify
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('mainhtml.html')

@app.route('/post', methods=['POST'])
def handle_post():
    # Parse JSON data from the request
    data = request.json
    response = {
        "received_data": data
    }

    # Extract parameters
    list_data = response['received_data']
    star_temp = str(list_data[0])  # Star temperature
    distance_star = str(list_data[1])  # Distance from the star
    planet_type = str(list_data[2])  # Type of planet
    planet_comp = str(list_data[3])  # Chemical composition

    # Get initial image based on parameters
    image_returned = imget(distance_star, planet_type)

    if planet_type in ['n', 'g'] and planet_comp == 'nh3':
        # Decode base64 if needed
        if isinstance(image_returned, str) and image_returned.startswith('data:image/png;base64,'):
            image_data = base64.b64decode(image_returned.split(',')[1])
            image_returned = Image.open(BytesIO(image_data))

        final_product = desaturate(image_returned, 90)  # Desaturate the image
        overall_final = final_product
    else:
        overall_final = image_returned

    # Calculate luminosity and temperature
    lum_star = {
        'c': 1.914e25,
        's': 3.828e26,
        'h': 3.828e29
    }.get(star_temp)

    albedo = {
        'r': 0.5,
        'g': 0.3,
        'n': 0.25
    }.get(planet_type)

    distance_to_star = calculate_distance(distance_star, star_temp)

    if distance_to_star is not None:
        planet_temp = stef_boltz_equn(lum_star, albedo, distance_to_star)

    print(distance_star, star_temp, planet_comp, planet_type)

    # Convert image to a BytesIO object for response
    img_io = BytesIO()
    overall_final.save(img_io, format='PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

def calculate_distance(distance_star, star_temp):
    distances = {
        ('c', 'c'): 7.49e9,
        ('c', 's'): 3.74e10,
        ('c', 'h'): 3.74e12,
        ('i', 'c'): 7.48e10,
        ('i', 's'): 1.197e11,
        ('i', 'h'): 7.48e12,
        ('f', 'c'): 1.122e11,
        ('f', 's'): 1.87e11,
        ('f', 'h'): 1.122e13,
    }
    return distances.get((distance_star, star_temp))

def stef_boltz_equn(L_sun, albedo, distance):
    sigma = 5.670373e-8
    T = ((L_sun * (1 - albedo)) / (16 * math.pi * distance ** 2 * sigma)) ** 0.25
    return T

def desaturate(image, factor):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    enhancer = ImageEnhance.Color(image)
    saturation = 1 - (factor / 100)
    output_image = enhancer.enhance(saturation)
    return output_image

def imget(distance_star, planet_type):
    images = {
        ('c', 'g'): 'pictures/closergas.png',
        ('c', 'r'): 'pictures/closerrock.png',
        ('c', 'n'): 'pictures/closernep.png',
        ('i', 'g'): 'pictures/ingas.png',
        ('i', 'r'): 'pictures/inrock.png',
        ('i', 'n'): 'pictures/innep.png',
        ('f', 'g'): 'pictures/farthergas.png',
        ('f', 'r'): 'pictures/fartherrock.png',
        ('f', 'n'): 'pictures/farthernep.png',
    }

    image_key = (distance_star, planet_type)
    image_path = images.get(image_key)

    if image_path:
        try:
            image = Image.open(image_path)
            return image
        except Exception as e:
            print(f"Error opening image '{image_path}': {e}")
            return None
    else:
        print(f"Error: No image found for distance '{distance_star}' and planet type '{planet_type}'.")
        return None

if __name__ == '__main__':
    app.run(debug=False)
