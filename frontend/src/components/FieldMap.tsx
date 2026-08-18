"use client";
import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix broken default marker icons in Next.js
const markerIcon = L.divIcon({
  className: "",
  html: `
    <div style="
      width: 20px;
      height: 20px;
      background: #3b6d11;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      position: relative;
    ">
      <div style="
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 6px; height: 6px;
        background: white;
        border-radius: 50%;
      "></div>
    </div>
  `,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -12],
});

const FIELD_LOCATION: [number, number] = [12.9298, 80.0629];

export default function FieldMap() {
  return (
    <div className="w-full h-48 rounded-xl overflow-hidden border border-green-100">
      <MapContainer
        center={FIELD_LOCATION}
        zoom={15}
        scrollWheelZoom={false}
        style={{ width: "100%", height: "100%" }}
        zoomControl={true}
        attributionControl={false}
      >
        {/* OpenStreetMap tiles - free, no API key needed */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap contributors"
        />

        {/* Field boundary circle */}
        <Circle
          center={FIELD_LOCATION}
          radius={80}
          pathOptions={{
            color: "#3b6d11",
            fillColor: "#3b6d11",
            fillOpacity: 0.15,
            weight: 2,
          }}
        />

        {/* Field marker */}
        <Marker position={FIELD_LOCATION} icon={markerIcon}>
          <Popup className="leaflet-popup-custom">
            <div style={{ padding: "4px 2px" }}>
              <p style={{ fontWeight: 600, color: "#173404", marginBottom: 2, fontSize: 13 }}>
                📍 Erumaiyur Village
              </p>
              <p style={{ color: "#4a6230", fontSize: 12 }}>Tambaram, Tamil Nadu</p>
              <p style={{ color: "#7a9a5a", fontSize: 11, marginTop: 2 }}>
                12.9298° N, 80.0629° E
              </p>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}