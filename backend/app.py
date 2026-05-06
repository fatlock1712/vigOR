import os
API_KEY = "AIzaSyA5DP2TA82kWcbe8syZQQZWA4Ai2sUL58o"
CF_API_KEY = "cfut_6h23KYTME17gVVSFxBlH4KlAnuZ4ulMVCIoFDsO52034f7e6"
CF_ACCOUNT_ID = "bc3c7d5d0d355d554ab05f65986614e2"

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import polyline
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import json

##########################Functions#######################################

def get_env_data(latitude, longitude, API_KEY ):
    env_data = {'temp': 0, 'humidity': 0, 'wind_speed': 0, 'pm25': 0, 'pm10': 0, 'no2': 0, 'o3': 0, 'tree_pollen': 0, 'weed_pollen': 0, 'grass_pollen': 0}
    headers = {"User-Agent": "vigOR (phatloc17122007@gmail.com)"}
    try:
        points_response = requests.get(f"https://api.weather.gov/points/{latitude},{longitude}", headers=headers, timeout=3)
        if points_response.status_code != 404:
            forecast_url = points_response.json()['properties']['forecastHourly']
            forecast_data = requests.get(forecast_url, headers=headers, timeout=3).json()
            cw = forecast_data['properties']['periods'][0]
            env_data['temp'] = cw.get('temperature', 70)
            env_data['humidity'] = cw.get('relativeHumidity', {}).get('value', 50)
            wind_str = cw.get('windSpeed', '0').replace(" mph", "").split(" to ")[-1]
            env_data['wind_speed'] = int(wind_str) if wind_str.isdigit() else 5
    except Exception: pass



    aqi_url = f"https://airquality.googleapis.com/v1/currentConditions:lookup?key={API_KEY}"
    try:
        aqi_response = requests.post(aqi_url, json={"location": {"latitude": latitude, "longitude": longitude}, "extraComputations": ["POLLUTANT_CONCENTRATION"]}, timeout=3)
        if 'pollutants' in aqi_response.json():
            for p in aqi_response.json()['pollutants']:
                if p.get('code', '').lower() in ['pm25', 'pm10', 'no2', 'o3']:
                    env_data[p['code'].lower()] = p.get('concentration', {}).get('value', 0)
    except Exception: pass

    pollen_url = "https://pollen.googleapis.com/v1/forecast:lookup"
    try:
        pollen_response = requests.get(pollen_url, params={"key": API_KEY, "location.latitude": latitude, "location.longitude": longitude, "days": 1, "languageCode": "en"}, timeout=3)
        pollen_data = pollen_response.json()
        if 'dailyInfo' in pollen_data and pollen_data['dailyInfo']:
            for pt in pollen_data['dailyInfo'][0].get('pollenTypeInfo', []):
                if pt.get('code') in ['TREE', 'WEED', 'GRASS']:
                    env_data[f"{pt.get('code').lower()}_pollen"] = pt.get('indexInfo', {}).get('value', 0)
    except Exception: pass


    return env_data

import json
import requests

