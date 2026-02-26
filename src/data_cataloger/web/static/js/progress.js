/**
 * Progress Tracker Component
 * Connects to SSE endpoint for real-time cataloging progress updates.
 */

const ProgressTracker = {
    eventSource: null,
    isActive: false,

    /**
     * Start listening for progress updates.
     */
    start() {
        if (this.eventSource) {
            this.stop();
        }

        this.eventSource = new EventSource('/api/progress');
        this.isActive = true;

        // Show progress panel
        this.showPanel();

        // Handle events
        this.eventSource.addEventListener('cataloging:started', (e) => {
            const data = JSON.parse(e.data);
            this.onStarted(data);
        });

        this.eventSource.addEventListener('table:processing', (e) => {
            const data = JSON.parse(e.data);
            this.onTableProcessing(data);
        });

        this.eventSource.addEventListener('table:completed', (e) => {
            const data = JSON.parse(e.data);
            this.onTableCompleted(data);
        });

        this.eventSource.addEventListener('table:error', (e) => {
            const data = JSON.parse(e.data);
            this.onTableError(data);
        });

        this.eventSource.addEventListener('cataloging:completed', (e) => {
            const data = JSON.parse(e.data);
            this.onCompleted(data);
        });

        this.eventSource.addEventListener('heartbeat', () => {
            // Connection is alive
        });

        this.eventSource.onerror = () => {
            console.error('SSE connection error');
            this.stop();
        };
    },

    /**
     * Stop listening for progress updates.
     */
    stop() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isActive = false;
    },

    /**
     * Show the progress panel.
     */
    showPanel() {
        const panel = document.getElementById('progress-panel');
        if (panel) panel.classList.remove('hidden');
    },

    /**
     * Hide the progress panel.
     */
    hidePanel() {
        const panel = document.getElementById('progress-panel');
        if (panel) panel.classList.add('hidden');
    },

    /**
     * Update progress bar.
     */
    updateProgress(current, total) {
        const progressBar = document.getElementById('progress-bar');
        const progressCount = document.getElementById('progress-count');

        const percent = total > 0 ? (current / total) * 100 : 0;

        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressCount) progressCount.textContent = `${current}/${total}`;
    },

    /**
     * Handle cataloging started event.
     */
    onStarted(data) {
        const progressText = document.getElementById('progress-text');
        if (progressText) progressText.textContent = 'Cataloging started...';
        this.updateProgress(0, data.total_tables);
    },

    /**
     * Handle table processing event.
     */
    onTableProcessing(data) {
        const progressText = document.getElementById('progress-text');
        if (progressText) progressText.textContent = `Processing: ${data.table_name}`;
    },

    /**
     * Handle table completed event.
     */
    onTableCompleted(data) {
        const progressText = document.getElementById('progress-text');
        if (progressText) progressText.textContent = `Completed: ${data.table_name}`;
        this.updateProgress(data.index, data.total);

        // Refresh table list
        if (typeof TableList !== 'undefined') {
            TableList.fetchTables().then(() => TableList.render());
        }
    },

    /**
     * Handle table error event.
     */
    onTableError(data) {
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `Error: ${data.table_name} - ${data.error}`;
            progressText.classList.add('text-red-600');
        }
    },

    /**
     * Handle cataloging completed event.
     */
    onCompleted(data) {
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `Completed! ${data.total_tables} tables in ${data.duration_seconds.toFixed(1)}s`;
            progressText.classList.add('text-green-600');
        }
        this.updateProgress(data.total_tables, data.total_tables);

        // Refresh views
        if (typeof TableList !== 'undefined') {
            TableList.fetchTables().then(() => TableList.render());
        }
        if (typeof GraphView !== 'undefined') {
            GraphView.loadGraph();
        }

        // Hide panel after delay
        setTimeout(() => {
            this.hidePanel();
            this.stop();
        }, 5000);
    }
};
