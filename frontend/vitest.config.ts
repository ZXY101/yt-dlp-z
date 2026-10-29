import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.ts";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["src/test/setup.ts"],
      coverage: {
        provider: "v8",
        include: ["src/**"],
        exclude: [
          "src/components/ui/**",
          "src/api/generated/**",
          "src/test/**",
          "src/main.tsx",
          "src/app/app.tsx",
          "**/*.test.{ts,tsx}",
          "**/types.ts",
        ],
        thresholds: { lines: 80, branches: 80, functions: 80, statements: 80 },
      },
    },
  }),
);
