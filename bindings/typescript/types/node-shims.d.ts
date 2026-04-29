declare module "node:path" {
  const path: {
    join: (...parts: string[]) => string;
  };

  export default path;
}

declare module "node:assert/strict" {
  const assert: {
    equal: (actual: unknown, expected: unknown, message?: string) => void;
    deepEqual: (actual: unknown, expected: unknown, message?: string) => void;
    ok: (value: unknown, message?: string) => void;
  };

  export default assert;
}

declare module "node:test" {
  type TestFunction = (
    name: string,
    fn: () => void | Promise<void>
  ) => void;

  const test: TestFunction;

  export default test;
}