def get_env_forecast(latitude, longitude, user_data):
    # We want data for 2 hours from now
    env_data = {'temp': 0, 'humidity': 0, 'wind_speed': 0, 'pm25': 0, 'pm10': 0, 'no2': 0, 'o3': 0, 'tree_pollen': 0, 'weed_pollen': 0, 'grass_pollen': 0}
    headers = {"User-Agent": "vigOR (phatloc17122007@gmail.com)"}

    # 1. NWS Weather Forecast (Hourly)
    try:
        points_res = requests.get(f"https://api.weather.gov/points/{latitude},{longitude}", headers=headers, timeout=3)
        forecast_url = points_res.json()['properties']['forecastHourly']
        forecast_data = requests.get(forecast_url, headers=headers, timeout=3).json()

        # Period [2] is usually 2 hours from now
        periods = forecast_data['properties']['periods']
        forecast_2h = periods[2] if len(periods) > 2 else periods[0]

        env_data['temp'] = forecast_2h.get('temperature', 70)
        env_data['humidity'] = forecast_2h.get('relativeHumidity', {}).get('value', 50)
        wind_str = forecast_2h.get('windSpeed', '0').replace(" mph", "").split(" to ")[-1]
        env_data['wind_speed'] = int(wind_str) if wind_str.isdigit() else 5
    except: pass

    # 2. Google Air Quality Forecast
    aqi_forecast_url = f"https://airquality.googleapis.com/v1/forecast:lookup?key={API_KEY}"
    try:
        body = {
            "location": {"latitude": latitude, "longitude": longitude},
            "extraComputations": ["POLLUTANT_CONCENTRATION"],
            "pageSize": 5
        }
        res = requests.post(aqi_forecast_url, json=body, timeout=3).json()
        if 'hourlyForecasts' in res:
            f_2h = res['hourlyForecasts'][2]
            for p in f_2h.get('pollutants', []):
                if p.get('code', '').lower() in ['pm25', 'pm10', 'no2', 'o3']:
                    env_data[p['code'].lower()] = p.get('concentration', {}).get('value', 0)
    except: pass

    # 3. Google Pollen Forecast
    pollen_url = "https://pollen.googleapis.com/v1/forecast:lookup"
    try:
        params = {"key": API_KEY, "location.latitude": latitude, "location.longitude": longitude, "days": 1}
        pollen_data = requests.get(pollen_url, params=params, timeout=3).json()
        if 'dailyInfo' in pollen_data:
            for pt in pollen_data['dailyInfo'][0].get('pollenTypeInfo', []):
                code = pt.get('code', '').lower()
                if code in ['tree', 'weed', 'grass']:
                    env_data[f"{code}_pollen"] = pt.get('indexInfo', {}).get('value', 0)
    except: pass

    llm_payload = {
        "location_context_in_2_hours": {
            "weather": {"temp": env_data["temp"], "humidity": env_data["humidity"], "wind_speed": env_data["wind_speed"]},
            "air_quality": {"pm25": env_data["pm25"], "pm10": env_data["pm10"], "no2": env_data["no2"], "o3": env_data["o3"]},
            "pollen" : {"tree_pollen": env_data["tree_pollen"], "weed_pollen": env_data["weed_pollen"], "grass_pollen": env_data["grass_pollen"]}
        },
        "user_context": {
            "user_age": user_data['age'],
            "user_asthma_severity(0-4)": user_data['asthma_severity'],
            "user_allergy": user_data['allergy'],
            "heart_condition": user_data['heart_condition']
        }
    }

    data_string = json.dumps(llm_payload, indent=2)

    nemotron_prompt = (
        "[SYSTEM ROLE]\n"
        "You are an Environmental Health Advisor. You provide personalized forecasting "
        "and health recommendations based on upcoming weather and atmospheric conditions.\n\n"

        "[INSTRUCTIONS]\n"
        "1. Analyze the environmental data provided in [DATA_INPUT] for 2 hours from now.\n"
        "2. Evaluate how these specific conditions will impact the user based on their exact 'user_context'.\n"
        "3. Address the user directly in a single, cohesive response.\n"
        "4. Structure your response naturally: First, summarize what the weather and air quality will be like in 2 hours. Next, explain exactly how those conditions affect their specific health profile. Finally, give 2-3 clear, actionable recommendations on what they should do.\n"
        "5. Output ONLY a raw JSON object containing the 'response' key. No markdown, no triple backticks.\n\n"

        "[CONSTRAINTS]\n"
        "- No hallucinations: If a pollutant or pollen value is 0 or missing, treat it as low/negligible. Do not make up severity levels.\n"
        "- Keep the tone professional, helpful, and highly readable.\n\n"

        "[DATA_INPUT]\n"
        f"<data>\n{data_string}\n</data>\n\n"

        "[OUTPUT_SCHEMA]\n"
        "{\n"
        '  "response": "(string) A cohesive message summarizing the 2-hour forecast, assessing the user\'s specific health risks, and providing actionable recommendations."\n'
        "}"
    )

    raw_response = prompt_with_nemotron(nemotron_prompt)

    # Safe JSON parsing
    try:
        parsed_data = json.loads(raw_response)
    except json.JSONDecodeError:
        clean_text = raw_response.replace("```json", "").replace("```", "").strip()
        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback if the LLM fails completely
            return "Forecast data was retrieved, but could not be summarized. Please evaluate the weather manually based on your health profile and carry necessary medications."

    # Return just the string payload
    return parsed_data.get("response", "Error: Could not generate response.")

