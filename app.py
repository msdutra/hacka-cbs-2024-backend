from flask_cors import CORS
from flasgger import Swagger
from flask import Flask, request
from modules.weather_forecast import process_weather_forecast
from modules.social_media_insigth import generate_social_media_insigth

app = Flask(__name__)
swagger = Swagger(app)

allowed_origins = ["http://localhost:5173", "https://orusapp.netlify.app"]
CORS(app, resources={r"/*": {"origins": allowed_origins}})


@app.route("/")
def home():
    """Página inicial da API
    ---
    responses:
      200:
        description: Retorna a página inicial da API
        schema:
          type: string
          example: "Api home page documentations"
    """
    return "Api home page documentations"


@app.route("/healthCheck", methods=["GET"])
def healthCheck():
    """Verificação de Saúde da API
    ---
    responses:
      200:
        description: Confirma que a API está respondendo como esperado
        schema:
          type: string
          example: "Health check done, api is responding as expected"
    """
    return "Health check done, api is responding as expected", 200


@app.route("/process_agricultural_forecasting", methods=["POST"])
def processAgriculturalForecasting():
    """Processa a previsão agrícola
    ---
    parameters:
      - in: body
        name: data_json
        description: JSON contendo dados para a previsão agrícola
        required: true
        schema:
          type: object
          properties:
            crop:
              type: array
              items:
                type: string
              example: ["corn", "Soybean"]
            size:
              type: string
              example: "1 a 3 hectars"
            location:
              type: object
              properties:
                latitude:
                  type: number
                  example: -16.686072
                longitude:
                  type: number
                  example: -49.262533
    responses:
      200:
        description: Resultados da previsão agrícola
        schema:
          type: string
    """
    data_json = request.get_json()
    return process_weather_forecast(data_json)


@app.route("/generate_social_media_insigth", methods=["POST"])
def generateSocialMediaInsigth():
    """Gera Postagem e Insigths nas redes sociais
    ---
    respose:
      200:
        description: Retorno do processo de geração da postagem
        schema:
          type: string
    """
    data_json = request.get_json()
    return generate_social_media_insigth(data_json)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
