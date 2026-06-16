const path = require('path');
const webpack = require('webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
    mode: 'development',
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'dist'),
    },
    resolve: {
        fallback: {
            "crypto": require.resolve("crypto-browserify"),
            "buffer": require.resolve("buffer/"),
            "stream": require.resolve("stream-browserify"),
            "vm": require.resolve("vm-browserify"),
            "path": false,
            "fs": false
        }
    },
    module: {
        rules: [
            {
                test: /\.sql$/i,
                type: 'asset/source'
            },
            {
                test: /argon2\.js$/,
                loader: 'string-replace-loader',
                options: {
                    multiple: [
                        { search: "typeof require === 'function'", replace: "false", flags: 'g' },
                        { search: "node_modules/argon2-browser/dist/argon2.wasm", replace: "argon2.wasm", flags: 'g' }
                    ]
                }
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            Buffer: ['buffer', 'Buffer'],
            process: 'process/browser',
        }),
        new webpack.DefinePlugin({
            'global.argon2WasmPath': JSON.stringify('argon2.wasm')
        }),
        new CopyWebpackPlugin({
            patterns: [
                { from: 'src/index.html', to: 'index.html' },
                { from: 'src/manifest.json', to: 'manifest.json' },
                { from: 'src/icon.svg', to: 'icon.svg' },
                { from: 'node_modules/sql.js/dist/sql-wasm.wasm', to: 'sql-wasm.wasm' },
                { from: 'node_modules/argon2-browser/dist/argon2.wasm', to: 'argon2.wasm' }
            ],
        }),
    ],
};