def get_sample_points(encoded_polyline):
    coords = polyline.decode(encoded_polyline)
    pts = len(coords)
    indices = [
        0,
        int(pts * 0.25),
        int(pts * 0.50),
        int(pts * 0.75),
        pts-1
    ]
    return [coords[i] for i in indices]

def format_comprehensive_route(all_coords, env_results):
    # Standardizing the 5 points
    n = len(all_coords)
    indices = [0, n//4, n//2, (3*n)//4, n-1]
    labels = ["Start", "25%", "50%", "75%", "End"]

    route_data = []

    for i, idx in enumerate(indices):
        coord = all_coords[idx]
        env = env_results[i]

        route_data.append({
            "stage": labels[i],
            "coordinates": {"lat": round(coord[0], 4), "lng": round(coord[1], 4)},
            "weather": {
                "temp": env['temp'],
                "humidity": env['humidity'],
                "wind_speed": env['wind_speed']
            },
            "air_quality": {
                "pm25": env['pm25'],
                "pm10": env['pm10'],
                "no2": env['no2'],
                "o3": env['o3']
            },
            "pollen": {
                "tree (Universal Pollen Index)": env['tree_pollen'],
                "weed (Universal Pollen Index)": env['weed_pollen'],
                "grass (Universal Pollen Index)": env['grass_pollen']
            }
        })
    return route_data

def prompt_with_nemotron(nemotron_prompt, chat_history=None):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/nvidia/nemotron-3-120b-a12b"

    headers = {
        "Authorization": f"Bearer {CF_API_KEY}",
        "Content-Type": "application/json"
    }

    # 1. Structure the chat history correctly
    messages = []
    if chat_history and isinstance(chat_history, list):
        messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": nemotron_prompt
    })

    payload = {
        "messages": messages
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        response.raise_for_status()

        result_data = response.json()

        if not result_data.get('success', True):
            print(f"Cloudflare API Error: {result_data.get('errors')}")
            return None

        result = result_data.get('result', {})

        # 2. Extract the raw text
        if 'choices' in result:
            raw_text = result['choices'][0]['message']['content']
        elif 'response' in result:
            raw_text = result['response']
        else:
            print(f"Unexpected Cloudflare JSON format: {result_data}")
            return None

        # 3. Clean up the response (Strip Markdown backticks if they exist)
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]

        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        # 4. Return the clean JSON string directly
        return raw_text.strip()

    except requests.exceptions.RequestException as req_err:
        print(f"Network or HTTP Error: {req_err}")
        if hasattr(req_err, 'response') and req_err.response is not None:
             print(f"Raw Response: {req_err.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def general_response(user_prompt, chat_history=None):
    nemotron_prompt = (
        "[SYSTEM ROLE]\n"
        "You are the Orchestration Router for a Medical & Environmental Intelligence Agent. "
        "Your ONLY job is to read the user's prompt, understand their intent, and select the correct tool to execute.\n\n"

        "[INSTRUCTIONS]\n"
        "1. Analyze the [USER PROMPT] and [CHAT HISTORY].\n"
        "2. Match the user's intent to exactly ONE of the tools listed in the [TOOLS] section.\n"
        "3. Output ONLY a raw JSON object. No markdown, no triple backticks, no conversational text.\n\n"

        "[TOOLS]\n"
        "- 'find_route': Use this if the user wants to travel, navigate, or find a safe path from one location to another.\n"
        "- 'forecast': Use this if the user is asking about current or future weather, air quality, or pollen at their current location.\n"
        "- 'wrong_feedback': Use this if the user asks for a joke, general knowledge, or anything outside the scope of health, weather, and navigation.\n\n"

        "[CHAT HISTORY]\n"
        f"<data>\n{chat_history}\n</data>\n\n"

        "[USER PROMPT]\n"
        f"<data>\n{user_prompt}\n</data>\n\n"

        "[OUTPUT_SCHEMA]\n"
        "{\n"
        '  "action": (string, exactly one of: "find_route", "forecast", "wrong_feedback")\n'
        "}"
    )
    answer = json.loads(prompt_with_nemotron(nemotron_prompt))
    return answer['action']

def asking_response(user_prompt):
    nemotron_prompt = (
        "[SYSTEM ROLE]\n"
        "You are a Medical & Route Intelligence Agent."
         "You just warned the user about environmental risks on a suggested route and asked if they accept the risk to proceed.\n\n"

        "[INSTRUCTIONS]\n"
        "1. Analyze the [USER PROMPT].\n"
        "2. Determine if the user's response indicates they want to proceed (yes) or cancel/wait (no).\n"
        "3. If the response is ambiguous or a completely unrelated question, default to 'no' for safety.\n"
        "4. Output ONLY a raw JSON object. No markdown, no triple backticks, no conversational text.\n\n"

        "[USER PROMPT]\n"
        f"<data>\n{user_prompt}\n</data>\n\n"

        "[OUTPUT_SCHEMA]\n"
        "{\n"
        '  "decision": (string, exactly one of: "yes", "no")\n'
        "}"
    )

    raw_response = prompt_with_nemotron(nemotron_prompt)

    # Safe JSON parsing
    try:
        parsed_data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Strip markdown ticks just in case
        clean_text = raw_response.replace("```json", "").replace("```", "").strip()
        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Ultimate fallback if the LLM goes completely off the rails
            return "no"

    # Use .get() with a default of "no" to fail safely
    return parsed_data.get('decision', 'no').lower()

# Don't mind this
def turn_prompt_into_variables(prompt):
  try:

      parsed_data = json.loads(prompt)


      best_route = parsed_data['recommended_route_id']
      trip_verdict = parsed_data['verdict']
      explanation = parsed_data['reasoning_summary']
      hazard_warnings = parsed_data['warnings']

      print(f"Suggested Route: {best_route}")
      print(f"Status: {trip_verdict}")

      print("Health Warnings:")
      for warning in hazard_warnings:
          print(f" - {warning}")
      return parsed_data
  except json.JSONDecodeError:
      print("Failed to parse JSON")

def GO_respond_user(recommended_route_id, verdict, medical_logic, reasoning_summary, warnings):
    llm_payload = {
        "context": {
            "recommended_route_id": recommended_route_id,
            "verdict": verdict,
            "medical_logic": medical_logic,
            "reasoning_summary": reasoning_summary,
            "warnings": warnings
        }
    }

    data_string = json.dumps(llm_payload, indent=2)

    nemotron_prompt = (
        "[SYSTEM ROLE]\n"
        "You are a Medical & Environmental Intelligence Agent. You specialize in analyzing "
        "how atmospheric conditions (pollutants, weather, pollen) impact individuals "
        "based on their age and respiratory health markers (asthma, allergies).\n\n"

        "[INSTRUCTIONS]\n"
        "1. Analyze the <context> provided in the [DATA_INPUT].\n"
        "2. Focus on 'medical_logic' and 'reasoning_summary'.\n"
        "3. Remind the user about the 'warnings' in the chosen route.\n"
        "4. Turn your reasoning into a clear, convincing response addressed directly to the user.\n\n"

        "[CONSTRAINTS]\n"
        "- Use only the numbers provided in the data. Do not invent statistics.\n"
        "- Be professional and helpful.\n\n"

        "[DATA_INPUT]\n"
        f"<data>\n{data_string}\n</data>\n\n"

        "[OUTPUT_SCHEMA]\n"
        "Respond strictly in valid JSON format using the following structure:\n"
        "{\n"
        '  "response": "(string) The final, formatted message to the user."\n'
        "}"
    )
    a = json.loads(prompt_with_nemotron(nemotron_prompt))
    return a['response']

def WAIT_respond_user(medical_logic, reasoning_summary, warnings, suggestion):
    llm_payload = {
        "context": {
            "medical_logic": medical_logic,
            "reasoning_summary": reasoning_summary,
            "warnings": warnings,
            "suggestion": suggestion
        }
    }

    data_string = json.dumps(llm_payload, indent=2)

    nemotron_prompt = (
        "[SYSTEM ROLE]\n"
        "You are a Medical & Environmental Intelligence Agent. You specialize in analyzing "
        "how atmospheric conditions (pollutants, weather, pollen) impact individuals "
        "based on their age and respiratory health markers (asthma, allergies).\n\n"

        "[INSTRUCTIONS]\n"
        "1. Analyze the <context> provided in the [DATA_INPUT].\n"
        "2. Focus on translating 'medical_logic' and 'reasoning_summary' into plain language.\n"
        "3. Explicitly state the 'warnings' for the chosen route so the user knows exactly what they are facing.\n"
        "4. Provide the 'suggestion' items as ideas for what the user can do while waiting for conditions to improve.\n"
        "5. Turn your reasoning into a clear, empathetic, but firm response addressed directly to the user.\n"
        "6. Conclude by explicitly asking the user if they accept the risk and wish to proceed anyway.\n\n"

        "[CONSTRAINTS]\n"
        "- Use only the numbers provided in the data. Do not invent statistics.\n"
        "- Be professional, empathetic, and highly readable.\n\n"

        "[DATA_INPUT]\n"
        f"<data>\n{data_string}\n</data>\n\n"

        "[OUTPUT_SCHEMA]\n"
        "Respond strictly in valid JSON format using the following structure. No markdown or backticks:\n"
        "{\n"
        '  "response": "(string) The final, formatted message to the user."\n'
        "}"
    )

    raw_response = prompt_with_nemotron(nemotron_prompt)

    # Safe JSON parsing to prevent crashes from markdown formatting
    try:
        parsed_data = json.loads(raw_response)
    except json.JSONDecodeError:
        clean_text = raw_response.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_text)

    return parsed_data.get('response', "Error: Could not generate response.")

