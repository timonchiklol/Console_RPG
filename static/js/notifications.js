// Notifications system
const notificationSystem = {
    container: null,
    activeNotifications: {},
    
    // Initialize the notification container
    init: function() {
        // Create container if it doesn't exist
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
    },
    
    // Show a notification
    show: function(message, type = 'info', duration = 3000) {
        this.init();
        
        // Check if we need to replace an existing notification with same type/category
        if (message.includes('Zoom:')) {
            // Remove existing zoom notifications
            this.removeByCategory('zoom');
            // Use shorter duration for zoom notifications
            duration = 1000;
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add category data attribute for identification
        if (message.includes('Zoom:')) {
            notification.dataset.category = 'zoom';
        }
        
        // Add to container
        this.container.appendChild(notification);
        
        // Trigger entrance animation
        setTimeout(() => {
            notification.classList.add('fade-in');
        }, 10);
        
        // Set up auto-removal
        const timeoutId = setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
        
        // Store reference to notification
        const id = Date.now().toString();
        this.activeNotifications[id] = {
            element: notification,
            timeoutId: timeoutId
        };
        
        return id;
    },
    
    // Remove a notification by element
    removeNotification: function(notification) {
        notification.classList.add('fade-out');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            // Clean up activeNotifications
            for (const id in this.activeNotifications) {
                if (this.activeNotifications[id].element === notification) {
                    delete this.activeNotifications[id];
                    break;
                }
            }
        }, 500);
    },
    
    // Remove notifications by category
    removeByCategory: function(category) {
        const notifications = this.container.querySelectorAll(`[data-category="${category}"]`);
        notifications.forEach(notification => {
            // Find and clear the timeout
            for (const id in this.activeNotifications) {
                if (this.activeNotifications[id].element === notification) {
                    clearTimeout(this.activeNotifications[id].timeoutId);
                    delete this.activeNotifications[id];
                    break;
                }
            }
            
            // Remove the notification immediately
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
};

// Expose to window
window.showNotification = function(message, type, duration) {
    return notificationSystem.show(message, type, duration);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    notificationSystem.init();
});
