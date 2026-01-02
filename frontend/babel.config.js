export default {
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' }, modules: 'commonjs' }],
    ['@babel/preset-react', { runtime: 'automatic' }],
  ],
  plugins: [
    ['@babel/plugin-transform-modules-commonjs', { loose: true }],
    // Jest runs tests in a CommonJS context where `import.meta` is not available.
    // Vite (prod/dev) does NOT use this Babel config, so we can safely transform
    // `import.meta` for tests only.
    ({ types: t }) => ({
      name: 'transform-import-meta-to-globalThis-import-meta',
      visitor: {
        MetaProperty(path) {
          if (path.node.meta.name !== 'import' || path.node.property.name !== 'meta') return

          // Transform: import.meta -> globalThis.import.meta
          path.replaceWith(
            t.memberExpression(
              t.memberExpression(t.identifier('globalThis'), t.identifier('import')),
              t.identifier('meta')
            )
          )
        },
      },
    }),
  ],
}
