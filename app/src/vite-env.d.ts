/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

// Declare worker modules
declare module '*?worker' {
  const workerConstructor: {
    new (): Worker
  }
  export default workerConstructor
}

declare module '*?worker&inline' {
  const workerConstructor: {
    new (): Worker
  }
  export default workerConstructor
}

declare module '*?sharedworker' {
  const workerConstructor: {
    new (): SharedWorker
  }
  export default workerConstructor
}

declare module '*?worker&url' {
  const workerUrl: string
  export default workerUrl
}