import { useEffect, useState } from "react";
import MapComponent from "./MapComponent";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { MapPin, Map } from 'lucide-react';
import { useLocation, Location } from "./LocationContext";
import { Button } from "./ui/button";

export function TravelMapComponent() {
  const { 
    detectedLocations, 
    selectedLocation, 
    setSelectedLocation,
    clearDetectedLocations
  } = useLocation();
  
  const [markers, setMarkers] = useState<Array<{
    lat: number;
    lng: number;
    title?: string;
    type?: 'primary' | 'secondary' | 'reference';
  }>>([]);
  
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number } | undefined>(undefined);
  const [mapZoom, setMapZoom] = useState(2); // Default to world view
  
  // Update markers when detected locations change
  useEffect(() => {
    if (!detectedLocations.length) {
      setMarkers([]);
      setMapCenter(undefined);
      setMapZoom(2);
      return;
    }
    
    // Filter valid locations (non-null lat/lng)
    const validLocations = detectedLocations.filter(
      loc => loc.lat != null && loc.lng != null
    ) as Location[]; // Assert non-null lat/lng for valid locations
    
    // Convert valid locations to markers
    const newMarkers = validLocations.map(location => ({
      lat: location.lat!, // Safe due to filter
      lng: location.lng!, // Safe due to filter
      title: location.name,
      type: location.type
    }));
    
    setMarkers(newMarkers);
    
    // Set center to the highest relevance location
    const primaryLocations = validLocations
      .filter(loc => loc.type === 'primary')
      .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
    
    if (primaryLocations.length > 0) {
      setMapCenter({ lat: primaryLocations[0].lat!, lng: primaryLocations[0].lng! });
      setMapZoom(primaryLocations.length === 1 ? 8 : 5);
    } else if (validLocations.length > 0) {
      setMapCenter({ lat: validLocations[0].lat!, lng: validLocations[0].lng! });
      setMapZoom(validLocations.length > 1 ? 4 : 8);
    } else {
      // No valid locations; keep default center
      setMapCenter(undefined);
      setMapZoom(2);
    }
  }, [detectedLocations]);
  
  // Update center when selected location changes
  useEffect(() => {
    if (selectedLocation && selectedLocation.lat != null && selectedLocation.lng != null) {
      setMapCenter({ lat: selectedLocation.lat, lng: selectedLocation.lng });
      setMapZoom(10);
    }
  }, [selectedLocation]);
  
  // Handle map click to select location
  const handleMapClick = (location: { lat: number; lng: number }) => {
    const newLocation: Location = {
      name: `Selected Location (${location.lat.toFixed(4)}, ${location.lng.toFixed(4)})`,
      lat: location.lat,
      lng: location.lng,
      type: 'primary',
      relevanceScore: 100
    };
    
    setSelectedLocation(newLocation);
  };
  
  return (
    <Card className="shadow-lg h-full">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 flex flex-row items-center justify-between">
        <CardTitle className="flex items-center">
          <Map className="mr-2 h-5 w-5 text-blue-600" />
          Travel Map
        </CardTitle>
        {detectedLocations.length > 0 && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => clearDetectedLocations()}
          >
            Clear Pins
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[600px]">
          <MapComponent 
            markers={markers}
            center={mapCenter}
            zoom={mapZoom}
            onMapClick={handleMapClick}
            height="600px"
          />
        </div>
      </CardContent>
      
      {/* Location List Overlay */}
      {detectedLocations.length > 0 && (
        <div className="absolute top-16 right-4 bg-white rounded-lg shadow-lg p-4 max-w-xs max-h-[400px] overflow-auto z-10">
          <h3 className="text-sm font-semibold mb-2 flex items-center">
            <MapPin className="h-4 w-4 mr-1 text-blue-600" />
            Detected Locations
          </h3>
          <div className="space-y-2">
            {detectedLocations
              .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0))
              .map((location, index) => (
                <div 
                  key={index}
                  className={`p-2 rounded-md cursor-pointer border-l-4 ${
                    location.isMock
                      ? 'border-red-400 bg-red-50'
                      : location.type === 'primary' 
                        ? 'border-blue-600 bg-blue-50' 
                        : location.type === 'secondary'
                          ? 'border-blue-400 bg-gray-50'
                          : 'border-gray-300'
                  } ${selectedLocation?.name === location.name ? 'ring-1 ring-blue-400' : ''}`}
                  onClick={() => setSelectedLocation(location)}
                >
                  <div className="font-medium text-sm">{location.name}</div>
                  {location.isMock ? (
                    <div className="text-xs text-red-500 mt-1">Location not found</div>
                  ) : (
                    location.formattedAddress && (
                      <div className="text-xs text-gray-500 mt-1">{location.formattedAddress}</div>
                    )
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
    </Card>
  );
}





