export type User = {
    _id: string;
    email: string;
    name: string;
    addressLine1: string;
    city: string;
    country: string;
  };

  export type TravelResponse = {
    status: string;   
    answer: string;   
    model: string;
    chat_id?: string;
    location?: string;
    hotels?: {
      data: Array<{
        type: string;
        hotel: {
          type: string;
          hotelId: string;
          chainCode: string;
          dupeId: string;
          name: string;
          cityCode: string;
          location: {
            lat: number;
            lng: number;
          }
        };
        available: boolean;
        offers: Array<{
          id: string;
          checkInDate: string;
          checkOutDate: string;
          rateCode: string;
          room: {
            type: string;
            typeEstimated: {
              category: string;
              beds: number;
              bedType: string;
            };
            description: {
              text: string;
              lang: string;
            }
          };
          guests: {
            adults: number;
          };
          price: {
            currency: string;
            base: string;
            total: string;
            variations: {
              average: {
                base: string;
              };
              changes: Array<{
                startDate: string;
                endDate: string;
                total: string;
              }>;
            }
          };
          policies: {
            paymentType: string;
            cancellation: {
              description: {
                text: string;
              };
              type: string;
            }
          }
        }>;
      }>;
      dictionaries?: {
        chains: Record<string, string>;
        roomTypes: Record<string, string>;
      }
    };
    attractions?: Array<{
      name: string;
      address: string;
      rating: number;
      total_ratings: number;
      photo_url: string;
      location: {
        lat: number;
        lng: number;
      };
      types: string[];
    }>;
    attractions_list?: {
      attractions: Array<{
        name: string;
        address: string;
        location: {
          lat: number;
          lng: number;
        };
        rating: number;
        photo_url: string;
        total_ratings: number;
        types: string[];
      }>;
      length: number;
    };
    restaurants?: Array<{
      name: string;
      address: string;
      rating: number;
      total_ratings: number;
      photo_url: string;
      location: {
        lat: number;
        lng: number;
      };
      types: string[];
    }>;
    flights?: {
      meta: {
        count: number;
        origin: string;
        destination: string;
        departureDate: string;
        passengers: number;
        passengerType: string;
      };
      data: Array<{
        id: string;
        carrier: string;
        carrierName: string;
        departure: {
          iataCode: string;
          terminal: string;
          at: string;
        };
        arrival: {
          iataCode: string;
          terminal: string;
          at: string;
        };
        duration: string;
        price: {
          currency: string;
          total: string;
          perAdult: string;
        };
        cabinClass: string;
        baggage: {
          checkedBags: number;
          cabinBags: number;
        }
      }>;
    };
    query?: {
      location: string;
    };
  };