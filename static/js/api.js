const API = {
    baseUrl: '',

    async fetchFiles() {
        const res = await fetch(`${this.baseUrl}/api/files`);
        return res.json();
    },

    async getBasePath() {
        const res = await fetch(`${this.baseUrl}/api/base-path`);
        const data = await res.json();
        return data.base_path;
    },

    async getNearbyFolders(path) {
        const res = await fetch(`${this.baseUrl}/api/nearby-folders/${encodeURIComponent(path)}`);
        const data = await res.json();
        return data.folders || [];
    },

    async searchFolders(query) {
        const res = await fetch(`${this.baseUrl}/api/search-folders?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        return data.folders || [];
    },

    async getHistory() {
        const res = await fetch(`${this.baseUrl}/api/history`);
        const data = await res.json();
        return data.destinations || [];
    },

    async moveFile(destination) {
        const res = await fetch(`${this.baseUrl}/api/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination }),
        });
        return res.json();
    },

    async skipFile() {
        const res = await fetch(`${this.baseUrl}/api/skip`, {
            method: 'POST',
        });
        return res.json();
    },

    async renameFile(newName) {
        const res = await fetch(`${this.baseUrl}/api/rename`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName }),
        });
        return res.json();
    },

    async rollback() {
        const res = await fetch(`${this.baseUrl}/api/rollback`, {
            method: 'POST',
        });
        return res.json();
    },

    async getState() {
        const res = await fetch(`${this.baseUrl}/api/state`);
        return res.json();
    },
};

const Socket = {
    socket: null,

    connect() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.socket.emit('request_update');
        });

        this.socket.on('file_updated', (data) => {
            App.handleFileUpdate(data);
        });

        this.socket.on('progress_updated', (data) => {
            App.handleProgressUpdate(data);
        });

        this.socket.on('history_updated', () => {
            App.loadHistory();
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });
    },

    emit(event, data) {
        if (this.socket) {
            this.socket.emit(event, data);
        }
    },
};
