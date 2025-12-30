/**
 * Blueprint Editor - JavaScript for Show Blueprint Management
 * Handles protagonist, world, characters, and concepts editing
 */

// Global state
let currentShowId = null;
let blueprintData = null;
let characterModal = null;

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

/**
 * Initialize the blueprint editor on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Get show ID from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    currentShowId = urlParams.get('show_id');
    
    if (!currentShowId) {
        showToast('Error: No show ID specified', 'danger');
        return;
    }
    
    // Initialize character modal (wait for Bootstrap to load)
    if (typeof bootstrap !== 'undefined') {
        characterModal = new bootstrap.Modal(document.getElementById('characterModal'));
    }
    
    // Load blueprint data
    loadBlueprint();
    
    // Setup form handlers
    setupFormHandlers();
});

/**
 * Load blueprint data from API
 */
async function loadBlueprint() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/shows/${currentShowId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load blueprint: ${response.statusText}`);
        }
        
        blueprintData = await response.json();
        
        // Update UI with blueprint data
        updateShowHeader(blueprintData.show);
        populateProtagonistForm(blueprintData.protagonist);
        populateWorldForm(blueprintData.world);
        populateCharactersList(blueprintData.characters);
        populateConcepts(blueprintData.concepts_history);
        
        // Show the blueprint container
        document.getElementById('blueprint-container').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading blueprint:', error);
        showToast(`Error loading blueprint: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Update show header information
 */
function updateShowHeader(show) {
    document.getElementById('show-title').textContent = show.title || 'Blueprint Editor';
    document.getElementById('show-description').textContent = show.description || '';
}

/**
 * Populate protagonist form with data
 */
function populateProtagonistForm(protagonist) {
    document.getElementById('protagonist-name').value = protagonist.name || '';
    document.getElementById('protagonist-age').value = protagonist.age || '';
    document.getElementById('protagonist-description').value = protagonist.description || protagonist.physical_description || '';
    document.getElementById('protagonist-backstory').value = protagonist.backstory || protagonist.core_motivation || '';
    
    // Populate personality traits (handle both 'values' and 'personality_traits')
    populateListItems('protagonist-traits-list', protagonist.values || protagonist.personality_traits || [], 'trait');
    
    // Populate catchphrases
    populateListItems('protagonist-catchphrases-list', protagonist.catchphrases || [], 'catchphrase');
    
    // Voice config
    const voiceConfig = protagonist.voice_config || {};
    document.getElementById('protagonist-voice-provider').value = voiceConfig.provider || '';
    document.getElementById('protagonist-voice-id').value = voiceConfig.voice_id || '';
    
    // Image preview (if exists)
    if (protagonist.image_path) {
        showImagePreview('protagonist-preview', protagonist.image_path);
    }
}

/**
 * Populate world form with data
 */
function populateWorldForm(world) {
    document.getElementById('world-name').value = world.world_name || '';
    document.getElementById('world-setting').value = world.setting || world.description || '';
    document.getElementById('world-atmosphere').value = world.atmosphere || world.era_or_style || '';
    
    // Populate world rules (handle both 'rules' and 'world_rules')
    populateListItems('world-rules-list', world.rules || world.world_rules || [], 'rule');
    
    // Populate locations (handle both 'locations' and 'key_locations')
    populateLocations(world.locations || world.key_locations || []);
}

/**
 * Populate characters list
 */
function populateCharactersList(characters) {
    const container = document.getElementById('characters-list');
    
    if (!characters || characters.length === 0) {
        container.innerHTML = '<p class="text-muted">No characters added yet.</p>';
        return;
    }
    
    container.innerHTML = characters.map((char, index) => `
        <div class="character-card">
            <div class="row">
                <div class="col-md-2">
                    ${char.image_path ? `<img src="${char.image_path}" class="img-fluid rounded" alt="${char.name}">` : '<div class="bg-secondary text-white d-flex align-items-center justify-content-center" style="height: 100px; border-radius: 8px;">No Image</div>'}
                </div>
                <div class="col-md-8">
                    <h5>${char.name}</h5>
                    <p class="text-muted mb-1"><strong>Role:</strong> ${char.role || 'N/A'}</p>
                    <p class="mb-0">${char.description || 'No description'}</p>
                </div>
                <div class="col-md-2 text-end">
                    <button class="btn btn-sm btn-outline-primary mb-2" onclick="editCharacter(${index})">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCharacter(${index})">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Populate concepts timeline
 */
function populateConcepts(conceptsHistory) {
    const timeline = document.getElementById('concepts-timeline');
    const concepts = conceptsHistory.concepts || [];
    
    if (concepts.length === 0) {
        timeline.innerHTML = '<p class="text-muted">No concepts covered yet.</p>';
        return;
    }
    
    // Sort by date (most recent first)
    const sortedConcepts = [...concepts].sort((a, b) => 
        new Date(b.date_covered) - new Date(a.date_covered)
    );
    
    timeline.innerHTML = sortedConcepts.map(concept => `
        <div class="concept-item">
            <h5>${concept.concept_name}</h5>
            <p class="text-muted mb-1">
                <small>Episode: ${concept.episode_id || 'N/A'} | 
                Date: ${new Date(concept.date_covered).toLocaleDateString()}</small>
            </p>
            <p class="mb-0">${concept.description || ''}</p>
        </div>
    `).join('');
}

/**
 * Setup form submit handlers
 */
function setupFormHandlers() {
    // Protagonist form
    document.getElementById('protagonist-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveProtagonist();
    });
    
    // World form
    document.getElementById('world-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveWorld();
    });
    
    // Concepts search
    document.getElementById('concepts-search').addEventListener('input', (e) => {
        filterConcepts(e.target.value);
    });
}

/**
 * Save protagonist data
 */
async function saveProtagonist() {
    showLoading(true);
    
    try {
        const protagonist = {
            name: document.getElementById('protagonist-name').value,
            age: parseInt(document.getElementById('protagonist-age').value),
            description: document.getElementById('protagonist-description').value,
            backstory: document.getElementById('protagonist-backstory').value,
            values: getListItems('protagonist-traits-list'),
            catchphrases: getListItems('protagonist-catchphrases-list'),
            voice_config: {
                provider: document.getElementById('protagonist-voice-provider').value || null,
                voice_id: document.getElementById('protagonist-voice-id').value || null
            }
        };
        
        const response = await fetch(`${API_BASE_URL}/api/shows/${currentShowId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ protagonist })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save protagonist: ${response.statusText}`);
        }
        
        blueprintData = await response.json();
        showToast('Protagonist saved successfully!', 'success');
        
    } catch (error) {
        console.error('Error saving protagonist:', error);
        showToast(`Error saving protagonist: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Save world data
 */
async function saveWorld() {
    showLoading(true);
    
    try {
        const world = {
            setting: document.getElementById('world-setting').value,
            atmosphere: document.getElementById('world-atmosphere').value,
            rules: getListItems('world-rules-list'),
            locations: getLocations()
        };
        
        const response = await fetch(`${API_BASE_URL}/api/shows/${currentShowId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ world })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save world: ${response.statusText}`);
        }
        
        blueprintData = await response.json();
        showToast('World saved successfully!', 'success');
        
    } catch (error) {
        console.error('Error saving world:', error);
        showToast(`Error saving world: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

/**
 * Show character modal for add/edit
 */
function showCharacterModal(index = null) {
    // Initialize modal if not already initialized
    if (!characterModal && typeof bootstrap !== 'undefined') {
        characterModal = new bootstrap.Modal(document.getElementById('characterModal'));
    }
    
    const form = document.getElementById('character-form');
    form.reset();
    document.getElementById('character-preview').innerHTML = '';
    
    if (index !== null && blueprintData.characters[index]) {
        // Edit mode
        const char = blueprintData.characters[index];
        document.getElementById('characterModalTitle').textContent = 'Edit Character';
        document.getElementById('character-index').value = index;
        document.getElementById('character-name').value = char.name || '';
        document.getElementById('character-role').value = char.role || '';
        document.getElementById('character-description').value = char.description || '';
        document.getElementById('character-personality').value = char.personality_snippet || '';
        
        const voiceConfig = char.voice_config || {};
        document.getElementById('character-voice-provider').value = voiceConfig.provider || '';
        document.getElementById('character-voice-id').value = voiceConfig.voice_id || '';
        
        if (char.image_path) {
            showImagePreview('character-preview', char.image_path);
        }
    } else {
        // Add mode
        document.getElementById('characterModalTitle').textContent = 'Add Character';
        document.getElementById('character-index').value = '';
    }
    
    if (characterModal) {
        characterModal.show();
    }
}

/**
 * Save character (add or update)
 */
async function saveCharacter() {
    const form = document.getElementById('character-form');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const index = document.getElementById('character-index').value;
    const character = {
        name: document.getElementById('character-name').value,
        role: document.getElementById('character-role').value,
        description: document.getElementById('character-description').value,
        personality_snippet: document.getElementById('character-personality').value,
        voice_config: {
            provider: document.getElementById('character-voice-provider').value || null,
            voice_id: document.getElementById('character-voice-id').value || null
        }
    };
    
    // Update local data
    if (index === '') {
        // Add new character
        blueprintData.characters.push(character);
    } else {
        // Update existing character
        blueprintData.characters[parseInt(index)] = character;
    }
    
    // Save to backend (Note: API doesn't have character endpoint yet, so we'll save the whole blueprint)
    await saveAllCharacters();
    
    // Update UI
    populateCharactersList(blueprintData.characters);
    
    // Close modal
    if (characterModal) {
        characterModal.hide();
    }
}

/**
 * Edit character
 */
function editCharacter(index) {
    showCharacterModal(index);
}

/**
 * Delete character with confirmation
 */
async function deleteCharacter(index) {
    if (!confirm('Are you sure you want to delete this character?')) {
        return;
    }
    
    blueprintData.characters.splice(index, 1);
    await saveAllCharacters();
    populateCharactersList(blueprintData.characters);
    showToast('Character deleted successfully!', 'success');
}

/**
 * Save all characters (workaround since API doesn't have character-specific endpoint)
 */
async function saveAllCharacters() {
    // For now, we'll just update the local state
    // In a real implementation, you'd need a dedicated endpoint
    showToast('Characters updated (local only - backend save not implemented)', 'warning');
}

/**
 * Add a location to the world
 */
function addLocation() {
    const container = document.getElementById('locations-container');
    const index = container.children.length;
    
    const locationHtml = `
        <div class="location-card" data-index="${index}">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h5>Location ${index + 1}</h5>
                <button type="button" class="btn btn-sm btn-remove" onclick="removeLocation(${index})">
                    Remove
                </button>
            </div>
            <div class="mb-2">
                <label class="form-label">Name</label>
                <input type="text" class="form-control location-name" placeholder="Location name">
            </div>
            <div class="mb-2">
                <label class="form-label">Description</label>
                <textarea class="form-control location-description" rows="2" 
                          placeholder="Location description"></textarea>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', locationHtml);
}

/**
 * Remove a location
 */
function removeLocation(index) {
    const container = document.getElementById('locations-container');
    const locationCard = container.querySelector(`[data-index="${index}"]`);
    if (locationCard) {
        locationCard.remove();
    }
}

/**
 * Populate locations from data
 */
function populateLocations(locations) {
    const container = document.getElementById('locations-container');
    container.innerHTML = '';
    
    locations.forEach((location, index) => {
        addLocation();
        const card = container.querySelector(`[data-index="${index}"]`);
        if (card) {
            card.querySelector('.location-name').value = location.name || '';
            card.querySelector('.location-description').value = location.description || '';
        }
    });
}

/**
 * Get all locations from form
 */
function getLocations() {
    const container = document.getElementById('locations-container');
    const locations = [];
    
    container.querySelectorAll('.location-card').forEach(card => {
        const name = card.querySelector('.location-name').value;
        const description = card.querySelector('.location-description').value;
        
        if (name || description) {
            locations.push({
                name,
                description
            });
        }
    });
    
    return locations;
}

/**
 * Add a list item (for traits, catchphrases, rules, etc.)
 */
function addListItem(containerId, placeholder) {
    const container = document.getElementById(containerId);
    const input = document.createElement('div');
    input.className = 'list-input-group';
    input.innerHTML = `
        <div class="input-group">
            <input type="text" class="form-control" placeholder="Enter ${placeholder}">
            <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.parentElement.remove()">
                Remove
            </button>
        </div>
    `;
    container.appendChild(input);
}

/**
 * Populate list items from array
 */
function populateListItems(containerId, items, placeholder) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    items.forEach(item => {
        const input = document.createElement('div');
        input.className = 'list-input-group';
        input.innerHTML = `
            <div class="input-group">
                <input type="text" class="form-control" value="${item}" placeholder="Enter ${placeholder}">
                <button class="btn btn-outline-danger" type="button" onclick="this.parentElement.parentElement.remove()">
                    Remove
                </button>
            </div>
        `;
        container.appendChild(input);
    });
}

/**
 * Get list items as array
 */
function getListItems(containerId) {
    const container = document.getElementById(containerId);
    const items = [];
    
    container.querySelectorAll('input').forEach(input => {
        const value = input.value.trim();
        if (value) {
            items.push(value);
        }
    });
    
    return items;
}

/**
 * Preview image before upload
 */
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Show existing image in preview
 */
function showImagePreview(previewId, imagePath) {
    const preview = document.getElementById(previewId);
    preview.innerHTML = `<img src="${imagePath}" alt="Current image">`;
}

/**
 * Filter concepts by search term
 */
function filterConcepts(searchTerm) {
    const timeline = document.getElementById('concepts-timeline');
    const items = timeline.querySelectorAll('.concept-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * Show loading spinner
 */
function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    const container = document.getElementById('blueprint-container');
    
    if (show) {
        spinner.style.display = 'block';
        if (container) container.style.display = 'none';
    } else {
        spinner.style.display = 'none';
        if (container) container.style.display = 'block';
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Use Bootstrap Toast if available
    if (typeof bootstrap !== 'undefined') {
        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();
        
        // Remove toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    } else {
        // Fallback: just show the toast and remove after delay
        toast.style.display = 'block';
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}
