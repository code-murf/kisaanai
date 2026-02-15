# AgriBharat Mobile App

## Overview
Expo React Native mobile application for the Agri-Analytics Platform. Built with TypeScript and Expo for easy cross-platform development.

## Features
- **Home Screen**: Dashboard with commodity prices, quick actions, and alerts
- **Mandi Finder**: Find nearby mandis with price comparisons and transport cost calculation
- **Voice Assistant**: Ask queries in Hindi/English using voice recognition
- **Price Charts**: View historical price trends and AI forecasts
- **Settings**: User preferences, language selection, notifications

## Tech Stack
- **React Native** with Expo SDK
- **TypeScript**
- **React Navigation** (Bottom Tabs)
- **Zustand** (State Management)
- **Expo Speech** (Text-to-Speech)
- **React Native Voice** (Speech-to-Text)
- **React Native Gifted Charts** (Visualizations)

## Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Android Studio (for Android development)
- iOS: macOS with Xcode (for iOS development)
- Expo Go app on your phone (for testing)

## Installation

```bash
cd agribharat-mobile
npm install
```

## Running on Device via USB

1. **Enable Developer Options on Android:**
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings > System > Developer Options
   - Enable "USB Debugging"

2. **Connect phone via USB**

3. **Start the dev server:**
   ```bash
   npx expo start
   ```

4. **Press 'a' for Android** (this will install the Expo Go app and run your app)

## Running on Emulator

```bash
# Android
npx expo start --android

# iOS (macOS only)
npx expo start --ios
```

## Building APK

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build APK
eas build --platform android --profile preview
```

## Project Structure

```
agribharat-mobile/
├── src/
│   ├── screens/           # Screen components
│   ├── navigation/        # Navigation configuration
│   ├── components/        # Reusable components
│   ├── services/          # API, Voice services
│   ├── store/             # Zustand state management
│   ├── types/             # TypeScript types
│   ├── constants/         # App constants
│   └── hooks/             # Custom hooks
├── assets/                # Images, fonts
├── App.tsx               # Root component
└── app.json              # Expo configuration
```

## API Configuration

The app connects to the backend API at:
- Development: `http://localhost:8000/api/v1`
- Device: `http://192.168.1.100:8000/api/v1` (update in app.json)

Update `API_URL` in `app.json` -> `extra` for your backend URL.

## Permissions

- Location (for finding nearby mandis)
- Microphone (for voice search)
- Internet (for API calls)

## Language Support

- Hindi (हिंदी)
- English
- Punjabi (ਪੰਜਾਬੀ)
- Tamil, Telugu, Marathi, Bengali, Gujarati (coming soon)

## Troubleshooting

### "Unable to resolve module"
Run: `npm install`

### Metro bundler issues
Run: `npx expo start --clear`

### USB device not detected
1. Check USB debugging is enabled
2. Try different USB cable
3. Run `adb devices` to verify connection

### Network request failed
1. Ensure your phone and computer are on the same network
2. Update API_URL in app.json to your computer's local IP
3. Check if backend is running
