/**
 * Battle Field - Main initialization and coordination script
 */

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up tab switching
    setupTabs();
    
    // Add viewport adjustments for mobile
    setupResponsiveAdjustments();
    
    // Add button visual effects
    setupButtonEffects();
    
    // Setup pan indicator behavior
    setupPanIndicator();
    
    // Prevent context menu on battlefield canvas (for right-click panning)
    document.getElementById('battlefieldCanvas').addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
    
    // Fade in the interface
    document.querySelector('.game-container').style.opacity = '1';
});

// Set up tab switching for the action panel
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.remove('active');
                content.style.opacity = '0';
            });
            
            // Deactivate all tab buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Activate the selected tab and button
            const tabContent = document.getElementById(`${tabId}-tab`);
            button.classList.add('active');
            
            // Add animation effect
            setTimeout(() => {
                tabContent.classList.add('active');
                setTimeout(() => {
                    tabContent.style.opacity = '1';
                }, 50);
            }, 150);
        });
    });
}

// Set up responsive adjustments for mobile
function setupResponsiveAdjustments() {
    // Function to adjust layouts for different screen sizes
    function adjustForScreenSize() {
        const width = window.innerWidth;
        const container = document.querySelector('.game-container');
        
        if (width <= 768) {
            // Mobile layout
            container.classList.add('mobile-layout');
            
            // Ensure battlefield is visible first on mobile
            const gameArea = document.querySelector('.game-area');
            if (gameArea) {
                // Adjust order on mobile - battlefield first, then panels
                const panels = Array.from(gameArea.children);
                panels.forEach(panel => {
                    if (panel.classList.contains('battlefield-container')) {
                        panel.style.order = '1';
                    } else if (panel.classList.contains('character-panel')) {
                        panel.style.order = '2';
                    } else if (panel.classList.contains('action-panel')) {
                        panel.style.order = '3';
                    }
                });
            }
        } else {
            // Desktop layout
            container.classList.remove('mobile-layout');
        }
    }
    
    // Run on load and on window resize
    adjustForScreenSize();
    window.addEventListener('resize', adjustForScreenSize);
}

// Add visual effects to buttons
function setupButtonEffects() {
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.action-btn, .tab-btn, .zoom-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (button.disabled) return;
            
            // Create ripple element
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            
            // Get button position
            const rect = button.getBoundingClientRect();
            
            // Calculate ripple position relative to button
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Set ripple position and size
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            // Add ripple to button
            button.appendChild(ripple);
            
            // Remove ripple after animation
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add hover effects
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            if (!button.disabled) {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
            }
        });
        
        button.addEventListener('mouseleave', function() {
            button.style.transform = '';
            button.style.boxShadow = '';
        });
    });
}

// Add CSS for button effects
(function addButtonEffectStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .ripple-effect {
            position: absolute;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            pointer-events: none;
            transform: scale(0);
            animation: ripple 0.6s linear;
            z-index: 1;
        }
        
        @keyframes ripple {
            to {
                transform: scale(2.5);
                opacity: 0;
            }
        }
        
        .game-container {
            opacity: 0;
            transition: opacity 0.5s ease;
        }
        
        .tab-content {
            transition: opacity 0.3s ease;
        }
    `;
    document.head.appendChild(style);
})();

// Set up pan indicator behavior
function setupPanIndicator() {
    const panIndicator = document.getElementById('panIndicator');
    const canvas = document.getElementById('battlefieldCanvas');
    
    if (panIndicator && canvas) {
        // Initially show the indicator
        panIndicator.style.opacity = '0.9';
        
        // Hide the indicator after a few seconds
        setTimeout(() => {
            panIndicator.style.opacity = '0';
        }, 5000);
        
        // Show the indicator when the mouse enters the canvas
        canvas.addEventListener('mouseenter', () => {
            panIndicator.style.opacity = '0.9';
            
            // Hide it again after a short delay
            setTimeout(() => {
                panIndicator.style.opacity = '0';
            }, 2000);
        });
        
        // Also show on touch start on mobile
        canvas.addEventListener('touchstart', () => {
            panIndicator.style.opacity = '0.9';
            
            // Hide it again after a short delay
            setTimeout(() => {
                panIndicator.style.opacity = '0';
            }, 2000);
        }, { passive: false });
    }
} 