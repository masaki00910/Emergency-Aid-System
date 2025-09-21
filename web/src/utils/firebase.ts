import { initializeApp, getApps } from 'firebase/app'
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
}

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig)
export const db = getFirestore(app)

// Firestore Emulator connection (for local development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  const emulatorHost = process.env.NEXT_PUBLIC_FIRESTORE_EMULATOR_HOST
  if (emulatorHost && !db._delegate._databaseId.isDefaultDatabase) {
    try {
      const [host, port] = emulatorHost.split(':')
      connectFirestoreEmulator(db, host, parseInt(port))
      console.log('🔧 Connected to Firestore Emulator')
    } catch (error) {
      console.warn('Failed to connect to Firestore Emulator:', error)
    }
  }
}
