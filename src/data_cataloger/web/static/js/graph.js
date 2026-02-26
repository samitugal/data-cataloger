/**
 * Graph Visualization Component
 * Uses Cytoscape.js to render interactive table relationship graph.
 */

const GraphView = {
    cy: null,

    /**
     * Initialize the graph visualization.
     */
    async init() {
        const container = document.getElementById('graph-container');
        if (!container) return;

        // Initialize Cytoscape
        this.cy = cytoscape({
            container: container,
            style: this.getStyles(),
            layout: { name: 'cose', animate: false },
            minZoom: 0.3,
            maxZoom: 3,
        });

        // Setup event handlers
        this.setupEvents();

        // Load initial data
        await this.loadGraph();
    },

    /**
     * Get Cytoscape style configuration.
     */
    getStyles() {
        return [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': '#6366f1',
                    'color': '#fff',
                    'text-outline-color': '#6366f1',
                    'text-outline-width': 2,
                    'font-size': '12px',
                    'width': 80,
                    'height': 80,
                }
            },
            {
                selector: 'node[sensitivity="PII"]',
                style: {
                    'background-color': '#ef4444',
                    'text-outline-color': '#ef4444',
                }
            },
            {
                selector: 'node[sensitivity="financial"]',
                style: {
                    'background-color': '#f59e0b',
                    'text-outline-color': '#f59e0b',
                }
            },
            {
                selector: 'node[sensitivity="public"]',
                style: {
                    'background-color': '#22c55e',
                    'text-outline-color': '#22c55e',
                }
            },
            {
                selector: 'node[sensitivity="internal"]',
                style: {
                    'background-color': '#3b82f6',
                    'text-outline-color': '#3b82f6',
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#1e1b4b',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#94a3b8',
                    'target-arrow-color': '#94a3b8',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10,
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'line-color': '#6366f1',
                    'target-arrow-color': '#6366f1',
                    'width': 3,
                }
            }
        ];
    },

    /**
     * Setup event handlers.
     */
    setupEvents() {
        // Node click - show table detail
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            const tableName = node.data('id');
            TableDetail.show(tableName);
        });
    },

    /**
     * Load full graph from API.
     */
    async loadGraph() {
        try {
            const response = await fetch('/api/graph');
            if (!response.ok) throw new Error('Failed to fetch graph');
            const data = await response.json();
            this.renderGraph(data);
        } catch (error) {
            console.error('Error loading graph:', error);
        }
    },

    /**
     * Render graph data.
     */
    renderGraph(data) {
        if (!this.cy) return;

        // Clear existing elements
        this.cy.elements().remove();

        // Add nodes
        const nodes = data.nodes.map(node => ({
            data: {
                id: node.id,
                label: node.label,
                sensitivity: node.sensitivity,
            }
        }));

        // Add edges
        const edges = data.edges.map((edge, index) => ({
            data: {
                id: `edge-${index}`,
                source: edge.source,
                target: edge.target,
                label: edge.label,
            }
        }));

        this.cy.add([...nodes, ...edges]);

        // Apply layout
        this.cy.layout({
            name: 'cose',
            animate: true,
            animationDuration: 500,
            nodeRepulsion: 8000,
            idealEdgeLength: 100,
        }).run();

        // Fit to viewport
        this.cy.fit(undefined, 50);
    },

    /**
     * Focus on a specific table and its neighbors.
     */
    async focusOnTable(tableName) {
        try {
            const response = await fetch(`/api/graph/${encodeURIComponent(tableName)}/neighbors`);
            if (!response.ok) throw new Error('Failed to fetch neighbors');
            const data = await response.json();
            this.renderGraph(data);

            // Highlight the focused node
            const node = this.cy.$(`node[id="${tableName}"]`);
            if (node.length) {
                node.select();
                this.cy.center(node);
            }
        } catch (error) {
            console.error('Error focusing on table:', error);
        }
    },

    /**
     * Reset to full graph view.
     */
    async resetView() {
        await this.loadGraph();
    }
};