#############################Tools#########################################

def get_routes(origin, destination, transport, user_data):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    travel_mode = {'driving': 'DRIVE', 'biking': 'BICYCLE', 'walking': 'WALK'}.get(transport.lower(), 'DRIVE')
    payload = {
        "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
        "destination": {"location": {"latLng": {"latitude": destination[0], "longitude": destination[1]}}},
        "travelMode": travel_mode, "computeAlternativeRoutes": True
    }
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY, "X-Goog-FieldMask": "routes.polyline.encodedPolyline"}
    routes = requests.post(url, json=payload, headers=headers).json().get('routes', [])

    all_routes_data = []

    # 1. Create a dictionary to store polylines locally
    polylines_map = {}

    for route_index, route in enumerate(routes):
        route_id = route_index + 1 # Use 1-based indexing for the ID
        encoded_poly = route['polyline']['encodedPolyline']

        # 2. Save the polyline to our local map
        polylines_map[route_id] = encoded_poly

        route_points = get_sample_points(encoded_poly)
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(get_env_data, pt[0], pt[1], API_KEY) for pt in route_points]
            env_results = [future.result() for future in futures]
            route_details = format_comprehensive_route(route_points, env_results)
            all_routes_data.append({
                "route_id": route_id, # 3. Explicitly give the LLM the ID
                "route_label": f"Route {route_id}",
                "checkpoints": route_details
            })

    llm_payload = {
        "trip_context": {
            "transport": travel_mode, "user_age": user_data['age'], "user_asthma(from 0 to 4)": user_data['asthma_severity'], "user_allergy": user_data['allergy'], "heart_condition": user_data['heart_condition']
        },
        "alternatives": all_routes_data
    }

    # Convert the dictionary to a clean JSON string
    data_string = json.dumps(llm_payload, indent=2)

    nemotron_prompt = (
      "[SYSTEM ROLE]\n"
      "You are a Medical & Environmental Intelligence Agent. You specialize in analyzing "
      "how atmospheric conditions (pollutants, weather, pollen) impact individuals "
      "based on their age and respiratory health markers (asthma, allergies).\n\n"

      "[INSTRUCTIONS]\n"
      "1. Analyze the <trip_context> against the <route_options> provided in the [DATA_INPUT].\n"
      "2. Focus on how user information in <trip_context> could be affected by environmental factors.\n"
      "3. Identify synergistic risks (e.g., how high humidity might worsen the impact of PM2.5 for an asthmatic).\n"
      "4. Decide the 'action'. If all routes present a severe health risk (Danger), set 'action' to 'Wait'. Otherwise, set to 'Go'.\n"
      "5. ALWAYS determine a 'recommended_route_id' matching a 'route_id' provided in the data. If the action is 'Go', pick the safest/fastest balance. If the action is 'Wait', pick the *least dangerous* route available.\n"
      "6. If 'action' is 'Wait', explain why the user should wait instead of taking the recommended route, and estimate when conditions might improve.\n"
      "7. If 'action' is 'Wait', populate 'suggestion' with general types of indoor places nearby (e.g., 'a library', 'a local cafe with AC') where the user can safely wait.\n"
      "8. Output ONLY a raw JSON object. No markdown, no triple backticks, no conversational text.\n\n"

      "[CONSTRAINTS]\n"
      "- Use only the numbers provided in the data. Do not invent statistics.\n"
      "- If a route is discarded for health reasons, specify the pollutant or factor in 'warnings'.\n"
      "- Ensure the output is strictly valid JSON.\n\n"

      "[DATA_INPUT]\n"
      f"<data>\n{data_string}\n</data>\n\n"

      "[OUTPUT_SCHEMA]\n"
      "{\n"
      '  "action": "Go" or "Wait",\n'
      '  "recommended_route_id": (integer, the best available route ID, even if action is Wait),\n'
      '  "verdict": "Safe", "Caution", or "Danger",\n'
      '  "medical_logic": (string, your expert physiological reasoning),\n'
      '  "reasoning_summary": (string, why this action/route was chosen),\n'
      '  "warnings": (list of strings, list any potential dangers on the routes),\n'
      '  "suggestion": (list of strings, specific types of places the user should search for nearby to wait safely, empty list if Go)\n'
      "}"
    )


    # 4. Get the response and parse it
    raw_llm_response = prompt_with_nemotron(nemotron_prompt)

    try:
        response_data = json.loads(raw_llm_response)
    except json.JSONDecodeError:
        clean_text = raw_llm_response.replace("```json", "").replace("```", "").strip()
        response_data = json.loads(clean_text)

    # 5. Separate the chosen polyline from the unchosen ones
    chosen_id = response_data.get("recommended_route_id")

    # Set the recommended polyline (will be None if LLM returns null for chosen_id)
    response_data["recommended_polyline"] = polylines_map.get(chosen_id) if chosen_id else None

    # Use a list comprehension to gather all polylines EXCEPT the chosen one
    unchosen = [
        polyline for route_id, polyline in polylines_map.items()
        if route_id != chosen_id
    ]
    response_data["unchosen_polylines"] = unchosen

    return response_data

