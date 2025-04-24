from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import csv
import requests
import re

# Set up OpenAI API key


# Initialize FastAPI app
app = FastAPI()

# Define request model
class StressAnalysisRequest(BaseModel):
    account_transactions: list
    health_metrics: dict

# Define response model
class StressAnalysisResponse(BaseModel):
    financial_stress: str
    mental_stress: str

# Updated function to call OpenAI using REST API
def openai_call(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer ",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4.1",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    response_data = response.json()
    response_text = response_data["choices"][0]["message"]["content"].strip()
    print(f"Raw OpenAI Response: {response_text}")  # Log raw response for debugging
    return response_text

# Updated function to log OpenAI responses for debugging
def analyze_stress_level(response_text):
    response_text = str(response_text)  # Convert to string if not already
    print(f"Raw OpenAI Response for Stress Level Analysis: {response_text}")  # Log response for debugging
    if "stress" in response_text.lower():
        return "high"
    elif "anxiety" in response_text.lower():
        return "medium"
    elif "calm" in response_text.lower():
        return "low"
    else:
        print("Stress level not identified in response.")  # Log if no match is found
        return "unknown"

# Updated function to analyze stress level based on health metrics
def analyze_health_metrics(health_metrics):
    # Analyze heart rate
    avg_heart_rate = sum(health_metrics["heart_rate"]) / len(health_metrics["heart_rate"])
    if avg_heart_rate > 100:
        heart_rate_stress = "high"
    elif avg_heart_rate > 80:
        heart_rate_stress = "medium"
    else:
        heart_rate_stress = "low"

    # Analyze sleep hours
    avg_sleep_hours = sum(health_metrics["sleep_hours"]) / len(health_metrics["sleep_hours"])
    if avg_sleep_hours < 6:
        sleep_stress = "high"
    elif avg_sleep_hours < 7:
        sleep_stress = "medium"
    else:
        sleep_stress = "low"

    # Analyze blood pressure
    avg_systolic = sum(health_metrics["systolic"]) / len(health_metrics["systolic"])
    if avg_systolic > 140:
        blood_pressure_stress = "high"
    elif avg_systolic > 120:
        blood_pressure_stress = "medium"
    else:
        blood_pressure_stress = "low"

    return {
        "heart_rate_stress": heart_rate_stress,
        "sleep_stress": sleep_stress,
        "blood_pressure_stress": blood_pressure_stress
    }

@app.post("/analyze-stress", response_model=StressAnalysisResponse)
async def analyze_stress():
    # Load data from CSV and API
    mock_account_transactions = load_transaction_data("Statement_2025_3.csv")
    mock_health_metrics = load_health_metrics_from_api(user_id=10)

    # Financial stress analysis
    financial_prompt = f"Analyze the financial stress based on these transactions: {mock_account_transactions}"
    print(f"Financial Prompt: {financial_prompt}")
    financial_response = openai_call(financial_prompt)
    financial_stress = analyze_stress_level(financial_response)

    # Mental stress analysis based on health metrics
    health_stress = analyze_health_metrics(mock_health_metrics)

    return StressAnalysisResponse(
        financial_stress=financial_stress,  # Return stress level as high, medium, or low
        mental_stress=str(health_stress)  # Convert health stress dictionary to string
    )

# Updated function to load transaction data from CSV file
def load_transaction_data(file_path):
    transactions = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:  # Added encoding to handle BOM if present
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            transactions.append({
                "date": row["Date"],
                "description": row["Description"],
                "type": row["Type"],
                "money_in": float(row["Money In (£)"].replace(",", "")) if row["Money In (£)"] else 0.0,
                "money_out": float(row["Money Out (£)"].replace(",", "")) if row["Money Out (£)"] else 0.0,
                "balance": float(row["Balance (£)"].replace(",", ""))
            })
    return transactions

# Updated function to include 'date' in health metrics
def load_health_metrics_from_api(user_id):
    url = f"https://health-service.azurewebsites.net/api/health?userId={user_id}"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    data = response.json()

    health_metrics = {
        "date": [entry["date"] for entry in data.get("dailyData", [])],
        "heart_rate": [entry["heartRate"] for entry in data.get("dailyData", [])],
        "sleep_hours": [entry["sleepHours"] for entry in data.get("dailyData", [])],
        "systolic": [entry["systolicPressure"] for entry in data.get("dailyData", [])],
        "diastolic": [entry["diastolicPressure"] for entry in data.get("dailyData", [])]
    }
    return health_metrics

@app.post("/analyze-daily-health-stress", response_model=list)
async def analyze_daily_health_stress():
    # Load health metrics data from API
    health_metrics = load_health_metrics_from_api(user_id=10)

    # Prepare daily stress levels
    daily_stress_levels = []

    for i in range(len(health_metrics["heart_rate"])):
        # Extract daily metrics
        daily_metrics = {
            "heart_rate": [health_metrics["heart_rate"][i]],
            "sleep_hours": [health_metrics["sleep_hours"][i]],
            "systolic": [health_metrics["systolic"][i]],
            "diastolic": [health_metrics["diastolic"][i]]
        }

        # Analyze stress for the day
        daily_stress = analyze_health_metrics(daily_metrics)

        # Append daily stress level with date
        daily_stress_levels.append({
            "date": health_metrics["date"][i],
            "stress_levels": daily_stress
        })

    return daily_stress_levels

# Updated function to analyze financial stress level based on thresholds
def analyze_financial_stress_level(transaction):
    stress_value = transaction["money_in"] - transaction["money_out"]
    if stress_value > 1000:
        return "low"
    elif stress_value > 500:
        return "medium"
    else:
        return "high"

@app.post("/analyze-daily-financial-stress", response_model=list)
async def analyze_daily_financial_stress():
    # Load transaction data from CSV
    transactions = load_transaction_data("Statement_2025_3.csv")

    # Limit analysis to the first 10 days
    transactions = transactions[:10]

    # Prepare daily financial stress levels
    daily_financial_stress = []

    for transaction in transactions:
        # Analyze financial stress based on thresholds
        financial_stress = analyze_financial_stress_level(transaction)

        # Append daily financial stress level with date
        daily_financial_stress.append({
            "date": transaction["date"],
            "financial_stress": financial_stress
        })

    return daily_financial_stress
