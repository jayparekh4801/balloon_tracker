import requests
import numpy as np
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache  # Optional: Django cache system to store data

def impute_nan_values(arr):
    # Efficiently impute NaN values along features
    for i in range(arr.shape[1]):  # Loop through 1000 instances
        for j in range(arr.shape[2]):  # Loop through features
            # If a value is NaN, impute with the mean of the non-NaN values along the first axis (24 values)
            if np.isnan(arr[:, i, j]).any():
                non_nan_values = arr[:, i, j][~np.isnan(arr[:, i, j])]
                if non_nan_values.size > 0:
                    mean_value = np.mean(non_nan_values)
                    arr[:, i, j] = np.where(np.isnan(arr[:, i, j]), mean_value, arr[:, i, j])

    return arr

def load_data():
    # Load data and cache it for reuse
    balloons_data = []
    hours = [f"{i:02d}" for i in range(24)]

    for hour in hours:
        try:
            current_api = f"https://a.windbornesystems.com/treasure/{hour}.json"
            response = requests.get(current_api)
            response.raise_for_status()  # Check if request was successful

            data = response.json()
            balloons_data.append(data)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for hour {hour}: {e}")
            # Handle failed request, e.g., use default data or skip
            # balloons_data.append([])  # Empty data or default value
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for hour {hour}: {e}")
            data = "[" + response.text
            data = json.loads(data)
            balloons_data.append(data)

    # Convert data to a numpy array
    balloons_data = np.array(balloons_data)

    # Impute missing values
    balloons_data = impute_nan_values(balloons_data)

    # Cache data in Django cache (optional)
    cache.set('balloons_data', balloons_data, timeout=86400)  # Cache for 24 hours

def get_data(request):
    # Ensure data is loaded
    if cache.get('balloons_data') is None:
        load_data()

    return render(request, 'index.html')

def get_hourly_data(request, hour):
    try:
        hour = int(hour)  # Convert to integer

        # Fetch data from cache
        balloons_data = cache.get('balloons_data')
        
        if balloons_data is None or hour >= balloons_data.shape[0]:
            return JsonResponse({"error": "Invalid hour or data not available"}, status=400)

        return JsonResponse({"balloons": balloons_data[hour, :150, :].tolist()})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_balloon_trajectory(request, balloon_number):
    try:
        balloon_number = int(balloon_number)
        balloons_data = cache.get('balloons_data')

        trajectory = balloons_data[:, balloon_number, :]
        return JsonResponse({"trajectory": trajectory.tolist()})
    except (ValueError, IndexError):
        return JsonResponse({"error": "Invalid balloon number"}, status=400)
