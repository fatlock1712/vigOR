import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.vigor.app',
  appName: 'vigOR',
  webDir: 'frontend',
  server: {
    // Keep scheme explicit for iOS webview assets.
    iosScheme: 'app',
  },
};

export default config;
