const App = {
    state: {
        current: 1,
        total: 0,
        currentFile: null,
        files: [],
        basePath: '',
        recentDestinations: [],
        suggestions: [],
        selectedSuggestionIndex: -1,
    },

    elements: {},

    async init() {
        this.cacheElements();
        this.bindEvents();
        this.connectWebSocket();
        await this.loadInitialData();
    },

    cacheElements() {
        this.elements = {
            fileList: document.getElementById('file-list'),
            previewName: document.getElementById('preview-name'),
            previewSize: document.getElementById('preview-size'),
            previewType: document.getElementById('preview-type'),
            previewModified: document.getElementById('preview-modified'),
            previewPath: document.getElementById('preview-path'),
            basePath: document.getElementById('base-path'),
            recentList: document.getElementById('recent-list'),
            destinationInput: document.getElementById('destination-input'),
            autocompleteDropdown: document.getElementById('autocomplete-dropdown'),
            suggestionsList: document.getElementById('suggestions-list'),
            progressFill: document.getElementById('progress-fill'),
            progressText: document.getElementById('progress-text'),
            btnMove: document.getElementById('btn-move'),
            btnSkip: document.getElementById('btn-skip'),
            btnRename: document.getElementById('btn-rename'),
            btnUndo: document.getElementById('btn-undo'),
            btnQuit: document.getElementById('btn-quit'),
            renameModal: document.getElementById('rename-modal'),
            renameInput: document.getElementById('rename-input'),
            renameCancel: document.getElementById('rename-cancel'),
            renameConfirm: document.getElementById('rename-confirm'),
            toast: document.getElementById('toast'),
            toastMessage: document.getElementById('toast-message'),
        };
    },

    bindEvents() {
        this.elements.btnMove.addEventListener('click', () => this.moveFile());
        this.elements.btnSkip.addEventListener('click', () => this.skipFile());
        this.elements.btnRename.addEventListener('click', () => this.showRenameModal());
        this.elements.btnUndo.addEventListener('click', () => this.undo());
        this.elements.btnQuit.addEventListener('click', () => this.quit());

        this.elements.renameCancel.addEventListener('click', () => this.hideRenameModal());
        this.elements.renameConfirm.addEventListener('click', () => this.confirmRename());

        this.elements.destinationInput.addEventListener('focus', () => this.showSuggestions());
        this.elements.destinationInput.addEventListener('blur', () => this.delayHideSuggestions());
        this.elements.destinationInput.addEventListener('input', () => this.handleInput());
        this.elements.destinationInput.addEventListener('keydown', (e) => this.handleInputKeydown(e));

        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
        
        this.elements.basePath.addEventListener('click', () => {
            this.elements.destinationInput.value = this.elements.basePath.textContent;
            this.elements.destinationInput.focus();
        });
    },

    connectWebSocket() {
        Socket.connect();
    },

    async loadInitialData() {
        try {
            const data = await API.fetchFiles();
            this.state.current = data.current;
            this.state.total = data.total;
            this.state.currentFile = data.current_file;
            this.state.files = data.files || [];

            this.state.basePath = await API.getBasePath();
            this.state.recentDestinations = await API.getHistory();

            this.render();
        } catch (err) {
            this.showToast('Failed to load data: ' + err.message, 'error');
        }
    },

    async loadHistory() {
        this.state.recentDestinations = await API.getHistory();
    },

    render() {
        this.renderFileList();
        this.renderPreview();
        this.renderProgress();
        this.renderBasePath();
        this.renderRecentDestinations();
    },

    renderFileList() {
        const list = this.elements.fileList;
        
        if (this.state.files.length === 0) {
            list.innerHTML = '<li class="file-item loading">No files found</li>';
            return;
        }

        list.innerHTML = this.state.files.map((file, index) => {
            const isActive = index === this.state.current - 1;
            return `<li class="file-item ${isActive ? 'active' : ''}" data-index="${index}">${file.name}</li>`;
        }).join('');
    },

    renderPreview() {
        const file = this.state.currentFile;
        
        if (!file) {
            this.elements.previewName.textContent = 'No file selected';
            this.elements.previewSize.textContent = '-';
            this.elements.previewType.textContent = '-';
            this.elements.previewModified.textContent = '-';
            this.elements.previewPath.textContent = '-';
            this.elements.previewIcon.textContent = '📄';
            return;
        }

        this.elements.previewName.textContent = file.name;
        this.elements.previewSize.textContent = this.formatSize(file.size);
        this.elements.previewType.textContent = file.file_type;
        this.elements.previewModified.textContent = new Date(file.modified).toLocaleDateString();
        this.elements.previewPath.textContent = file.path;
    },

    renderProgress() {
        const percent = this.state.total > 0 ? Math.round((this.state.current / this.state.total) * 100) : 0;
        this.elements.progressFill.style.width = `${percent}%`;
        this.elements.progressText.textContent = `${this.state.current}/${this.state.total} (${percent}%)`;
    },

    renderBasePath() {
        this.elements.basePath.textContent = this.state.basePath;
    },

    renderRecentDestinations() {
        const list = this.elements.recentList;
        const recent = this.state.recentDestinations.slice(0, 20);
        
        list.innerHTML = recent.map((dest, index) => {
            return `<li class="recent-item" data-index="${index}" data-path="${dest}">${index + 1}. ${dest}</li>`;
        }).join('');

        list.querySelectorAll('.recent-item').forEach(item => {
            item.addEventListener('click', () => {
                this.elements.destinationInput.value = item.dataset.path;
                this.elements.destinationInput.focus();
            });
        });
    },

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    },

    async showSuggestions() {
        const query = this.elements.destinationInput.value;
        await this.loadSuggestions(query);
        this.elements.autocompleteDropdown.classList.add('visible');
    },

    async loadSuggestions(query) {
        try {
            this.state.suggestions = await API.searchFolders(query);
            this.state.selectedSuggestionIndex = this.state.suggestions.length > 0 ? 0 : -1;
            this.renderSuggestions();
        } catch (err) {
            this.state.suggestions = [];
            this.state.selectedSuggestionIndex = -1;
        }
    },

    renderSuggestions() {
        const list = this.elements.suggestionsList;
        
        if (this.state.suggestions.length === 0) {
            list.innerHTML = '<li class="suggestion-item">No folders found</li>';
            return;
        }

        list.innerHTML = this.state.suggestions.map((folder, index) => {
            const isSelected = index === this.state.selectedSuggestionIndex;
            return `<li class="suggestion-item ${isSelected ? 'selected' : ''}" data-index="${index}" data-path="${folder}">📂 ${folder}</li>`;
        }).join('');

        list.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.selectSuggestion(parseInt(item.dataset.index));
            });
        });
    },

    delayHideSuggestions() {
        setTimeout(() => {
            this.elements.autocompleteDropdown.classList.remove('visible');
            this.state.selectedSuggestionIndex = -1;
        }, 200);
    },

    handleInput() {
        const value = this.elements.destinationInput.value;
        this.loadSuggestions(value);
        if (value) {
            this.elements.autocompleteDropdown.classList.add('visible');
        }
    },

    handleInputKeydown(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (this.state.suggestions.length > 0) {
                if (this.state.selectedSuggestionIndex < 0) {
                    this.state.selectedSuggestionIndex = 0;
                } else {
                    this.state.selectedSuggestionIndex = Math.min(
                        this.state.selectedSuggestionIndex + 1,
                        this.state.suggestions.length - 1
                    );
                }
            }
            this.renderSuggestions();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (this.state.selectedSuggestionIndex > 0) {
                this.state.selectedSuggestionIndex = Math.max(this.state.selectedSuggestionIndex - 1, 0);
            }
            this.renderSuggestions();
        } else if (e.key === 'Tab') {
            e.preventDefault();
            if (this.state.suggestions.length > 0) {
                if (this.state.selectedSuggestionIndex < 0) {
                    this.state.selectedSuggestionIndex = 0;
                }
                this.selectSuggestion(this.state.selectedSuggestionIndex);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            this.moveFile();
        }
    },

    selectSuggestion(index) {
        if (this.state.suggestions[index]) {
            let selectedPath = this.state.suggestions[index];
            if (!selectedPath.startsWith('/')) {
                selectedPath = this.state.basePath + '/' + selectedPath;
            }
            this.elements.destinationInput.value = selectedPath;
            this.elements.autocompleteDropdown.classList.remove('visible');
            this.elements.destinationInput.focus();
        }
    },

    handleGlobalKeydown(e) {
        if (e.target.tagName === 'INPUT') return;

        if (e.key === 'Enter') {
            this.moveFile();
        } else if (e.key === 's' || e.key === 'S') {
            this.skipFile();
        } else if (e.key === 'r' || e.key === 'R') {
            this.showRenameModal();
        } else if (e.key === 'u' || e.key === 'U') {
            this.undo();
        } else if (e.key === 'q' || e.key === 'Q') {
            this.quit();
        } else if (e.key === '0') {
            this.elements.destinationInput.value = '';
            this.elements.destinationInput.focus();
        } else if (e.key >= '1' && e.key <= '9') {
            const index = parseInt(e.key) - 1;
            const recent = this.state.recentDestinations[index];
            if (recent) {
                this.elements.destinationInput.value = recent;
                this.elements.destinationInput.focus();
            }
        }
    },

    async moveFile() {
        const destination = this.elements.destinationInput.value.trim();
        
        if (!destination && !this.state.currentFile) {
            this.showToast('No file to move', 'error');
            return;
        }

        try {
            const result = await API.moveFile(destination);
            if (result.success) {
                this.showToast('File moved successfully', 'success');
                this.elements.destinationInput.value = '';
                await this.loadHistory();
                this.renderRecentDestinations();
                await this.refreshFiles();
            } else {
                this.showToast(result.error || 'Failed to move file', 'error');
            }
        } catch (err) {
            this.showToast('Error: ' + err.message, 'error');
        }
    },

    async refreshFiles() {
        try {
            const data = await API.fetchFiles();
            this.state.current = data.current;
            this.state.total = data.total;
            this.state.currentFile = data.current_file;
            this.state.files = data.files || [];
            this.renderFileList();
            this.renderPreview();
            this.renderProgress();
            this.renderRecentDestinations();
        } catch (err) {
            console.error('Failed to refresh files:', err);
        }
    },

    async skipFile() {
        try {
            await API.skipFile();
            await this.loadHistory();
            this.renderRecentDestinations();
            await this.refreshFiles();
        } catch (err) {
            this.showToast('Error: ' + err.message, 'error');
        }
    },

    showRenameModal() {
        if (!this.state.currentFile) return;
        this.elements.renameInput.value = this.state.currentFile.name;
        this.elements.renameModal.classList.add('visible');
        this.elements.renameInput.focus();
    },

    hideRenameModal() {
        this.elements.renameModal.classList.remove('visible');
    },

    async confirmRename() {
        const newName = this.elements.renameInput.value.trim();
        
        if (!newName) {
            this.showToast('Please enter a filename', 'error');
            return;
        }

        try {
            const result = await API.renameFile(newName);
            if (result.success) {
                this.hideRenameModal();
                this.showToast('File renamed', 'success');
            } else {
                this.showToast(result.error || 'Failed to rename', 'error');
            }
        } catch (err) {
            this.showToast('Error: ' + err.message, 'error');
        }
    },

    async undo() {
        try {
            const result = await API.rollback();
            if (result.success) {
                this.showToast('Undo successful', 'success');
                await this.refreshFiles();
                await this.loadHistory();
            } else {
                this.showToast('Nothing to undo', 'error');
            }
        } catch (err) {
            this.showToast('Error: ' + err.message, 'error');
        }
    },

    quit() {
        if (confirm('Are you sure you want to quit? Progress will be saved.')) {
            window.close();
        }
    },

    handleFileUpdate(data) {
        if (data.current_file) {
            this.state.currentFile = data.current_file;
        }
        if (data.current) {
            this.state.current = data.current;
        }
        this.render();
    },

    handleProgressUpdate(data) {
        if (data.current) {
            this.state.current = data.current;
        }
        if (data.total) {
            this.state.total = data.total;
        }
        this.renderProgress();
    },

    showToast(message, type = '') {
        this.elements.toastMessage.textContent = message;
        this.elements.toast.className = 'toast visible ' + type;
        
        setTimeout(() => {
            this.elements.toast.classList.remove('visible');
        }, 3000);
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());
