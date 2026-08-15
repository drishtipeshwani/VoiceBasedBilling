// Must run once, before any other react-native-executorch API is used.
// Imported for its side effect at the app entry point (see index.ts).
import { initExecutorch } from 'react-native-executorch';
import { ExpoResourceFetcher } from 'react-native-executorch-expo-resource-fetcher';

initExecutorch({ resourceFetcher: ExpoResourceFetcher });
