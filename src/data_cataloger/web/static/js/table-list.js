/**
 * Table List Component
 * Fetches and renders the list of cataloged tables with search functionality.
 */

const TableList = {
    tables: [],
    filteredTables: [],
    selectedTable: null,

    /**
     * Initialize the table list component.
     */
    async init() {
        await this.fetchTables();
        this.setupSearch();
        this.render();
    },

    /**
     * Fetch all tables from the API.
     */
    async fetchTables() {
        try {
            const response = await fetch('/api/tables');
            if (!response.ok) throw new Error('Failed to fetch tables');
            const data = await response.json();
            this.tables = data.tables;
            this.filteredTables = [...this.tables];
        } catch (error) {
            console.error('Error fetching tables:', error);
            this.tables = [];
            this.filteredTables = [];
        }
    },

    /**
     * Setup search input event listener.
     */
    setupSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;

        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.search(e.target.value);
            }, 300);
        });
    },

    /**
     * Search tables by keyword.
     */
    async search(query) {
        if (!query || query.length < 1) {
            this.filteredTables = [...this.tables];
            this.render();
            return;
        }

        try {
            const response = await fetch(`/api/tables/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Search failed');
            const data = await response.json();
            this.filteredTables = data.tables;
            this.render();
        } catch (error) {
            console.error('Search error:', error);
        }
    },

    /**
     * Select a table and show its details.
     */
    selectTable(tableName) {
        this.selectedTable = tableName;
        this.render();
        TableDetail.show(tableName);
    },

    /**
     * Get sensitivity badge class.
     */
    getSensitivityBadge(sensitivity) {
        const badges = {
            'PII': 'bg-red-100 text-red-800',
            'financial': 'bg-yellow-100 text-yellow-800',
            'internal': 'bg-blue-100 text-blue-800',
            'public': 'bg-green-100 text-green-800'
        };
        return badges[sensitivity] || badges['internal'];
    },

    /**
     * Render the table list.
     */
    render() {
        const container = document.getElementById('table-list');
        if (!container) return;

        if (this.filteredTables.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No tables found.</p>';
            return;
        }

        container.innerHTML = this.filteredTables.map(table => `
            <div class="table-item p-3 border rounded cursor-pointer hover:bg-indigo-50 transition-colors
                        ${this.selectedTable === table.name ? 'bg-indigo-100 border-indigo-500' : ''}
                        border-l-4 border-l-green-500"
                 onclick="TableList.selectTable('${table.name}')">
                <div class="flex justify-between items-start">
                    <span class="font-medium">${table.name}</span>
                    <span class="px-2 py-1 rounded text-xs ${this.getSensitivityBadge(table.sensitivity)}">
                        ${table.sensitivity}
                    </span>
                </div>
                <p class="text-sm text-gray-600 mt-1 line-clamp-2">${table.description}</p>
            </div>
        `).join('');
    }
};
