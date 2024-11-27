import requests
import tensorflow as tf
import numpy as np
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("API_URL")
token = os.getenv("HUGGINGFACE_TOKEN")

parameter_names = {
    "RH2M": "Relative Humidity at 2m",
    "ALLSKY_SFC_SW_DWN": "Surface Shortwave Downward Irradiance",
    "T2M": "Temperature at 2m (°C)",
}


def format_date_to_api(date_input):
    return date_input.strftime("%Y%m%d")


def fetch_nasa_power_data(latitude, longitude, start_date, end_date):
    parameters = "RH2M,ALLSKY_SFC_SW_DWN,T2M"
    format_type = "JSON"
    api_power_url = f"https://power.larc.nasa.gov/api/temporal/daily/point?latitude={latitude}&longitude={longitude}&parameters={parameters}&format={format_type}&start={start_date}&end={end_date}&community=AG"
    response_power = requests.get(api_power_url)

    if response_power.status_code == 200:
        return response_power.json()["properties"]["parameter"]
    else:
        raise Exception(
            f"Error fetching data from NASA POWER API: {response_power.status_code}"
        )


def llm3(query):
    parameters = {
        "max_new_tokens": 100,
        "temperature": 0.1,
        "top_k": 50,
        "top_p": 0.95,
        "return_full_text": False,
    }

    prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful and smart assistant. You accurately provide answer to the provided user query.<|eot_id|><|start_header_id|>user<|end_header_id|> Here is the query: ```{query}```.
      Provide precise and concise answer. Provide only in plain text, no special characters.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    prompt = prompt.replace("{query}", query)

    payload = {"inputs": prompt, "parameters": parameters}

    response = requests.post(url, headers=headers, json=payload)
    response_text = response.json()[0]["generated_text"].strip()

    return response_text


def llm2(query):
    parameters = {
        "max_new_tokens": 100,
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.95,
        "return_full_text": False,
    }

    prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful and smart assistant. You accurately provide answer to the provided user query.<|eot_id|><|start_header_id|>user<|end_header_id|> Here is the query: ```{query}```.
      Provide precise and concise answer.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    prompt = prompt.replace("{query}", query)

    payload = {"inputs": prompt, "parameters": parameters}

    response = requests.post(url, headers=headers, json=payload)
    response_text = response.json()[0]["generated_text"].strip()

    return response_text


def llm(query):
    parameters = {
        "max_new_tokens": 100,
        "temperature": 0.002,
        "top_k": 50,
        "top_p": 0.95,
        "return_full_text": False,
    }

    prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful and smart assistant. You accurately provide answer to the provided user query.<|eot_id|><|start_header_id|>user<|end_header_id|> Here is the query: ```{query}```.
      Provide precise and concise answer.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    prompt = prompt.replace("{query}", query)

    payload = {"inputs": prompt, "parameters": parameters}

    response = requests.post(url, headers=headers, json=payload)
    response_text = response.json()[0]["generated_text"].strip()

    return response_text


def generate_dynamic_title(insight):
    prompt = """Generate a single 2-3 word title that summarizes this agricultural recommendation:
    '{insight}'
    Return ONLY the title, no quotes, no formatting, no explanation."""

    try:
        response = llm(prompt.format(insight=insight))
        cleaned_title = response.split("\n")[0].strip().strip("\"'")
        words = cleaned_title.split()[:3]
        return " ".join(words)
    except Exception as e:
        return "Recommendation"


def predict_parameter_value(historical_data, parameter_name, target_date, location):
    prompt = f"""You are a weather prediction system. Return ONLY a single number.

Historical {parameter_names[parameter_name]} 
Location: {location['latitude']}, {location['longitude']}
Target: {target_date}

if the value is -999, its because we dont have the value.

Rules for {parameter_name}:
T2M: between -50 and 60
RH2M: between 0 and 100
ALLSKY_SFC_SW_DWN: between 0 and 100

RH2M = Relative Humidity at 2m,
ALLSKY_SFC_SW_DWN = Surface Shortwave Downward Irradiance,
T2M = Temperature at 2m (°C)

Return ONLY the predicted number. No text, no units, no explanation.
Example good response format for T2M: '24.5'
Example bad response format for T2M: 'The temperature will be 24.5 degrees
Example good response format for RH2M: '57.5'
Example bad response format for RH2M: 'The temperature will be 57.5
Example good response format for ALLSKY_SFC_SW_DWN: '24.5'
Example bad response format for ALLSKY_SFC_SW_DWN: 'The temperature will be 24.5 


'

values: {historical_data[-30:]}"""

    try:
        response = llm(
            prompt.format(
                prompt.format(
                    historical_data=historical_data,
                    parameter_name=parameter_name,
                    target_date=target_date,
                    location=location,
                )
            )
        ).strip()
        return response
    except Exception as e:
        print(f"Error predicting value for {parameter_name}: {str(e)}")
        defaults = {
            "T2M": 25.0,
            "RH2M": 50.0,
            "ALLSKY_SFC_SW_DWN": 500.0,
        }
        return defaults.get(parameter_name, 0.0)

    except Exception as e:
        print(f"Error predicting value for {parameter_name}: {str(e)}")
        defaults = {
            "T2M": 25.0,
            "RH2M": 50.0,
            "ALLSKY_SFC_SW_DWN": 500.0,
        }
        return defaults.get(parameter_name, 0.0)


