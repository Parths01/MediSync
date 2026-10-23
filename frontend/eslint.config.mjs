import { defineConfig, globalIgnores } from "eslint/config";
import eslint from "@eslint/js";
import typescript from "typescript-eslint";

const eslintConfig = defineConfig([
  eslint.configs.recommended,
  ...typescript.configs.recommended,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
