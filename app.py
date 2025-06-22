from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cargar el modelo y los objetos de preprocesamiento
try:
    model = joblib.load('random_forest_model.pkl')
    encoder = joblib.load('ordinal_encoder.pkl')  # Cargar OrdinalEncoder
    scaler = joblib.load('minmax_scaler.pkl')    # Cargar MinMaxScaler
    logger.info("Modelo y preprocesadores cargados exitosamente")
except Exception as e:
    logger.error(f"Error al cargar el modelo o preprocesadores: {str(e)}")
    raise

# Definir categorías basadas en el dataset (para validación)
categories = {
    'Cpu_Type': ['Intel Core i3', 'Intel Core i5', 'Intel Core i7', 'Intel Core i9', 'Intel Pentium',
                 'Intel Celeron', 'AMD Ryzen', 'AMD A-Series', 'AMD E-Series', 'Other'],
    'OpSys': ['Windows 10', 'No OS', 'Linux', 'Windows 7', 'Chrome OS', 'macOS', 'Mac OS X',
              'Windows 10 S', 'Android'],
    'Storage_Type': ['SSD', 'HDD', 'Flash Storage', 'Hybrid', 'Unknown'],
    'Gpu_Brand': ['Intel', 'Nvidia', 'AMD', 'ARM'],
    'Company': ['Dell', 'Lenovo', 'HP', 'Asus', 'Acer', 'MSI', 'Toshiba', 'Apple', 'Samsung',
                'Razer', 'Mediacom', 'Microsoft', 'Xiaomi', 'Vero', 'Chuwi', 'Google',
                'Fujitsu', 'LG', 'Huawei'],
    'TypeName': ['Notebook', 'Gaming', 'Ultrabook', '2 in 1 Convertible', 'Workstation', 'Netbook']
}

# Orden exacto de las columnas esperadas por el scaler
SCALER_COLUMNS = [
    'Inches', 'Ram', 'Weight', 'ScRes_X', 'ScRes_Y', 'ScRes_is_touchscreen',
    'SSD_Capacity', 'HDD_Capacity', 'Flash_Capacity', 'Hybrid_Capacity',
    'Cpu_Frequency', 'Company', 'TypeName', 'OpSys', 'Storage_Type',
    'Cpu_Type', 'Gpu_Brand'
]

# Columnas esperadas por el modelo (subconjunto de SCALER_COLUMNS)
MODEL_COLUMNS = [
    'Ram', 'ScRes_X', 'ScRes_Y', 'Cpu_Type', 'Weight', 'Cpu_Frequency', 'SSD_Capacity',
    'Inches', 'OpSys', 'Storage_Type', 'Gpu_Brand', 'Company', 'TypeName'
]

@app.route('/', methods=['GET'])
def home():
    logger.debug("Accediendo a la ruta raíz (/)")
    return render_template('index.html', categories=categories)

