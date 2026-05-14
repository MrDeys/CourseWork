import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.neuropredict.app",
  appName: "NeuroPredict",
  webDir: "build",
  server: {
    androidScheme: "http",
    cleartext: true,
  },
};

export default config;