def forecast(origin, user_data) :
  env_forecast = get_env_forecast(origin[0], origin[1])
  location_data = []
  location_data.append({
            "coordinates": {"lat": round(origin[0], 4), "lng": round(origin[1], 4)},
            "weather": {
                "temp": env_forecast['temp'],
                "humidity": env_forecast['humidity'],
                "wind_speed": env_forecast['wind_speed']
            },
            "air_quality": {
                "pm25": env_forecast['pm25'],
                "pm10": env_forecast['pm10'],
                "no2": env_forecast['no2'],
                "o3": env_forecast['o3']
            },
            "pollen": {
                "tree (Universal Pollen Index)": env_forecast['tree_pollen'],
                "weed (Universal Pollen Index)": env_forecast['weed_pollen'],
                "grass (Universal Pollen Index)": env_forecast['grass_pollen']
            }
        })
  llm_payload = {
          "user_context": {
                "user_age": user_data['age'], "user_asthma(from 0 to 4)": user_data['asthma_severity'], "user_allergy": user_data['allergy'], "heart_condition": user_data['heart_condition'],
            "location_context_2_hours_forecast": location_data
                  }
          }
  data_string = json.dumps(llm_payload, indent=2)
  nemotron_prompt = (
      "[SYSTEM ROLE]\n"
      "You are a Medical & Environmental Intelligence Agent. You specialize in generating "
      "highly personalized, short-term (2-hour) forecast reports by analyzing how upcoming "
      "weather, AQI, and pollen conditions will impact a specific user's respiratory health.\n\n"

      "[INSTRUCTIONS]\n"
      "1. Analyze the <user_profile> against the 2-hour <forecast_data> provided in the [DATA_INPUT].\n"
      "2. Determine the overall 'verdict' for the user to be outside at their current location over the next 2 hours.\n"
      "3. Break the report down into a 'weather_summary' (temperature, rain, wind), 'pollen_summary' and an 'aqi_summary'.\n"
      "4. Provide 'medical_outlook' explaining exactly how the changing conditions will interact with the user's specific health markers.\n"
      "5. Generate actionable 'recommendations' for the user based on the forecast.\n"
      "6. Output ONLY a raw JSON object. No markdown, no triple backticks, no conversational text.\n\n"

      "[CONSTRAINTS]\n"
      "- Use only the numbers provided in the data. Do not invent statistics or weather events.\n"
      "- Ensure the output is strictly valid JSON.\n\n"

      "[DATA_INPUT]\n"
      f"<data>\n{data_string}\n</data>\n\n"

      "[OUTPUT_SCHEMA]\n"
      "{\n"
      '  "verdict": "Safe", "Caution", or "Danger",\n'
      '  "weather_summary": (string, brief summary of temperature/precipitation changes in the next 2 hours),\n'
      '  "aqi_pollen_summary": (string, brief summary of air quality and allergen trends),\n'
      '  "medical_outlook": (string, your expert physiological reasoning linking the forecast to the user profile),\n'
      '  "recommendations": (list of strings, 2 to 3 actionable health or safety tips, e.g., "Keep windows closed", "Bring rescue inhaler")\n'
      "}"
  )
  answer = json.loads(prompt_with_nemotron(nemotron_prompt))
  return answer




