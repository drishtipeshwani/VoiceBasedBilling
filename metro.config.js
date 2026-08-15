const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// react-native-executorch: allow bundling exported model/tokenizer binaries
// via require() (e.g. `require('./assets/model.pte')`).
config.resolver.assetExts.push('pte');
config.resolver.assetExts.push('bin');

module.exports = config;
