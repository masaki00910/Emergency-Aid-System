#!/usr/bin/env python3
"""
Simple backend server for testing frontend API integration.
Serves mock data in the same format as the actual backend.
"""

import json
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Mock data that matches the API schema
mock_incidents = [
    {
        "id": "i1",
        "title": "地震（震度5弱）",
        "lat": 43.0642,
        "lng": 141.3469,
        "isActive": True,
        "hazard": "earthquake",
        "area": "札幌",
        "severity": "high",
        "reportedAt": int(time.time() * 1000) - 15 * 60 * 1000,  # 15 minutes ago
        "description": "札幌市で震度5弱の地震が発生しました。"
    },
    {
        "id": "i2",
        "title": "大雨・冠水",
        "lat": 40.8246,
        "lng": 140.7400,
        "isActive": False,
        "hazard": "flood",
        "area": "青森",
        "severity": "medium",
        "reportedAt": int(time.time() * 1000) - 50 * 60 * 1000,
        "description": "青森市で大雨による道路冠水が発生しています。"
    },
    {
        "id": "i3",
        "title": "台風接近",
        "lat": 34.6937,
        "lng": 135.5023,
        "isActive": True,
        "hazard": "typhoon",
        "area": "大阪",
        "severity": "high",
        "reportedAt": int(time.time() * 1000) - 10 * 60 * 1000,
        "description": "大阪府に台風が接近中です。"
    }
]

mock_alerts = [
    {
        "id": "a1",
        "title": "地震注意報（関東）",
        "level": "warning",
        "hazard": "earthquake",
        "area": "関東",
        "startedAt": int(time.time() * 1000) - 15 * 60 * 1000,
        "updatedAt": int(time.time() * 1000) - 5 * 60 * 1000
    },
    {
        "id": "a2",
        "title": "大雨警報（東京23区）",
        "level": "watch",
        "hazard": "flood",
        "area": "東京23区",
        "startedAt": int(time.time() * 1000) - 45 * 60 * 1000,
        "updatedAt": int(time.time() * 1000) - 10 * 60 * 1000
    }
]

mock_feeds = [
    {
        "id": "f1",
        "incidentId": "i1",
        "source": "jma",
        "title": "【地震情報】北海道で震度5弱",
        "summary": "交通機関に影響の可能性。余震に注意してください。",
        "url": "https://www.jma.go.jp/",
        "publishedAt": int(time.time() * 1000) - 10 * 60 * 1000,
        "labels": ["警報", "地震"],
        "area": "北海道",
        "hazard": "earthquake",
        "isAlertCandidate": True
    },
    {
        "id": "f2",
        "incidentId": "i2",
        "source": "nhk",
        "title": "大雨の影響で一部路線で遅延",
        "url": "https://www.nhk.or.jp/",
        "publishedAt": int(time.time() * 1000) - 60 * 60 * 1000,
        "labels": ["注意報", "大雨"],
        "area": "青森",
        "hazard": "flood",
        "isAlertCandidate": True
    },
    {
        "id": "f3",
        "incidentId": "i3",
        "source": "tenki",
        "title": "台風12号 近畿地方に接近中",
        "summary": "強風・高波に警戒してください。",
        "url": "https://tenki.jp/",
        "publishedAt": int(time.time() * 1000) - 5 * 60 * 1000,
        "labels": ["台風", "警報"],
        "area": "近畿",
        "hazard": "typhoon",
        "isAlertCandidate": True
    }
]

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    """Get incidents with optional since parameter"""
    since = request.args.get('since')
    incidents = mock_incidents.copy()

    if since:
        try:
            since_ms = int(since)
            incidents = [i for i in incidents if i['reportedAt'] >= since_ms]
        except ValueError:
            pass

    return jsonify(incidents)

@app.route('/api/incidents/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Get a specific incident by ID"""
    incident = next((i for i in mock_incidents if i['id'] == incident_id), None)
    if incident:
        return jsonify(incident)
    return jsonify({"error": "Incident not found"}), 404

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional active filter"""
    active_only = request.args.get('active') == 'true'
    alerts = mock_alerts.copy()

    if active_only:
        # Filter for 'active' alerts (warning level)
        alerts = [a for a in alerts if a['level'] == 'warning']

    return jsonify(alerts)

@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert by ID"""
    alert = next((a for a in mock_alerts if a['id'] == alert_id), None)
    if alert:
        return jsonify(alert)
    return jsonify({"error": "Alert not found"}), 404

@app.route('/api/feeds', methods=['GET'])
def get_feeds():
    """Get feeds with optional filters"""
    limit = request.args.get('limit', 50)
    incident_id = request.args.get('incidentId')

    try:
        limit = int(limit)
    except ValueError:
        limit = 50

    feeds = mock_feeds.copy()

    if incident_id:
        feeds = [f for f in feeds if f.get('incidentId') == incident_id]

    # Sort by publishedAt (newest first) and limit
    feeds.sort(key=lambda x: x['publishedAt'], reverse=True)
    feeds = feeds[:limit]

    return jsonify(feeds)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time() * 1000),
        "service": "mock_backend"
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info"""
    return jsonify({
        "message": "Emergency Aid System - Mock Backend",
        "version": "1.0.0",
        "endpoints": {
            "incidents": "/api/incidents",
            "alerts": "/api/alerts",
            "feeds": "/api/feeds",
            "health": "/health"
        }
    })

if __name__ == '__main__':
    print("Starting Mock Backend Server...")
    print("API Endpoints:")
    print("   - http://localhost:8080/api/incidents")
    print("   - http://localhost:8080/api/alerts")
    print("   - http://localhost:8080/api/feeds")
    print("   - http://localhost:8080/health")
    print("")
    print("For frontend integration:")
    print("   Set NEXT_PUBLIC_USE_FIREBASE=false")
    print("   Set NEXT_PUBLIC_API_BASE_URL=http://localhost:8080")
    print("")

    app.run(host='0.0.0.0', port=8080, debug=True)