############### CONNECT to frontend###############
app = Flask(__name__)
CORS(app)



@app.route('/api/general_response', methods=['POST'])
def api_general_response():
    data = request.json
    user_prompt = data.get('user_prompt', '')
    chat_history = data.get('chat_history', [])
    action = general_response(user_prompt, chat_history)
    return jsonify({"action": action})


@app.route('/api/GO_respond_user', methods=['POST'])
def api_GO_respond_user():
    # 1. Get the JSON payload from the frontend
    data = request.json

    # 2. Extract the variables safely using .get() to prevent KeyErrors
    recommended_route_id = data.get('recommended_route_id')
    verdict = data.get('verdict', 'Safe')
    medical_logic = data.get('medical_logic', '')
    reasoning_summary = data.get('reasoning_summary', '')
    warnings = data.get('warnings', [])

    # 3. Pass the data to your LLM generator function
    response_message = GO_respond_user(
        recommended_route_id=recommended_route_id,
        verdict=verdict,
        medical_logic=medical_logic,
        reasoning_summary=reasoning_summary,
        warnings=warnings
    )

    # 4. Return the generated string to the frontend as proper JSON
    return jsonify({
        "status": "success",
        "message": response_message
    }), 200



@app.route('/api/get_routes', methods=['POST'])
def api_get_routes():
    # 1. Get the JSON payload from the frontend
    data = request.json

    # 2. Extract the required variables
    origin = data.get('origin')           # Expected format: [latitude, longitude]
    destination = data.get('destination') # Expected format: [latitude, longitude]
    transport = data.get('transport', 'driving') # Default to driving if missing
    user_data = data.get('user_data', {})

    # Basic validation to ensure we have coordinates
    if not origin or not destination:
        return jsonify({
            "status": "error",
            "message": "Origin and destination coordinates are required."
        }), 400

    # Ensure user_data has the necessary keys with safe defaults
    safe_user_data = {
        'age': user_data.get('age', 30),
        'asthma_severity': user_data.get('asthma_severity', 0),
        'allergy': user_data.get('allergy', 'none'),
        'heart_condition': user_data.get('heart_condition', 'none')
    }

    try:
        # 3. Pass the data to your main routing function
        route_analysis = get_routes(
            origin=origin,
            destination=destination,
            transport=transport,
            user_data=safe_user_data
        )

        # 4. Return the comprehensive data back to the frontend
        return jsonify({
            "status": "success",
            "data": route_analysis
        }), 200

    except Exception as e:
        # Catch any unexpected errors (e.g., API failures) so the server doesn't crash
        return jsonify({
            "status": "error",
            "message": f"An error occurred while processing routes: {str(e)}"
        }), 500

