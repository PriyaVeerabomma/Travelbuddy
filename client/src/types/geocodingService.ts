import { Location } from '@/components/LocationContext';

// Track API requests to avoid hitting rate limits
let lastRequestTime = 0;
const requestDelay = 300; // ms between requests

/**
 * Extract locations from text using refined NLP patterns
 */
export async function extractLocationsFromText(text: string): Promise<string[]> {
  if (!text) return [];
  
  const travelVerbs = ['visit', 'go', 'travel', 'fly', 'explore', 'see', 'discover', 'stay', 'recommend'];
  const travelPrepositions = ['to', 'in', 'at', 'near', 'around', 'by', 'from'];
  const ignoreWords = [
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when',
    'where', 'how', 'which', 'who', 'whom', 'whose', 'that', 'there', 'here',
    'like', 'want', 'would', 'could', 'should', 'will', 'plan', 'looking',
    'recommend', 'recommending', 'exploring', 'visiting', 'traveling', 'staying',
    'beaches', 'hotels', 'near'
  ];
  
  // Normalize text: capitalize first letter of each word
  const normalizedText = text
    .toLowerCase()
    .replace(/(^|\s)\w/g, letter => letter.toUpperCase());
  
  const patterns = [
    // Preposition + Phrase (e.g., "to New York")
    new RegExp(`\\b(${travelPrepositions.join('|')})\\s+([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)*)`, 'g'),
    // Verb + Phrase (e.g., "visit Paris")
    new RegExp(`\\b(${travelVerbs.join('|')})(?:ing)?\\s+([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)*)`, 'g'),
    // Multi-word Phrases (e.g., "Los Angeles")
    /\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)\b/g,
    // Single-word locations (e.g., "India")
    /\b([A-Z][a-zA-Z]{3,})\b/g
  ];
  
  const potentialLocations: Set<string> = new Set();
  
  patterns.forEach((pattern, index) => {
    let match;
    while ((match = pattern.exec(normalizedText)) !== null) {
      const location = match[2] || match[1];
      if (location && location.length > 2 && !ignoreWords.includes(location.toLowerCase())) {
        console.log(`Pattern ${index} matched: "${location}"`);
        potentialLocations.add(location.trim());
      }
    }
  });
  
  const locations = Array.from(potentialLocations);
  console.log("Final extracted location names:", locations);
  return locations;
}

/**
 * Calculate relevance score for a location based on context
 */
export function calculateRelevanceScore(locationName: string, query: string): number {
  let relevanceScore = 50;
  const locationLower = locationName.toLowerCase();
  const queryLower = query.toLowerCase();
  
  const travelVerbs = ['visit', 'go', 'travel', 'fly', 'explore', 'see', 'discover', 'stay', 'recommend'];
  const travelPrepositions = ['to', 'in', 'at', 'near', 'around', 'by', 'from'];
  
  travelVerbs.forEach(verb => {
    if (queryLower.includes(`${verb} ${locationLower}`)) {
      relevanceScore += 20;
    }
  });
  
  travelPrepositions.forEach(prep => {
    if (queryLower.includes(`${prep} ${locationLower}`)) {
      relevanceScore += 15;
    }
  });
  
  const nameMatches = (queryLower.match(new RegExp(locationLower, 'g')) || []).length;
  if (nameMatches > 1) {
    relevanceScore += nameMatches * 10;
  }
  
  const firstHalf = queryLower.substring(0, queryLower.length / 2);
  if (firstHalf.includes(locationLower)) {
    relevanceScore += 10;
  }
  
  return Math.min(relevanceScore, 100);
}

/**
 * Geocode a location using the backend proxy to Google Maps API
 */
export async function geocodeLocation(locationName: string, apiKey: string): Promise<Location | null> {
  try {
    // Rate limiting
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    if (timeSinceLastRequest < requestDelay) {
      await new Promise(resolve => setTimeout(resolve, requestDelay - timeSinceLastRequest));
    }
    lastRequestTime = Date.now();

    console.log(`Geocoding "${locationName}"`);

    // Check cache
    const cacheKey = `geocode_${locationName.toLowerCase()}`;
    const cachedResult = localStorage.getItem(cacheKey);
    if (cachedResult) {
      console.log(`Using cached result for "${locationName}"`);
      return JSON.parse(cachedResult);
    }

    // Backend Proxy
    const baseUrl = import.meta.env.VITE_BASE_URL || '';
    const backendProxy = `${baseUrl}/api/maps/geocode`;
    
    console.log(`Fetching: ${backendProxy}?address=${encodeURIComponent(locationName)}`);
    
    const response = await fetch(
      `${backendProxy}?address=${encodeURIComponent(locationName)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend proxy failed for "${locationName}": Status ${response.status}, Details:`, errorText);
      throw new Error(`Backend proxy request failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`Geocoding response for "${locationName}":`, data);
    
    if (data.status === 'OK' && data.results && data.results.length > 0) {
      const result = data.results[0];
      const { lat, lng } = result.geometry.location;
      
      const location: Location = {
        name: locationName,
        lat,
        lng,
        formattedAddress: result.formatted_address,
        placeId: result.place_id,
        type: 'primary',
        isMock: false
      };

      localStorage.setItem(cacheKey, JSON.stringify(location));
      console.log(`Successfully geocoded "${locationName}":`, location);
      return location;
    } else {
      console.warn(`Geocoding failed for "${locationName}": ${data.status}`);
      return null;
    }

  } catch (error) {
    console.error(`Error geocoding "${locationName}":`, error);
    return null;
  }
}

/**
 * Process a message to extract, geocode, and score locations
 */
export async function processLocationQuery(
  query: string,
  apiKey: string,
  onUpdate?: (locations: Location[]) => void
): Promise<Location[]> {
  try {
    console.log("Processing query:", query);
    const locationNames = await extractLocationsFromText(query);
    console.log("Extracted location names:", locationNames);
    
    if (locationNames.length === 0) {
      console.log("No locations found in query");
      return [];
    }
    
    const locations: Location[] = [];
    
    for (const name of locationNames) {
      try {
        const geocoded = await geocodeLocation(name, apiKey);
        if (!geocoded) {
          console.log(`Skipping "${name}" due to geocoding failure`);
          continue;
        }
        
        const score = calculateRelevanceScore(name, query);
        
        let type: 'primary' | 'secondary' | 'reference' = 'reference';
        if (score >= 80) type = 'primary';
        else if (score >= 60) type = 'secondary';
        
        const location: Location = {
          ...geocoded,
          relevanceScore: score,
          type,
        };
        
        locations.push(location);
        console.log(`Added location:`, location);
        
        if (onUpdate) {
          onUpdate([...locations]);
        }
      } catch (error) {
        console.error(`Error processing location "${name}":`, error);
      }
    }
    
    const sortedLocations = locations.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
    console.log("Final locations:", sortedLocations);
    return sortedLocations;

  } catch (error) {
    console.error("Error processing location query:", error);
    return [];
  }
}

