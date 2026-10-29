export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "scope-enum": [
      1,
      "always",
      ["backend", "frontend", "docker", "e2e", "ci", "deps", "docs", "release"],
    ],
  },
};
