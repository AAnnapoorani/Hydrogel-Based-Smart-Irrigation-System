"use client";

import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Clean custom marker icon
const markerIcon = L.divIcon({
  className: "",
  html: `
    <div style="
      width: 18px;
      height: 18px;
      background: #15803d;
      border: 2px solid #ffffff;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.25);
      position: relative;
    ">
      <div style="
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 6px; height: 6px;
        background: #ffffff;
        border-radius: 50%;
      "></div>
    </div>
  `,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
  popupAnchor: [0, -10],
});

const FIELD_LOCATION: [number, number] = [12.9298, 80.0629];

export default function FieldMap() {
  return (
    <div className="w-full h-48 rounded-xl overflow-hidden border border-slate-200/80 shadow-soft">
      <MapContainer
        center={FIELD_LOCATION}
        zoom={15}
        scrollWheelZoom={false}
        style={{ width: "100%", height: "100%" }}
        zoomControl={true}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap contributors"
        />

        {/* Field boundary circle */}
        <Circle
          center={FIELD_LOCATION}
          radius={80}
          pathOptions={{
            color: "#15803d",
            fillColor: "#15803d",
            fillOpacity: 0.12,
            weight: 2,
          }}
        />

        {/* Field marker */}
        <Marker position={FIELD_LOCATION} icon={markerIcon}>
          <Popup className="leaflet-popup-custom">
            <div className="text-xs">
              <p className="font-semibold text-slate-900 mb-0.5 text-xs">
                Tambaram Terrace Research Station
              </p>
              <p className="text-slate-600 text-[11px]">10 × 15L Grow Bags · Tamil Nadu</p>
              <p className="text-slate-400 text-[10px] mt-1 font-mono">
                12.9298° N, 80.0629° E
              </p>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}