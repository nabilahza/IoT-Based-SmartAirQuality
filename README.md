# IoT-Based-SmartAirQuality
CPC357 IOT ARCHITECTURE AND SMART APPLICATIONS

---
# System Description
This project designed and deployed IoT-based Smart Air Quality on Google Cloud Platform (GCP) which monitor the air quality in the room environment by measuring the gas value using MQ-135 sensor. The system simulates air circulation by activating a fan under moderate, unhealthy, and hazardous air quality conditions, while an LED indicator displays green, yellow, or red to represent the air quality level. 

---
# Repository Structure 

```
IoT-Based-SmartAirQuality/
│
├── README.md                                    # Project documentation
├── dashboard_screenshot/                        # Dashboard screenshots directory
│
├── firmware/                                    # ESP32 firmware
│   └── smart_air_quality.ino                    # Main firmware code
│
├── smart-air-quality-backend/                   # Backend Service (MQTT + Firestore)
│   ├── main.py                                  # Main backend server
│   ├── requirements.txt                         # Python dependencies
│   ├── Dockerfile                               # Docker configuration for backend
│
├── smart-air-quality-dashboard/                 # Frontend Dashboard (Streamlit)
│   ├── app.py                                   # Streamlit web application
│   ├── requirements.txt                         # Python dependencies
│   └── Dockerfile                               # Docker configuration for dashboard
│

```
---
# Security features of Smart Air Quality
- Secure Device Communication (MQTT over TLS)	
- MQTT Authentication	
- Firestore Data Security Rules	
- Firebase Authentication	
