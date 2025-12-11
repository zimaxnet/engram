/// <reference types="vite/client" />

// Allow importing global styles without module declarations
declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}
