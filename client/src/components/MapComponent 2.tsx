// MapComponent.tsx with black pin markers

import { useEffect, useRef, useState } from "react";
import { Loader } from "@googlemaps/js-api-loader";
import { Skeleton } from "./ui/skeleton";

interface MapComponentProps {
  center?: { lat: number; lng: number };
  zoom?: number;
  markers?: Array<{
    lat: number;
    lng: number;
    title?: string;
    type?: 'primary' | 'secondary' | 'reference';
  }>;
  height?: string;
  width?: string;
  onMapClick?: (location: { lat: number; lng: number }) => void;
}

export default function MapComponent({
  center = { lat: 40.7128, lng: -74.006 }, // Default to New York City
  zoom = 10,
  markers = [],
  height = "100%",
  width = "100%",
  onMapClick,
}: MapComponentProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [mapInstance, setMapInstance] = useState<google.maps.Map | null>(null);
  const [mapMarkers, setMapMarkers] = useState<google.maps.Marker[]>([]);

  // Initialize the map
  useEffect(() => {
    const initializeMap = async () => {
      if (!mapRef.current) return;

      try {
        const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
        if (!apiKey) {
          console.error("Google Maps API key is missing");
          setLoading(false);
          return;
        }

        const loader = new Loader({
          apiKey,
          version: "weekly",
          libraries: ["places"],
        });

        const googleMaps = await loader.load();
        const map = new googleMaps.maps.Map(mapRef.current, {
          center,
          zoom,
          mapTypeControl: true,
          streetViewControl: true,
          fullscreenControl: true,
          zoomControl: true,
        });

        if (onMapClick) {
          map.addListener("click", (e: google.maps.MapMouseEvent) => {
            if (e.latLng) {
              onMapClick({
                lat: e.latLng.lat(),
                lng: e.latLng.lng(),
              });
            }
          });
        }

        setMapInstance(map);
        setLoading(false);
      } catch (error) {
        console.error("Error loading Google Maps:", error);
        setLoading(false);
      }
    };

    initializeMap();
  }, []);

  // Update markers when they change
  useEffect(() => {
    if (!mapInstance) return;

    // Clear existing markers
    mapMarkers.forEach((marker) => marker.setMap(null));
    setMapMarkers([]);

    // Add new markers with custom styling
    const newMarkers = markers.map((markerData) => {
      // Set up marker options
      let markerOptions: google.maps.MarkerOptions = {
        position: { lat: markerData.lat, lng: markerData.lng },
        map: mapInstance,
        title: markerData.title || 'Location',
        animation: google.maps.Animation.DROP,
      };

      // Apply different styles based on marker type
      if (markerData.type) {
        switch (markerData.type) {
          case 'primary':
            // Black pin for primary locations
            markerOptions.icon = {
              // Map pin SVG
              url: `data:image/svg+xml,${encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z" fill="black" stroke="black"/>
                  <circle cx="12" cy="10" r="3" fill="white" stroke="white"/>
                </svg>
              `)}`,
              scaledSize: new google.maps.Size(36, 36),
              anchor: new google.maps.Point(18, 36), // Bottom middle of the pin
            };
            break;
          case 'secondary':
            // Gray pin for secondary locations
            markerOptions.icon = {
              url: `data:image/svg+xml,${encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z" fill="#4B5563" stroke="#4B5563"/>
                  <circle cx="12" cy="10" r="3" fill="white" stroke="white"/>
                </svg>
              `)}`,
              scaledSize: new google.maps.Size(30, 30),
              anchor: new google.maps.Point(15, 30), // Bottom middle of the pin
            };
            break;
          case 'reference':
            // Smaller light gray pin for reference locations
            markerOptions.icon = {
              url: `data:image/svg+xml,${encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z" fill="#9CA3AF" stroke="#9CA3AF"/>
                  <circle cx="12" cy="10" r="3" fill="white" stroke="white"/>
                </svg>
              `)}`,
              scaledSize: new google.maps.Size(24, 24),
              anchor: new google.maps.Point(12, 24), // Bottom middle of the pin
            };
            break;
        }
      } else {
        // Default black pin if no type specified
        markerOptions.icon = {
          url: `data:image/svg+xml,${encodeURIComponent(`
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z" fill="black" stroke="black"/>
              <circle cx="12" cy="10" r="3" fill="white" stroke="white"/>
            </svg>
          `)}`,
          scaledSize: new google.maps.Size(36, 36),
          anchor: new google.maps.Point(18, 36), // Bottom middle of the pin
        };
      }

      const marker = new google.maps.Marker(markerOptions);

      // Add info window
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="padding: 8px; max-width: 200px;">
            <h3 style="font-weight: bold; margin-bottom: 4px;">${markerData.title || 'Location'}</h3>
            <p style="font-size: 12px; margin: 0;">
              Lat: ${markerData.lat.toFixed(4)}, Lng: ${markerData.lng.toFixed(4)}
            </p>
          </div>
        `,
      });

      marker.addListener('click', () => {
        infoWindow.open(mapInstance, marker);
      });

      return marker;
    });

    setMapMarkers(newMarkers);

    // Fit bounds if we have markers
    if (newMarkers.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      markers.forEach((marker) => {
        bounds.extend({ lat: marker.lat, lng: marker.lng });
      });
      mapInstance.fitBounds(bounds);
      
      // Adjust zoom if too zoomed in (e.g., if only one marker)
      // Fixed the TypeScript error by using optional chaining and nullish coalescing
      google.maps.event.addListenerOnce(mapInstance, 'bounds_changed', () => {
        const currentZoom = mapInstance?.getZoom() ?? 0;
        if (currentZoom > 15) {
          mapInstance.setZoom(15);
        }
      });
    }
  }, [mapInstance, markers]);

  // Update center when it changes
  useEffect(() => {
    if (mapInstance && center) {
      mapInstance.setCenter(center);
      mapInstance.setZoom(zoom);
    }
  }, [mapInstance, center, zoom]);

  return (
    <div className="relative w-full h-full">
      {loading && <Skeleton className="absolute inset-0 z-10" />}
      <div
        ref={mapRef}
        style={{ height, width }}
        className="rounded-md overflow-hidden"
      />
    </div>
  );
}