@app.route('/api/asking_response', methods=['POST'])
def api_asking_response():
    # 1. Get the JSON payload from the frontend
    data = request.json

    # 2. Extract the user's reply safely
    user_prompt = data.get('user_prompt', '').strip()

    # Basic validation: ensure we actually got text
    if not user_prompt:
        return jsonify({
            "status": "error",
            "message": "User prompt is required."
        }), 400

    try:
        # 3. Pass the text to your intent classification function
        decision = asking_response(user_prompt)

        # 4. Return the clean "yes" or "no" decision back to the frontend
        return jsonify({
            "status": "success",
            "decision": decision
        }), 200

    except Exception as e:
        # Failsafe: if the server crashes, default to 'no' for user safety
        return jsonify({
            "status": "error",
            "decision": "no",
            "message": f"An error occurred: {str(e)}"
        }), 500



@app.route('/api/WAIT_respond_user', methods=['POST'])
def api_WAIT_respond_user():
    # 1. Get the JSON payload from the frontend
    data = request.json

    # 2. Extract the variables safely using .get()
    medical_logic = data.get('medical_logic', '')
    reasoning_summary = data.get('reasoning_summary', '')
    warnings = data.get('warnings', [])
    suggestion = data.get('suggestion', [])

    try:
        # 3. Pass the data to your LLM generator function
        response_message = WAIT_respond_user(
            medical_logic=medical_logic,
            reasoning_summary=reasoning_summary,
            warnings=warnings,
            suggestion=suggestion
        )

        # 4. Return the generated warning string to the frontend as proper JSON
        return jsonify({
            "status": "success",
            "message": response_message
        }), 200

    except Exception as e:
        # Fallback error handling
        return jsonify({
            "status": "error",
            "message": "Conditions are currently hazardous. We recommend waiting indoors. Do you accept the risk to proceed?"
        }), 500


