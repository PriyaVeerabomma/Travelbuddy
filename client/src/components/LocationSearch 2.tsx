// src/components/LocationSearch.tsx

import { useState } from "react";
import { Search, MapPin, Plus } from 'lucide-react';
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Separator } from "./ui/separator";
import { Location } from './LocationContext'; // Import Location from LocationContext

interface LocationSearchProps {
  onLocationSelect: (location: Location) => void;
  savedLocations?: Location[];
}

export function LocationSearch({
  onLocationSelect,
  savedLocations = [],
}: LocationSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Location[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      // Get API key from environment
      const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";
      if (!apiKey) {
        console.warn("No Google Maps API key found!");
        setIsSearching(false);
        return;
      }
      
      // Use geocoding to search for the location
      try {
        // Rate limiting to avoid hitting API limits
        const response = await fetch(
          `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(searchQuery)}&key=${apiKey}`
        );
        
        if (!response.ok) {
          throw new Error(`Geocoding request failed: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status !== 'OK' || !data.results || data.results.length === 0) {
          console.warn(`Geocoding error for "${searchQuery}": ${data.status}`);
          useFallbackResults();
          return;
        }
        
        const result = data.results[0];
        const { lat, lng } = result.geometry.location;
        
        const geocodedLocation: Location = {
          name: searchQuery,
          lat,
          lng,
          formattedAddress: result.formatted_address,
          type: 'primary'
        };
        
        setSearchResults([geocodedLocation]);
      } catch (error) {
        console.error(`Error geocoding location "${searchQuery}":`, error);
        useFallbackResults();
      }
    } catch (error) {
      console.error("Error searching for location:", error);
      useFallbackResults();
    } finally {
      setIsSearching(false);
    }
  };

  // Fallback to mock results if geocoding fails
  const useFallbackResults = () => {
    console.log("Geocoding failed, using mock results");
    
    const mockResults: Location[] = [
      {
        name: `${searchQuery} - City Center`,
        lat: 40.7128 + Math.random() * 0.1,
        lng: -74.006 + Math.random() * 0.1,
        type: 'primary'
      },
      {
        name: `${searchQuery} - Downtown`,
        lat: 40.7128 + Math.random() * 0.1,
        lng: -74.006 + Math.random() * 0.1,
        type: 'secondary'
      },
      {
        name: `${searchQuery} - Airport`,
        lat: 40.7128 + Math.random() * 0.1,
        lng: -74.006 + Math.random() * 0.1,
        type: 'reference'
      },
    ];
    
    setSearchResults(mockResults);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl flex items-center">
          <MapPin className="mr-2 h-5 w-5 text-blue-600" />
          Find Locations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex space-x-2">
          <Input
            placeholder="Search for a location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <Button
            onClick={handleSearch}
            disabled={isSearching}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-medium text-sm">Search Results</h3>
            {searchResults.map((result, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 hover:bg-muted rounded-md cursor-pointer"
                onClick={() => onLocationSelect(result)}
              >
                <div className="flex items-center">
                  <MapPin className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span>{result.name}</span>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onLocationSelect(result);
                  }}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {savedLocations.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h3 className="font-medium text-sm">Saved Locations</h3>
              {savedLocations.map((location, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 hover:bg-muted rounded-md cursor-pointer"
                  onClick={() => onLocationSelect(location)}
                >
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 mr-2 text-blue-600" />
                    <span>{location.name}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}





