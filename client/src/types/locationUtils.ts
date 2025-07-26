// locationUtils.ts - need to change if testing is working
import { Location } from '@/components/LocationContext';


// Define common travel-related words for better location extraction
const travelVerbs = ['visit', 'go', 'travel', 'fly', 'explore', 'see', 'discover', 'stay'];
const travelPrepositions = ['to', 'in', 'at', 'near', 'around', 'by', 'from'];
const ignoreWords = [
  'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when',
  'where', 'how', 'which', 'who', 'whom', 'whose', 'that', 'there', 'here',
  'like', 'want', 'would', 'could', 'should', 'will', 'plan', 'looking'
];

/**
 * Basic location extraction from text
 * In a production app, you would likely use the AI's structured output
 * or a dedicated NLP service for better extraction
 */
export async function extractLocationsFromText(text: string): Promise<Location[]> {
  if (!text) return [];
  
  // Simple regex-based location extraction
  // Look for patterns: "in X", "to X", "visit X", etc.
  const patterns = [
    // Match capitalized words following travel prepositions (in Paris)
    new RegExp(`\\b(${travelPrepositions.join('|')})\\s+([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)*)`, 'g'),
    
    // Match capitalized words following travel verbs (visit Paris)
    new RegExp(`\\b(${travelVerbs.join('|')})(?:ing)?\\s+([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)*)`, 'g'),
    
    // Match consecutive capitalized words (New York City)
    /\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)\b/g,
    
    // Match standalone capitalized words that may be city names but exclude common non-location words
    /\b([A-Z][a-zA-Z]{3,})\b/g
  ];
  
  // Extract potential locations
  const potentialLocations: Set<string> = new Set();
  
  patterns.forEach(pattern => {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const location = match[2] || match[1]; // group 2 contains the location for patterns with prepositions/verbs
      if (location && location.length > 3 && !ignoreWords.includes(location.toLowerCase())) {
        potentialLocations.add(location.trim());
      }
    }
  });
  
  // Convert potential locations to Location objects
  // In a real app, you'd use the Google Geocoding API here
  const locations: Location[] = [];
  
  for (const name of potentialLocations) {
    try {
      // Here we would call the geocoding API
      // For now, we'll simulate it with random coordinates based on name
      // We use the name's characters to generate "pseudo-random" but consistent coordinates
      const nameHash = Array.from(name).reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const lat = 20 + (nameHash % 50);
      const lng = -100 + (nameHash % 180);
      
      // Calculate relevance score based on context
      let relevanceScore = 50; // Base score
      
      // Higher score if mentioned with travel intent verbs
      travelVerbs.forEach(verb => {
        if (text.toLowerCase().includes(`${verb} ${name.toLowerCase()}`)) {
          relevanceScore += 20;
        }
      });
      
      // Higher score if mentioned with destination prepositions
      travelPrepositions.forEach(prep => {
        if (text.toLowerCase().includes(`${prep} ${name.toLowerCase()}`)) {
          relevanceScore += 15;
        }
      });
      
      // Higher score if mentioned multiple times
      const nameMatches = text.match(new RegExp(name, 'gi'));
      if (nameMatches) {
        relevanceScore += nameMatches.length * 10;
      }
      
      // Determine location type based on relevance
      let type: 'primary' | 'secondary' | 'reference' = 'reference';
      if (relevanceScore >= 80) type = 'primary';
      else if (relevanceScore >= 60) type = 'secondary';
      
      locations.push({
        name,
        lat,
        lng,
        relevanceScore,
        type,
        description: `Location mentioned in your query`
      });
    } catch (error) {
      console.error(`Error geocoding location "${name}":`, error);
    }
  }
  
  return locations;
}

/**
 * Geocode a location using Google Maps Geocoding API
 * In a real app, replace the mock implementation with actual API calls
 */
export async function geocodeLocation(locationName: string): Promise<Location | null> {
  try {
    // In a real implementation, you would call:
    // const response = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(locationName)}&key=${API_KEY}`);
    // const data = await response.json();
    
    // For this example, we'll return mock data
    const nameHash = Array.from(locationName).reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    return {
      name: locationName,
      lat: 20 + (nameHash % 50),
      lng: -100 + (nameHash % 180),
      relevanceScore: 80,
      type: 'primary',
      description: `Geocoded location: ${locationName}`
    };
  } catch (error) {
    console.error(`Error geocoding location "${locationName}":`, error);
    return null;
  }
}

/**
 * Replace the mock geocoding with actual Google API in production
 */
export async function initializeGeocoder(apiKey: string): Promise<void> {
  // In a real app, you might initialize the geocoder here
  console.log('Geocoder initialized with API key:', apiKey);
}