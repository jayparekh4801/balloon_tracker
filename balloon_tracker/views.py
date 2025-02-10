import requests
import numpy as np
import json

from django.shortcuts import render
from django.http import JsonResponse

BALLOONS_DATA = None

def impute_nan_values(arr):
    # Iterate through all elements along the second dimension (axis 1)
    for i in range(arr.shape[1]):  # Loop through 1000 instances
        for j in range(arr.shape[2]):  # Loop through the 3rd dimension (features)
            # If a value is NaN, impute with the mean of the non-NaN values along the first axis (24 values)
            if np.isnan(arr[:, i, j]).any():
                non_nan_values = arr[:, i, j][~np.isnan(arr[:, i, j])]
                if non_nan_values.size > 0:
                    arr[:, i, j] = np.nan_to_num(arr[:, i, j], nan=np.mean(non_nan_values))  # Impute with the mean of the available values

    return arr

def load_data():
    balloons_data = []
    global BALLOONS_DATA
    hours = [f"{i:02d}" for i in range(24)]

    for hour in hours:
        try:
            current_api = f"https://a.windbornesystems.com/treasure/{hour}.json"
            response = requests.request("GET", current_api)
            if response.status_code == 200:
                data = response.json()
                balloons_data.append(data)
        except Exception as e:
            print(hour)
            text_data = "[" + response.text
            data = json.loads(text_data)
            balloons_data.append(data)
            print(e)
    balloons_data = np.array(balloons_data)

    BALLOONS_DATA = impute_nan_values(balloons_data)

load_data()

def get_data(request):
    return render(request, 'index.html')

def get_hourly_data(request, hour):
    try:
        hour = int(hour)  # Convert to integer
        
        # Ensure data is loaded and hour is within range
        if BALLOONS_DATA is None or hour >= BALLOONS_DATA.shape[0]:
            return JsonResponse({"error": "Invalid hour or data not available"}, status=400)

        return JsonResponse({"balloons": BALLOONS_DATA[hour,:150, :].tolist()})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)