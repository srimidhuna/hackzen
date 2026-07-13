def get_traffic_density(total_vehicles: int):
    """
    Determine the traffic density classification based on total unique vehicles processed.
    """
    if total_vehicles <= 20:
        return {"level": "LOW", "color": "green", "color_hex": "#22c55e"}
    elif total_vehicles <= 50:
        return {"level": "MEDIUM", "color": "yellow", "color_hex": "#eab308"}
    else:
        return {"level": "HIGH", "color": "red", "color_hex": "#ef4444"}

def generate_ai_insights(counts: dict, total_vehicles: int, density: dict):
    """Generate AI-style traffic insights text for the dashboard panel."""
    peak_vehicle = max(counts, key=counts.get) if any(counts.values()) else "None"
    peak_count = counts.get(peak_vehicle, 0)
    
    level = density["level"]
    
    if level == "LOW":
        status = "Normal"
        risk = "Low"
        summary = f"Traffic flow is smooth with {total_vehicles} vehicles detected. {peak_vehicle}s dominate at {peak_count} units."
        recommendations = [
            "No congestion detected. Roads are clear.",
            "Optimal time for route planning.",
            "Continue normal traffic signal timing."
        ]
    elif level == "MEDIUM":
        status = "Moderate"
        risk = "Medium"
        summary = f"Moderate traffic activity with {total_vehicles} vehicles. {peak_vehicle} is the most common type ({peak_count} detected)."
        recommendations = [
            "Consider adaptive signal timing adjustments.",
            "Monitor for potential congestion buildup.",
            f"High {peak_vehicle.lower()} volume detected — check lane allocation."
        ]
    else:
        status = "Congested"
        risk = "High"
        summary = f"Heavy traffic detected: {total_vehicles} vehicles on the road. {peak_vehicle}s lead with {peak_count} units."
        recommendations = [
            "Activate congestion mitigation protocols.",
            "Recommend alternate route diversion.",
            "Deploy additional traffic management resources.",
            f"Critical {peak_vehicle.lower()} volume — prioritize lane management."
        ]
    
    return {
        "summary": summary,
        "status": status,
        "risk": risk,
        "risk_color": density["color_hex"],
        "peak_vehicle": peak_vehicle,
        "recommendations": recommendations
    }

def generate_analytics_summary(counts: dict, total_vehicles: int):
    """
    Returns metrics based on the current stats.
    """
    density = get_traffic_density(total_vehicles)
    
    peak_vehicle = "None"
    max_count = 0
    for v_type, count in counts.items():
        if count > max_count:
            max_count = count
            peak_vehicle = v_type
    
    insights = generate_ai_insights(counts, total_vehicles, density)
            
    return {
        "density": density,
        "peak_vehicle_type": peak_vehicle,
        "total": total_vehicles,
        "distribution": counts,
        "insights": insights
    }
