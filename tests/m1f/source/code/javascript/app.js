/**
 * A simple JavaScript demonstration
 */

function greet(name = 'User') {
  return `Hello, ${name}!`;
}

// Export for use in other modules
module.exports = {
  greet
};