def generate_daily_insights(date, crop_info, location, predicted_values):
    prompt = f"""
    Date: {date}
    Location: Latitude {location['latitude']}, Longitude {location['longitude']}
    Crop: {crop_info['crop'][0]}
    Field Size: {crop_info['size_h']}

    Predicted conditions for this day:
    {', '.join([f"{parameter_names[param]}: {value}" for param, value in predicted_values.items()])}

    Based on these predictions, Consider:
    Supervision needs, Temperature management, Root moisture conditions, Possible critical actions, Possible pests of the crop in question, the time of year we are in according to the date, specific points of the person's crop and the person's location (city, state and country, according to latitude and longitude)
    Consider: water-related challenges due to unpredictable weather, pests, and diseases
    Consider: water-related challenges due to unpredictable weather, pests, and diseases
    Consider: water-related challenges due to unpredictable weather, pests, and diseases

    provide specific agricultural recommendations for this day in 2 sentences on plain text.

    Be direct and objective in the suggestions.
    Do not use the first person
    Your response must be in 200 characters or less.
    Dont write special characters, such as *, \n or \n\n 
    write on the third person 
    Give me only the 2 sentences recommendations
    """
    return llm3(
        prompt.format(
            date=date,
            crop_info=crop_info,
            location=location,
            predicted_values=predicted_values,
        )
    )


def determine_status(predicted_values):
    try:
        if any(
            predicted_values.get(key) is None
            for key in ["RH2M", "ALLSKY_SFC_SW_DWN", "T2M"]
        ):
            return "Normal"
        if predicted_values["T2M"] > 35 and predicted_values["RH2M"] < 30:
            return "Extreme dry heat"
        elif predicted_values["T2M"] > 35 and predicted_values["RH2M"] > 80:
            return "Extreme humid heat"
        elif predicted_values["T2M"] < 10:
            return "Extreme cold"

        elif (
            predicted_values["RH2M"] < 30
            and predicted_values["ALLSKY_SFC_SW_DWN"] > 800
        ):
            return "High evaporation"
        elif predicted_values["RH2M"] < 20:
            return "Critical low humidity"

        elif predicted_values["RH2M"] > 85 and predicted_values["T2M"] > 25:
            return "Risk of fungal diseases"

        elif predicted_values["ALLSKY_SFC_SW_DWN"] > 900:
            return "High solar radiation"

        elif 30 <= predicted_values["T2M"] <= 35:
            return "Moderate heat"
        elif predicted_values["RH2M"] < 40:
            return "Low humidity"
        elif predicted_values["RH2M"] > 80:
            return "High humidity"
        else:
            return "Normal"
    except (KeyError, TypeError):
        return "Normal"


def select_lucide_icon(title, description):
    prompt = """Based on the title and description, you should suggest, according to the lucide icons library, a single icon that best fits the context.
Below are some icon names from the "weather" class, but you can choose any other, as long as it is part of the lucide icons library:
cloud, cloud-drizzle, cloud-fog, cloud-hail, cloud-lightning, cloud-moon, cloud-moon-rain, cloud-off, cloud-rain, cloud-rain-wind, cloud-rain-wind, cloud-sun, cloud-sun-rain, cloudy, haze, moon-star, rainbow, snowflake, sparkles, star, sun, sun-dim, sun-medium, sun-snow, sunrise, sunset, thermometer, thermometer-snowflake, umbrella-off, waves, wind, zap, zap-off

return only the name of the icon.
Illustrative example of a good answer: wind
Illustrative example of a bad answer: The icon that best fits the context would be wind

Title: {title}
Description: {description}"""

    try:
        response = llm(prompt.format(title=title, description=description))
        icon_name = response.strip().split("\n")[0].strip()
        return icon_name
    except Exception as e:
        print(f"Error selecting icon: {str(e)}")
        return "sun"


def process_weather_forecast(input_json):
    crop = input_json["crop"]
    size = input_json["size"]
    location = input_json["location"]

    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    data = fetch_nasa_power_data(
        location["latitude"],
        location["longitude"],
        format_date_to_api(start_date),
        format_date_to_api(end_date),
    )

    df = pd.DataFrame(
        {param: list(data[param].values()) for param in parameter_names.keys()}
    )

    output_json = {"state": "Nome", "plantation": crop[0], "days": []}

    for day_offset in range(3):
        target_date = end_date + timedelta(days=day_offset)

        predicted_values = {}
        for parameter in parameter_names.keys():
            historical_values = df[parameter].tolist()
            predicted_value = predict_parameter_value(
                historical_values, parameter, target_date, location
            )
            predicted_values[parameter] = predicted_value

        insights = generate_daily_insights(
            target_date, {"crop": crop, "size_h": size}, location, predicted_values
        )

        status = determine_status(predicted_values)
        title = generate_dynamic_title(insights)

        icon = select_lucide_icon(title, insights)

        day_entry = {
            "icon": icon,
            "data": target_date.strftime("%d.%b."),
            "status": status,
            "duracao": f"{start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}",
            "dicks": [{"title": title, "icon": icon, "description": insights}],
        }

        output_json["days"].append(day_entry)

    return output_json