@app.route('/api/get_env_forecast', methods=['POST'])
def api_get_env_forecast():
    # 1. Get the JSON payload from the frontend
    data = request.json

    # 2. Extract the necessary variables
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    user_data = data.get('user_data', {})

    # Basic validation: ensure we have the coordinates
    if latitude is None or longitude is None:
        return jsonify({
            "status": "error",
            "message": "Latitude and longitude are required."
        }), 400

    # Ensure user_data has the necessary keys with safe defaults
    safe_user_data = {
        'age': user_data.get('age', 30),
        'asthma_severity': user_data.get('asthma_severity', 0),
        'allergy': user_data.get('allergy', 'none'),
        'heart_condition': user_data.get('heart_condition', 'none')
    }

    try:
        # 3. Call your forecasting and LLM generation function
        forecast_advice = get_env_forecast(
            latitude=float(latitude),
            longitude=float(longitude),
            user_data=safe_user_data
        )

        # 4. Return the structured report back to the frontend
        return jsonify({
            "status": "success",
            "data": forecast_advice
        }), 200

    except ValueError:
        # Catch errors if latitude/longitude aren't valid numbers
        return jsonify({
            "status": "error",
            "message": "Latitude and longitude must be valid numbers."
        }), 400
    except Exception as e:
        # Failsafe for general API or execution errors
        return jsonify({
            "status": "error",
            "message": f"An error occurred while fetching the forecast: {str(e)}"
        }), 500
    

if __name__ == '__main__':
    # Make sure host='0.0.0.0' is set so Tailscale can see it!
    app.run(host='0.0.0.0', debug=True, port=5000)

