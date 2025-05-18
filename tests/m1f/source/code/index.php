<?php
/**
 * Test PHP file for m1f.py testing
 */

// Simple example PHP function
function format_greeting($name = 'Guest') {
    return "Welcome, " . htmlspecialchars($name) . "!";
}

// Example usage
$user = "Test User";
echo format_greeting($user);

// Configuration array
$config = [
    'site_name' => 'Test Site',
    'debug' => true,
    'version' => '1.0.0'
];
?>
