/**
 * Example JavaScript file for testing
 */

function greet(name) {
    return `Hello, ${name}!`;
}

function calculateArea(width, height) {
    return width * height;
}

// Test the functions
console.log(greet("World"));
console.log(`Area of 5x3 rectangle: ${calculateArea(5, 3)}`);

// Export functions
module.exports = {
    greet,
    calculateArea
}; 