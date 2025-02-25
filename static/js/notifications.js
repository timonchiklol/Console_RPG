/**
 * Game Notification System
 * Provides popup notifications for combat and game events
 */

// Create notification container if it doesn't exist
document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    if (!document.getElementById('dice-result-container')) {
        const diceContainer = document.createElement('div');
        diceContainer.id = 'dice-result-container';
        document.body.appendChild(diceContainer);
    }
});

/**
 * Show a notification popup
 * @param {string} message - The message to display
 * @param {string} type - The type of notification ('info', 'success', 'warning', 'error')
 * @param {HTMLElement} targetElement - Optional element to position the notification near
 * @param {number} duration - How long to display the notification (milliseconds)
 */
window.showNotification = function(message, type = 'info', targetElement = null, duration = 3000) {
    const container = document.getElementById('notification-container');
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Position the notification
    if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        notification.style.position = 'absolute';
        notification.style.top = `${rect.top - 10}px`;
        notification.style.left = `${rect.left + rect.width / 2}px`;
        notification.style.transform = 'translate(-50%, -100%)';
    }
    
    // Add to container
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            container.removeChild(notification);
        }, 300); // Match the transition duration
    }, duration);
    
    // Also log to console for debugging
    console.log(`[${type.toUpperCase()}] ${message}`);
};

/**
 * Show a dice roll result popup
 * @param {number} roll - The dice roll result
 * @param {number} target - The target number needed
 * @param {boolean} success - Whether the roll was successful
 * @param {HTMLElement} targetElement - Optional element to position the popup near
 */
window.showDiceResult = function(roll, target, success, targetElement = null) {
    const container = document.getElementById('dice-result-container');
    
    // Create dice result element
    const diceResult = document.createElement('div');
    diceResult.className = `dice-result ${success ? 'success' : 'failure'}`;
    
    // Create inner content
    const rollSpan = document.createElement('span');
    rollSpan.className = 'roll-number';
    rollSpan.textContent = roll;
    
    const targetSpan = document.createElement('span');
    targetSpan.className = 'target-number';
    targetSpan.textContent = `/ ${target}`;
    
    diceResult.appendChild(rollSpan);
    diceResult.appendChild(targetSpan);
    
    // Position near target element if provided
    if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        diceResult.style.position = 'absolute';
        diceResult.style.top = `${rect.top - 30}px`;
        diceResult.style.left = `${rect.left + rect.width / 2}px`;
        diceResult.style.transform = 'translate(-50%, -100%)';
    }
    
    // Add to container
    container.appendChild(diceResult);
    
    // Animate in and out
    setTimeout(() => {
        diceResult.classList.add('show');
    }, 10);
    
    // Remove after animation
    setTimeout(() => {
        diceResult.classList.add('fade-out');
        setTimeout(() => {
            container.removeChild(diceResult);
        }, 500); // Match the transition duration
    }, 2000);
}; 