@app.route('/predict', methods=['POST'])
def predict():
    logger.debug("Recibida solicitud POST en /predict")
    try:
        # Obtener valores del formulario
        ram = float(request.form['ram'])
        scres_x = int(request.form['scres_x'])
        scres_y = int(request.form['scres_y'])
        scres_is_touchscreen = int(request.form['scres_is_touchscreen'])
        cpu_type = request.form['cpu_type']
        weight = float(request.form['weight'])
        cpu_frequency = float(request.form['cpu_frequency'])
        ssd_capacity = int(request.form['ssd_capacity'])
        hdd_capacity = int(request.form['hdd_capacity'])
        flash_capacity = int(request.form['flash_capacity'])
        hybrid_capacity = int(request.form['hybrid_capacity'])
        inches = float(request.form['inches'])
        opsys = request.form['opsys']
        storage_type = request.form['storage_type']
        gpu_brand = request.form['gpu_brand']
        company = request.form['company']
        typename = request.form['typename']

        logger.debug(f"Datos recibidos: ram={ram}, scres_x={scres_x}, scres_y={scres_y}, "
                     f"scres_is_touchscreen={scres_is_touchscreen}, cpu_type={cpu_type}, weight={weight}, "
                     f"cpu_frequency={cpu_frequency}, ssd_capacity={ssd_capacity}, hdd_capacity={hdd_capacity}, "
                     f"flash_capacity={flash_capacity}, hybrid_capacity={hybrid_capacity}, inches={inches}, "
                     f"opsys={opsys}, storage_type={storage_type}, gpu_brand={gpu_brand}, company={company}, "
                     f"typename={typename}")
       
        # Validaciones
        if not (2 <= ram <= 64):
            raise ValueError("RAM debe estar entre 2 y 64 GB")
        if not (1366 <= scres_x <= 2880):
            raise ValueError("Resolución X debe estar entre 1366 y 2880")
        if not (768 <= scres_y <= 1800):
            raise ValueError("Resolución Y debe estar entre 768 y 1800")
        if scres_is_touchscreen not in [0, 1]:
            raise ValueError("Pantalla táctil debe ser 0 (No) o 1 (Sí)")
        if cpu_type not in categories['Cpu_Type']:
            raise ValueError(f"Cpu_Type debe ser uno de {categories['Cpu_Type']}")
        if not (1 <= weight <= 3):
            raise ValueError("Peso debe estar entre 1 y 3 kg")
        if not (1.2 <= cpu_frequency <= 3.5):
            raise ValueError("Frecuencia CPU debe estar entre 1.2 y 3.5 GHz")
        if not (0 <= ssd_capacity <= 1000):
            raise ValueError("Capacidad SSD debe estar entre 0 y 1000 GB")
        if not (0 <= hdd_capacity <= 1000):
            raise ValueError("Capacidad HDD debe estar entre 0 y 1000 GB")
        if not (0 <= flash_capacity <= 1000):
            raise ValueError("Capacidad Flash debe estar entre 0 y 1000 GB")
        if not (0 <= hybrid_capacity <= 1000):
            raise ValueError("Capacidad Híbrida debe estar entre 0 y 1000 GB")
        if not (10 <= inches <= 18):
            raise ValueError("Pulgadas debe estar entre 10 y 18")
        if opsys not in categories['OpSys']:
            raise ValueError(f"OpSys debe ser uno de {categories['OpSys']}")
        if storage_type not in categories['Storage_Type']:
            raise ValueError(f"Storage_Type debe ser uno de {categories['Storage_Type']}")
        if gpu_brand not in categories['Gpu_Brand']:
            raise ValueError(f"Gpu_Brand debe ser uno de {categories['Gpu_Brand']}")
        if company not in categories['Company']:
            raise ValueError(f"Company debe ser uno de {categories['Company']}")
        if typename not in categories['TypeName']:
            raise ValueError(f"TypeName debe ser uno de {categories['TypeName']}")

        # Preparar datos en un solo DataFrame con el orden correcto para el scaler
        input_data_dict = {
            'Inches': inches,
            'Ram': ram,
            'Weight': weight,
            'ScRes_X': scres_x,
            'ScRes_Y': scres_y,
            'ScRes_is_touchscreen': scres_is_touchscreen,
            'SSD_Capacity': ssd_capacity,
            'HDD_Capacity': hdd_capacity,
            'Flash_Capacity': flash_capacity,
            'Hybrid_Capacity': hybrid_capacity,
            'Cpu_Frequency': cpu_frequency,
            'Company': company,
            'TypeName': typename,
            'OpSys': opsys,
            'Storage_Type': storage_type,
            'Cpu_Type': cpu_type,
            'Gpu_Brand': gpu_brand
        }

        input_data = pd.DataFrame([input_data_dict], columns=SCALER_COLUMNS)
        logger.debug("log despues de crear el dataframe")

        # Codificar variables categóricas con OrdinalEncoder
        categorical_cols = ['Company', 'TypeName', 'OpSys', 'Storage_Type', 'Cpu_Type', 'Gpu_Brand']
        logger.debug("log despues de definir categorical col")

        categorical_data = input_data[categorical_cols]
        logger.debug("log despues de definir categorical_data")
        
        categorical_encoded = encoder.transform(categorical_data)
        categorical_encoded_df = pd.DataFrame(categorical_encoded, columns=categorical_cols)
        logger.debug("log despues de usar el encoder y transformar")

        # Reemplazar las columnas categóricas originales con las codificadas
        input_data[categorical_cols] = categorical_encoded_df

        logger.debug(f"Datos antes de escalado: {input_data.to_dict(orient='records')}")

        # Escalar todas las variables con MinMaxScaler
        input_data_scaled = scaler.transform(input_data[SCALER_COLUMNS])
        input_data = pd.DataFrame(input_data_scaled, columns=SCALER_COLUMNS)

        logger.debug(f"Datos preprocesados: {input_data.to_dict(orient='records')}")

        # Seleccionar solo las columnas esperadas por el modelo
        input_data_model = input_data[MODEL_COLUMNS]

        # Verificar que las columnas coincidan con las esperadas por el modelo
        trained_columns = model.feature_names_in_
        logger.debug(f"Columnas esperadas por el modelo: {trained_columns}")
        if list(input_data_model.columns) != list(trained_columns):
            raise ValueError(f"Las columnas de entrada ({list(input_data_model.columns)}) no coinciden con las esperadas por el modelo ({list(trained_columns)})")

        # Predecir
        prediction = model.predict(input_data_model)[0]
        prediction = max(0, prediction)
        logger.debug(f"Predicción exitosa: {prediction}")

        return jsonify({'prediction': prediction}), 200

    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error en la predicción: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)