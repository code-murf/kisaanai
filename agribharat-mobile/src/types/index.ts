// API Response Types
export interface Commodity {
  id: number;
  name: string;
  category?: string;
  unit: string;
}

export interface Mandi {
  id: number;
  name: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  price?: number;
  distance?: number;
  arrival_qty?: number;
}

export interface Price {
  id: number;
  mandi_id: number;
  commodity_id: number;
  price_date: string;
  min_price?: number;
  max_price?: number;
  modal_price?: number;
  arrival_qty?: number;
}

export interface Forecast {
  date: string;
  predicted_price: number;
  lower_bound?: number;
  upper_bound?: number;
  confidence?: number;
}

export interface Alert {
  id: number;
  commodity_id: number;
  mandi_id?: number;
  target_price: number;
  condition: 'above' | 'below';
  is_active: boolean;
}

export interface User {
  id: number;
  phone_number: string;
  full_name?: string;
  preferred_language: string;
  state?: string;
  district?: string;
}

// Navigation Types
export type RootStackParamList = {
  Main: undefined;
  Login: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  Mandi: undefined;
  Voice: undefined;
  Charts: undefined;
  Settings: undefined;
};
