/**
 * Data Cataloger - Main Application
 */

const API_BASE = '/api';

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Data Cataloger initializing...');

    // Initialize table list
    await TableList.init();

    // Initialize graph view (if available)
    if (typeof GraphView !== 'undefined') {
        await GraphView.init();
    }

    console.log('Data Cataloger ready');
});
