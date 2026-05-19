module.exports = {
  testEnvironment: 'jsdom',
  collectCoverageFrom: ['src/**/*.js', '!src/index.js'],
  coverageDirectory: 'coverage',
  moduleNameMapper: {
    '^!!raw-loader!(.*)$': '<rootDir>/test/rawLoaderMock.js',
    '^sql.js$': '<rootDir>/test/sqljsMock.js'
  },
  setupFiles: ['<rootDir>/jest.setup.js']
};
