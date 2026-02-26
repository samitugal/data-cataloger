/**
 * Table Detail Component
 * Shows detailed information about a selected table.
 */

const TableDetail = {
    currentTable: null,

    /**
     * Show details for a specific table.
     */
    async show(tableName) {
        try {
            const response = await fetch(`/api/tables/${encodeURIComponent(tableName)}`);
            if (!response.ok) throw new Error('Failed to fetch table details');
            const table = await response.json();
            this.currentTable = table;
            this.render();
        } catch (error) {
            console.error('Error fetching table details:', error);
            this.showError(tableName);
        }
    },

    /**
     * Get sensitivity badge HTML.
     */
    getSensitivityBadge(sensitivity) {
        const colors = {
            'PII': 'bg-red-100 text-red-800 border-red-200',
            'financial': 'bg-yellow-100 text-yellow-800 border-yellow-200',
            'internal': 'bg-blue-100 text-blue-800 border-blue-200',
            'public': 'bg-green-100 text-green-800 border-green-200'
        };
        const colorClass = colors[sensitivity] || colors['internal'];
        return `<span class="px-3 py-1 rounded-full text-sm border ${colorClass}">${sensitivity}</span>`;
    },

    /**
     * Render the detail panel.
     */
    render() {
        const detailPanel = document.getElementById('detail-panel');
        const graphPanel = document.getElementById('graph-panel');
        const detailTitle = document.getElementById('detail-title');
        const detailContent = document.getElementById('detail-content');

        if (!detailPanel || !this.currentTable) return;

        // Show detail panel, hide graph panel
        detailPanel.classList.remove('hidden');
        if (graphPanel) graphPanel.classList.add('hidden');

        // Set title
        detailTitle.innerHTML = `
            <div class="flex items-center gap-3">
                <span>${this.currentTable.name}</span>
                ${this.getSensitivityBadge(this.currentTable.sensitivity)}
                <button onclick="TableDetail.hide()"
                        class="ml-auto text-gray-500 hover:text-gray-700">
                    ✕ Close
                </button>
            </div>
        `;

        // Set content
        detailContent.innerHTML = `
            <div class="space-y-4">
                <div>
                    <h3 class="font-semibold text-gray-700 mb-2">Description</h3>
                    <p class="text-gray-600">${this.currentTable.description}</p>
                </div>

                <div>
                    <h3 class="font-semibold text-gray-700 mb-2">Example Queries</h3>
                    <div class="space-y-2">
                        ${this.currentTable.example_queries.map(query => `
                            <pre class="bg-gray-100 p-3 rounded text-sm overflow-x-auto"><code>${this.escapeHtml(query)}</code></pre>
                        `).join('')}
                    </div>
                </div>

                <div class="pt-4 border-t">
                    <button onclick="TableDetail.showInGraph('${this.currentTable.name}')"
                            class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition-colors">
                        View in Graph
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Hide the detail panel and show graph.
     */
    hide() {
        const detailPanel = document.getElementById('detail-panel');
        const graphPanel = document.getElementById('graph-panel');

        if (detailPanel) detailPanel.classList.add('hidden');
        if (graphPanel) graphPanel.classList.remove('hidden');

        this.currentTable = null;
    },

    /**
     * Show table in graph view.
     */
    showInGraph(tableName) {
        this.hide();
        if (typeof GraphView !== 'undefined') {
            GraphView.focusOnTable(tableName);
        }
    },

    /**
     * Show error message.
     */
    showError(tableName) {
        const detailPanel = document.getElementById('detail-panel');
        const detailTitle = document.getElementById('detail-title');
        const detailContent = document.getElementById('detail-content');

        if (!detailPanel) return;

        detailPanel.classList.remove('hidden');
        detailTitle.textContent = 'Error';
        detailContent.innerHTML = `
            <p class="text-red-600">Failed to load details for table "${tableName}".</p>
            <button onclick="TableDetail.hide()"
                    class="mt-4 text-indigo-600 hover:text-indigo-800">
                Close
            </button>
        `;
    },

    /**
     * Escape HTML to prevent XSS.
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
